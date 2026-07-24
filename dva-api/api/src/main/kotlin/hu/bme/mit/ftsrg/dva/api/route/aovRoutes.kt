package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.MessageProperties
import hu.bme.mit.ftsrg.dva.api.resource.Attestations
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.dto.aov.ACAPyPresentationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.ACAPyPresentationResponseDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationVerificationRequestDTO
import hu.bme.mit.ftsrg.dva.log.*
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
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.koin.ktor.ext.inject
import java.util.*
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
fun Application.aovRoutes() {
    val rmqConnection by inject<Connection>()
    val reqsRepo by inject<ReqestLogRepo>()
    val verifsRepo by inject<VerifRequestLogRepo>()
    val httpClient by inject<HttpClient>()

    routing {
        post<Attestations> {
            val request: AttestationRequestDTO = call.receive()

            val id = UUID.randomUUID().toString()
            val requestWithID: AttestationRequestDTO = request.copy(id = id)

            reqsRepo.add(
                RequestLogNew(
                    type = RequestType.ATTESTATION_REQUEST,
                    requestID = Uuid.parse(requestWithID.id!!),
                    exchangeID = requestWithID.exchangeID,
                    contractID = requestWithID.contract["id"].toString(),
                    vlaID = Uuid.parse(requestWithID.contract["vla"]?.jsonObject["id"]?.jsonPrimitive?.content!!),
                    data = requestWithID.data,
                    attesterID = requestWithID.attesterID,
                    receivedDate = Clock.System.now(),
                )
            )

            rmqConnection.confirmChannel {
                declareQueue(QueueSpecification("ATTESTATION_REQUESTS"))
                publish {
                    publishWithConfirm(createMessage(Json.encodeToString(requestWithID)))
                }
            }

            call.respond(status = Accepted, message = IDDTO(id))
        }

        post<Attestations.Verify> {
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
                        environment.config.property("acaPy.controller.url").getString()
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
            if (!resp.status.isSuccess()) {
                call.respond(
                    resp.status,
                    ErrDTO(type = "ACAPY_${resp.status.value}", title = resp.bodyAsText()),
                )
            } else {
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
        }
    }
}

private fun createMessage(body: String): OutboundMessage =
    OutboundMessage(
        exchange = "",
        routingKey = "ATTESTATION_REQUESTS",
        properties = MessageProperties.PERSISTENT_BASIC,
        msg = body
    )