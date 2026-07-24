package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.AoVResponseDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncRequestDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncResponseDTO
import hu.bme.mit.ftsrg.dva.api.EvaluationResultDTO
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
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

@Serializable
private data class EvaluateBatchRequest(
    val vla: JsonObject,
    val data: JsonElement,
)

@Serializable
private data class AovIssueRequest(
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
private data class AovIssueResponse(
    val jws: String,
)

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
            val now = Clock.System.now()
            val data = (request.data as? JsonObject) ?: JsonObject(emptyMap())

            val rawVlaId = request.vlaId
            if (rawVlaId.isNullOrBlank()) {
                call.respond(
                    HttpStatusCode.BadRequest,
                    ErrDTO(type = "BAD_REQUEST", title = "vlaId is required"),
                )
                return@post
            }

            val parsedUuid = try {
                Uuid.parse(rawVlaId)
            } catch (e: IllegalArgumentException) {
                call.respond(
                    HttpStatusCode.BadRequest,
                    ErrDTO(
                        type = "BAD_REQUEST",
                        title = "invalid vlaId — expected a UUID v4, got: $rawVlaId",
                    )
                )
                return@post
            }

            val vla: JsonObject = try {
                val resp: HttpResponse = httpClient.get("$vlaManagerURL/vla/$parsedUuid") {
                    accept(ContentType.Application.Json)
                }
                if (resp.status == HttpStatusCode.NotFound) {
                    call.respond(
                        HttpStatusCode.NotFound,
                        ErrDTO(
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
                    ErrDTO(type = "BAD_GATEWAY", title = "VLA MANAGER API unreachable: ${e.message}"),
                )
                return@post
            }

            val results: List<EvaluationResultDTO> = try {
                val resp: HttpResponse = httpClient.post("$processingURL/evaluate-batch") {
                    contentType(ContentType.Application.Json)
                    setBody(EvaluateBatchRequest(vla = vla, data = data))
                }
                resp.body<List<EvaluationResultDTO>>()
            } catch (e: Exception) {
                call.respond(
                    HttpStatusCode.BadGateway,
                    ErrDTO(type = "BAD_GATEWAY", title = "DVA PROCESSING unreachable: ${e.message}"),
                )
                return@post
            }

            val allSuccess = results.isNotEmpty() && results.all { it.success }

            val recordId = UUID.randomUUID().toString()
            val vcId = Uuid.random().toString()
            var jws: String? = null

            val contractId = request.contract["id"]?.jsonPrimitive?.contentOrNull
                ?: request.contract["_id"]?.jsonPrimitive?.contentOrNull
                ?: ""
            val dataProvider = request.contract["dataProvider"]?.jsonPrimitive?.contentOrNull
                ?: request.attesterID

            if (allSuccess) {
                try {
                    val upstreamResp: HttpResponse = httpClient.post("$vcManagerURL/aov/issue") {
                        contentType(ContentType.Application.Json)
                        setBody(
                            AovIssueRequest(
                                vcId = vcId,
                                validSince = now.toString(),
                                subject = dataProvider,
                                issuerId = request.attesterID,
                                recordId = recordId,
                                contractId = contractId,
                                dataExchangeId = request.exchangeID,
                                payload = request.data.toString(),
                                evaluationResults = results,
                            )
                        )
                    }
                    if (upstreamResp.status == OK) {
                        jws = upstreamResp.body<AovIssueResponse>().jws
                    } else {
                        call.respond(
                            upstreamResp.status,
                            ErrDTO(
                                type = "VC_MANAGER_${upstreamResp.status.value}",
                                title = upstreamResp.bodyAsText(),
                            )
                        )
                        return@post
                    }
                } catch (e: Exception) {
                    call.respond(
                        HttpStatusCode.BadGateway,
                        ErrDTO(type = "BAD_GATEWAY", title = "DVA VC MANAGER unreachable: ${e.message}"),
                    )
                    return@post
                }
            }

            reqsRepo.add(
                RequestLogNew(
                    type = RequestType.ATTESTATION_REQUEST,
                    requestID = Uuid.parse(recordId),
                    exchangeID = request.exchangeID,
                    contractID = contractId,
                    vlaID = parsedUuid,
                    data = request.data,
                    attesterID = request.attesterID,
                    evaluationPassing = allSuccess,
                    evaluationResults = Json.encodeToString(results),
                    receivedDate = now,
                    evaluationDate = now,
                    vcIssuedDate = if (allSuccess) now else null,
                    vcID = if (allSuccess) vcId else null,
                )
            )

            call.respond(
                OK,
                AoVResponseDTO(
                    jws = jws,
                    evaluationPassing = allSuccess,
                    evaluationResults = results,
                )
            )
        }

        post<Attestations.Verify> {
            val request: AttestationVerifySyncRequestDTO = call.receive()
            try {
                val upstreamResp: HttpResponse = httpClient.post("$vcManagerURL/aov/verify") {
                    contentType(ContentType.Application.Json)
                    setBody(request)
                }
                if (upstreamResp.status == OK) {
                    call.respond(OK, upstreamResp.body<AttestationVerifySyncResponseDTO>())
                } else {
                    call.respond(
                        upstreamResp.status,
                        ErrDTO(
                            type = "VC_MANAGER_${upstreamResp.status.value}",
                            title = upstreamResp.bodyAsText(),
                        )
                    )
                }
            } catch (e: Exception) {
                call.respond(
                    HttpStatusCode.BadGateway,
                    ErrDTO(type = "BAD_GATEWAY", title = "DVA VC MANAGER unreachable: ${e.message}"),
                )
            }
        }
    }
}