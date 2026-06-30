package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.dva.api.AoVResponseDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncRequestDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncResponseDTO
import hu.bme.mit.ftsrg.dva.api.EvaluationResultDTO
import hu.bme.mit.ftsrg.dva.api.jws.AovClaims
import hu.bme.mit.ftsrg.dva.api.jws.Ed25519PrivateKey
import hu.bme.mit.ftsrg.dva.api.jws.SigningKeyStore
import hu.bme.mit.ftsrg.dva.api.jws.didKeyToEd25519PublicKey
import hu.bme.mit.ftsrg.dva.api.jws.signEd25519
import hu.bme.mit.ftsrg.dva.api.jws.verifyEd25519
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.ACAPyPresentationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.ACAPyPresentationResponseDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationVerificationRequestDTO
import hu.bme.mit.ftsrg.dva.evaluation.Evaluate
import hu.bme.mit.ftsrg.dva.jws.WhitelistRepo
import hu.bme.mit.ftsrg.dva.vla.VLARepo
import hu.bme.mit.ftsrg.dva.log.*
import hu.bme.mit.ftsrg.odcs.DataQuality
import io.github.viartemev.rabbitmq.channel.confirmChannel
import io.github.viartemev.rabbitmq.channel.publish
import io.github.viartemev.rabbitmq.publisher.OutboundMessage
import io.github.viartemev.rabbitmq.queue.QueueSpecification
import io.github.viartemev.rabbitmq.queue.declareQueue
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.Accepted
import io.ktor.http.HttpStatusCode.Companion.Forbidden
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.koin.ktor.ext.inject
import java.util.*
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
fun Application.aovRoutes(
    attestationMode: String =
        environment.config.propertyOrNull("dva.attestation.mode")?.getString() ?: "sync",
) {
    val rmqConnection by inject<Connection>()
    val reqsRepo by inject<ReqestLogRepo>()
    val verifsRepo by inject<VerifRequestLogRepo>()
    val httpClient by inject<HttpClient>()
    val keyStore by inject<SigningKeyStore>()
    val whitelistRepo by inject<WhitelistRepo>()
    val vlaRepo by inject<VLARepo>()

    val processingURL =
        environment.config.propertyOrNull("processing.url")?.getString() ?: "http://localhost:5000"

    routing {
        post<Attestations> {
            val request: AttestationRequestDTO = call.receive()

            val id = UUID.randomUUID().toString()
            val requestWithID: AttestationRequestDTO = request.copy(id = id)

            if (attestationMode == "async") {
                handleAsyncAttestation(requestWithID, id, rmqConnection, reqsRepo)
                call.respond(status = Accepted, message = IDDTO(id))
                return@post
            }

            // --- SYNC MODE ---
            val now = Clock.System.now()
            val data = (requestWithID.data as? JsonObject) ?: JsonObject(emptyMap())

            // 1. Evaluate each requirement in contract.vla.schema[*].quality[*]
            val results = mutableListOf<EvaluationResultDTO>()

            // Look up VLA: prefer vlaId from the request (real PDC flow),
            // fall back to contract["vla"] (Karate test compatibility)
            val rawVlaId = requestWithID.vlaId
            val vla: JsonObject? = if (!rawVlaId.isNullOrBlank()) {
                try {
                    vlaRepo.byID(Uuid.parse(rawVlaId))
                } catch (e: Exception) {
                    null
                }
            } else {
                requestWithID.contract["vla"]?.jsonObject
            }

            val schema: JsonArray? = vla?.get("schema")?.jsonArray
            if (schema != null) {
                for (schemaItem in schema) {
                    val quality = schemaItem.jsonObject["quality"]?.jsonArray ?: continue
                    for (requirement in quality) {
                        val reqObj = requirement.jsonObject
                        val engine = reqObj["engine"]?.jsonPrimitive?.contentOrNull
                        val implementation = reqObj["implementation"]?.jsonPrimitive?.contentOrNull
                        if (engine == null || implementation == null) continue

                        val evaluateRequest = Evaluate(
                            requirement = DataQuality(engine = engine, implementation = implementation),
                            data = data,
                        )
                        val resp: HttpResponse = httpClient.post("$processingURL/evaluate") {
                            contentType(ContentType.Application.Json)
                            setBody(evaluateRequest)
                        }
                        val result: EvaluationResultDTO = resp.body()
                        results.add(result)
                    }
                }
            }

            val allSuccess = results.isNotEmpty() && results.all { it.success }

            // 2. Sign JWS if all evaluations pass
            val vcId = Uuid.random().toString()
            var issuerDidKey: String? = null
            var jws: String? = null

            // Helpers: read contract.id (Karate test shape) with _id fallback
            // (PDC BilateralResponseType / ContractResponseType use _id), and
            // dataProvider (BilateralResponseType) with no PDC equivalent on
            // ContractResponseType (falls back to attesterID, which is correct).
            val contractId = requestWithID.contract["id"]?.jsonPrimitive?.contentOrNull
                ?: requestWithID.contract["_id"]?.jsonPrimitive?.contentOrNull
                ?: ""
            val dataProvider = requestWithID.contract["dataProvider"]?.jsonPrimitive?.contentOrNull
                ?: requestWithID.attesterID

            if (allSuccess) {
                keyStore.loadOrGenerate()
                issuerDidKey = keyStore.issuerDidKey()
                val pair = keyStore.loadOrGenerate()
                val claims = AovClaims(
                    vcId = vcId,
                    validSince = now.toString(),
                    subject = dataProvider,
                    issuerId = requestWithID.attesterID,
                    recordId = requestWithID.id!!,
                    contractId = contractId,
                    dataExchangeId = requestWithID.exchangeID,
                    payload = requestWithID.data.toString(),
                )
                jws = signEd25519(claims, pair.private as Ed25519PrivateKey, issuerDidKey)
            }

            // 3. Persist RequestLog with all fields
            val vlaIdForLog = requestWithID.vlaId
                ?: vla?.get("id")?.jsonPrimitive?.contentOrNull
            reqsRepo.add(
                RequestLogNew(
                    type = RequestType.ATTESTATION_REQUEST,
                    requestID = Uuid.parse(requestWithID.id!!),
                    exchangeID = requestWithID.exchangeID,
                    contractID = contractId,
                    vlaID = vlaIdForLog?.let { Uuid.parse(it) } ?: Uuid.parse("00000000-0000-0000-0000-000000000000"),
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

            // 4. Build and return response
            call.respond(
                OK,
                AoVResponseDTO(
                    requestId = id,
                    issuerDidKey = issuerDidKey,
                    jws = jws,
                    vcId = if (allSuccess) vcId else null,
                    evaluationPassing = allSuccess,
                    evaluationResults = results,
                    vcIssuedDate = if (allSuccess) now.toString() else null,
                )
            )
        }

        post<Attestations.Verify> {
            if (attestationMode == "async") {
                handleAsyncVerify(call, httpClient, verifsRepo)
                return@post
            }

            // --- SYNC MODE ---
            val request: AttestationVerifySyncRequestDTO = call.receive()

            // Whitelist check: if whitelist is non-empty, attester must be listed
            val whitelist = whitelistRepo.all()
            if (whitelist.isNotEmpty() && !whitelistRepo.contains(request.attesterDidKey)) {
                call.respond(
                    Forbidden,
                    AttestationVerifySyncResponseDTO(
                        verified = false,
                        reason = "attester not whitelisted",
                        payload = null,
                    )
                )
                return@post
            }

            // Look up the public key from the did:key
            val publicKey = try {
                didKeyToEd25519PublicKey(request.attesterDidKey)
            } catch (e: Exception) {
                call.respond(
                    OK,
                    AttestationVerifySyncResponseDTO(
                        verified = false,
                        reason = "invalid attester did:key: ${e.message}",
                        payload = null,
                    )
                )
                return@post
            }

            // Verify the JWS signature
            val verified = try {
                verifyEd25519(request.jws, publicKey)
            } catch (e: Exception) {
                false
            }

            if (!verified) {
                call.respond(
                    OK,
                    AttestationVerifySyncResponseDTO(
                        verified = false,
                        reason = "signature mismatch",
                        payload = null,
                    )
                )
                return@post
            }

            // Decode the JWS payload (middle segment, base64url)
            val payload: JsonObject? = try {
                val parts = request.jws.split(".")
                val payloadBytes = java.util.Base64.getUrlDecoder().decode(parts[1])
                Json.decodeFromString(JsonObject.serializer(), String(payloadBytes, Charsets.UTF_8))
            } catch (e: Exception) {
                null
            }

            call.respond(
                OK,
                AttestationVerifySyncResponseDTO(
                    verified = true,
                    reason = null,
                    payload = payload,
                )
            )
        }
    }
}

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
private suspend fun handleAsyncAttestation(
    requestWithID: AttestationRequestDTO,
    id: String,
    rmqConnection: Connection,
    reqsRepo: ReqestLogRepo,
) {
    reqsRepo.add(
        RequestLogNew(
            type = RequestType.ATTESTATION_REQUEST,
            requestID = Uuid.parse(requestWithID.id!!),
            exchangeID = requestWithID.exchangeID,
            contractID = requestWithID.contract["id"].toString(),
            vlaID = Uuid.parse(
                requestWithID.contract["vla"]?.jsonObject?.get("id")?.jsonPrimitive?.content!!
            ),
            data = requestWithID.data,
            attesterID = requestWithID.attesterID,
            receivedDate = Clock.System.now(),
        )
    )

    rmqConnection.confirmChannel {
        declareQueue(QueueSpecification("ATTESTATION_REQUESTS", durable = true))
        publish {
            publishWithConfirm(createMessage(Json.encodeToString(requestWithID)))
        }
    }
}

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
private suspend fun handleAsyncVerify(
    call: ApplicationCall,
    httpClient: HttpClient,
    verifsRepo: VerifRequestLogRepo,
) {
    val request: AttestationVerificationRequestDTO = call.receive()

    val id = UUID.randomUUID().toString()
    val requestWithID: AttestationVerificationRequestDTO = request.copy(id = id)

    val verifLogEntity = verifsRepo.add(
        VerifRequestLogNew(
            exchangeID = requestWithID.exchangeID,
            contractID = requestWithID.contractID,
            attesterAgentURL = requestWithID.attesterAgentURL,
            attesterAgentLabel = requestWithID.attesterAgentLabel,
            receivedDate = Clock.System.now(),
        )
    )

    val resp: HttpResponse =
        httpClient.post(
            "${
                call.application.environment.config.property("acaPy.controller.url").getString()
            }/request_presentation_from_peer"
        ) {
            contentType(ContentType.Application.Json)
            setBody(
                ACAPyPresentationRequestDTO(
                    dataExchangeId = requestWithID.exchangeID,
                    attesterAgentURL = requestWithID.attesterAgentURL,
                    attesterLabel = requestWithID.attesterAgentLabel
                )
            )
        }
    val acaPyResp: ACAPyPresentationResponseDTO = resp.body()

    if (verifLogEntity != null) {
        verifsRepo.update(
            VerifRequestLogPatch(
                id = verifLogEntity.id,
                presentationRequestData = acaPyResp.aov,
            )
        )
    }

    call.respond(status = resp.status, message = acaPyResp)
}

private fun createMessage(body: String): OutboundMessage =
    OutboundMessage(
        exchange = "",
        routingKey = "ATTESTATION_REQUESTS",
        properties = MessageProperties.PERSISTENT_BASIC,
        msg = body
    )
