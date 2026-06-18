package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Evaluation
import hu.bme.mit.ftsrg.dva.api.service.render
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import hu.bme.mit.ftsrg.dva.evaluation.Evaluate
import hu.bme.mit.ftsrg.dva.evaluation.EvaluateFromTemplate
import hu.bme.mit.ftsrg.dva.vla.Template
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
import hu.bme.mit.ftsrg.odcs.DataQuality
import io.ktor.client.HttpClient
import io.ktor.client.request.*
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.contentType
import io.ktor.server.application.Application
import io.ktor.server.request.receive
import io.ktor.server.resources.post
import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.routing
import org.koin.ktor.ext.inject
import kotlin.uuid.ExperimentalUuidApi

@OptIn(ExperimentalUuidApi::class)
fun Application.evaluationRoutes() {
    val httpClient by inject<HttpClient>()
    val templateRepo by inject<TemplateRepo>()

    val processingURL = environment.config.property("processing.url").getString()

    routing {
        post<Evaluation> {
            val request = call.receive<Evaluate>()
            val response = httpClient.post("${processingURL}/evaluate") {
                setBody(request)
                contentType(ContentType.Application.Json)
            }

            call.respondText(
                text = response.bodyAsText(),
                contentType = ContentType.Application.Json,
                status = response.status
            )
        }

        post<Evaluation.FromTemplate> {
            val evaluationReq = call.receive<EvaluateFromTemplate>()
            val template: Template = templateRepo.byID(evaluationReq.templateID) ?: run {
                call.respond(NotFound)
                return@post
            }
            val quality: DataQuality = template.render(evaluationReq.templateModel) ?: run {
                call.respond(InternalServerError, ErrDTO(type = "UNKNOWN", title = "Failed to render template"))
                return@post
            }

            val request = Evaluate(requirement = quality, data = evaluationReq.data)
            val response = httpClient.post("${processingURL}/evaluate") {
                setBody(request)
                contentType(ContentType.Application.Json)
            }

            call.respondText(
                text = response.bodyAsText(),
                contentType = ContentType.Application.Json,
                status = response.status
            )
        }
    }
}
