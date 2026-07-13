package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.AoVResponseDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncRequestDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncResponseDTO
import hu.bme.mit.ftsrg.dva.api.EvaluationResultDTO
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.log.*
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*
import org.koin.ktor.ext.inject
import java.util.*
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

// --- DTOs for the new inter-service calls ---

@Serializable
data class EvaluateBatchRequest(
    val vla: JsonObject,
    val data: JsonElement,
)

@Serializable
data class AovIssueRequest(
    val vcId: String,
    val validSince: String,
    val subject: String,
    val issuerId: String,
    val recordId: String,
    val contractId: String,
    val dataExchangeId: String,
    val payload: String,
    val evaluationResults: List<EvaluationResultDTO>,
)

@Serializable
data class AovIssueResponse(
    val jws: String,
    val vcId: String,
    val issuerDidKey: String,
    val vcIssuedDate: String,
)

/**
 * Slim orchestrator for the synchronous attestation flow.
 *
 * Initiation: PDC POSTs /attestation with data + vlaId.
 * VLA Resolution: DVA API GETs /vla/{id} from the VLA MANAGER API at
 *                 the Data Intermediary.
 * Veracity Checks: DVA API POSTs /evaluate-batch to DVA PROCESSING with
 *                   the full VLA + data; gets back an array of
 *                   (requirement, result) pairs.
 * Credential Issuance: DVA API POSTs /aov/issue to DVA VC MANAGER with
 *                       the claims + evaluation results; gets back the
 *                       JWS.
 * Synchronous Return: DVA API returns the AoV JWS synchronously to the
 *                      PDC.
 *
 * The verify endpoint delegates body-and-all to the DVA VC MANAGER's
 * /aov/verify — the whitelist and JWS verification live there.
 */
@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
fun Application.aovRoutes() {
    val reqsRepo by inject<ReqestLogRepo>()
    val httpClient by inject<HttpClient>()

    val processingURL =
        environment.config.propertyOrNull("processing.url")?.getString() ?: "http://localhost:5000"
    val vlaManagerURL =
        environment.config.propertyOrNull("vlaManager.url")?.getString() ?: "http://localhost:8000"
    val vcManagerURL =
        environment.config.propertyOrNull("vcManager.url")?.getString() ?: "http://localhost:8000"

    routing {
        post<Attestations> {
            val request: AttestationRequestDTO = call.receive()
            val id = UUID.randomUUID().toString()
            val requestWithID: AttestationRequestDTO = request.copy(id = id)
            val now = Clock.System.now()
            val data = (requestWithID.data as? JsonObject) ?: JsonObject(emptyMap())

            // --- VLA Resolution via VLA MANAGER API ---
            val rawVlaId = requestWithID.vlaId
            val vla: JsonObject = if (!rawVlaId.isNullOrBlank()) {
                val parsedUuid = try {
                    Uuid.parse(rawVlaId)
                } catch (e: IllegalArgumentException) {
                    call.respond(
                        HttpStatusCode.BadRequest,
                        hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                            type = "BAD_REQUEST",
                            title = "invalid vlaId — expected a UUID v4, got: $rawVlaId",
                        )
                    )
                    return@post
                }
                try {
                    val resp: HttpResponse = httpClient.get("$vlaManagerURL/vla/${parsedUuid}") {
                        accept(ContentType.Application.Json)
                    }
                    if (resp.status == HttpStatusCode.NotFound) {
                        call.respond(
                            HttpStatusCode.NotFound,
                            hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                                type = "NOT_FOUND",
                                title = "VLA $parsedUuid not found at the Data Intermediary",
                            )
                        )
                        return@post
                    }
                    resp.body<JsonObject>()
                } catch (e: Exception) {
                    call.respond(
                        HttpStatusCode.BadGateway,
                        hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                            type = "BAD_GATEWAY",
                            title = "VLA MANAGER API unreachable: ${e.message}",
                        )
                    )
                    return@post
                }
            } else {
                requestWithID.contract["vla"]?.jsonObject ?: JsonObject(emptyMap())
            }

            // --- Veracity Checks via DVA PROCESSING /evaluate-batch ---
            val results: List<EvaluationResultDTO> = try {
                val resp: HttpResponse = httpClient.post("$processingURL/evaluate-batch") {
                    contentType(ContentType.Application.Json)
                    setBody(EvaluateBatchRequest(vla = vla, data = data))
                }
                resp.body<List<EvaluationResultDTO>>()
            } catch (e: Exception) {
                call.respond(
                    HttpStatusCode.BadGateway,
                    hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                        type = "BAD_GATEWAY",
                        title = "DVA PROCESSING unreachable: ${e.message}",
                    )
                )
                return@post
            }

            val allSuccess = results.isNotEmpty() && results.all { it.success }

            // --- Credential Issuance via DVA VC MANAGER /aov/issue ---
            val vcId = Uuid.random().toString()
            var issuerDidKey: String? = null
            var jws: String? = null
            var vcIssuedDate: String? = null

            val contractId = requestWithID.contract["id"]?.jsonPrimitive?.contentOrNull
                ?: requestWithID.contract["_id"]?.jsonPrimitive?.contentOrNull
                ?: ""
            val dataProvider = requestWithID.contract["dataProvider"]?.jsonPrimitive?.contentOrNull
                ?: requestWithID.attesterID

            if (allSuccess) {
                try {
                    val upstreamResp: HttpResponse = httpClient.post("$vcManagerURL/aov/issue") {
                        contentType(ContentType.Application.Json)
                        setBody(AovIssueRequest(
                            vcId = vcId,
                            validSince = now.toString(),
                            subject = dataProvider,
                            issuerId = requestWithID.attesterID,
                            recordId = requestWithID.id!!,
                            contractId = contractId,
                            dataExchangeId = requestWithID.exchangeID,
                            payload = requestWithID.data.toString(),
                            evaluationResults = results,
                        ))
                    }
                    if (upstreamResp.status == OK) {
                        val issueResp: AovIssueResponse = upstreamResp.body()
                        jws = issueResp.jws
                        issuerDidKey = issueResp.issuerDidKey
                        vcIssuedDate = issueResp.vcIssuedDate
                    } else {
                        // Upstream rejected — relay the real status, not 502.
                        call.respond(
                            upstreamResp.status,
                            hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                                type = "VC_MANAGER_${upstreamResp.status.value}",
                                title = upstreamResp.bodyAsText(),
                            )
                        )
                        return@post
                    }
                } catch (e: Exception) {
                    call.respond(
                        HttpStatusCode.BadGateway,
                        hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                            type = "BAD_GATEWAY",
                            title = "DVA VC MANAGER unreachable: ${e.message}",
                        )
                    )
                    return@post
                }
            }

            // --- Audit: persist RequestLog (dva-api owns the audit trail) ---
            val vlaIdForLog = requestWithID.vlaId
                ?: vla?.get("id")?.jsonPrimitive?.contentOrNull
            reqsRepo.add(
                RequestLogNew(
                    type = RequestType.ATTESTATION_REQUEST,
                    requestID = Uuid.parse(requestWithID.id!!),
                    exchangeID = requestWithID.exchangeID,
                    contractID = contractId,
                    vlaID = vlaIdForLog?.let {
                        try { Uuid.parse(it) } catch (_: IllegalArgumentException) { null }
                    },
                    data = requestWithID.data,
                    attesterID = requestWithID.attesterID,
                    evaluationPassing = allSuccess,
                    evaluationResults = Json.encodeToString(results),
                    receivedDate = now,
                    evaluationDate = now,
                    vcIssuedDate = if (allSuccess) now else null,
                    vcID = if (allSuccess) vcId else null,
                )
            )

            // --- Synchronous return to PDC ---
            call.respond(
                OK,
                AoVResponseDTO(
                    requestId = id,
                    issuerDidKey = issuerDidKey,
                    jws = jws,
                    vcId = if (allSuccess) vcId else null,
                    evaluationPassing = allSuccess,
                    evaluationResults = results,
                    vcIssuedDate = vcIssuedDate,
                )
            )
        }

        // --- Verify: delegate to DVA VC MANAGER /aov/verify ---
        post<Attestations.Verify> {
            val request: AttestationVerifySyncRequestDTO = call.receive()
            try {
                val upstreamResp: HttpResponse = httpClient.post("$vcManagerURL/aov/verify") {
                    contentType(ContentType.Application.Json)
                    setBody(request)
                }
                // Relay the upstream status directly: a 400 from the VC
                // Manager (e.g., malformed JWS) is NOT the same as the
                // VC Manager being unreachable. Without this fix the gateway
                // conflates "upstream rejected my request" with "upstream
                // is down" and the PDC sees a misleading 502.
                if (upstreamResp.status == OK) {
                    call.respond(OK, upstreamResp.body<AttestationVerifySyncResponseDTO>())
                } else {
                    // Non-2xx upstream — relay the same status with the
                    // upstream text as the title so the PDC sees the real
                    // reason ("malformed JWS: ...", "attester not
                    // whitelisted", etc.) rather than a generic 502.
                    call.respond(
                        upstreamResp.status,
                        hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                            type = "VC_MANAGER_${upstreamResp.status.value}",
                            title = upstreamResp.bodyAsText(),
                        )
                    )
                }
            } catch (e: Exception) {
                // Genuinely unreachable (connection refused, timeout,
                // hostname resolution failure) — fall back to 502.
                call.respond(
                    HttpStatusCode.BadGateway,
                    hu.bme.mit.ftsrg.dva.dto.ErrDTO(
                        type = "BAD_GATEWAY",
                        title = "DVA VC MANAGER unreachable: ${e.message}",
                    )
                )
            }
        }
    }
}