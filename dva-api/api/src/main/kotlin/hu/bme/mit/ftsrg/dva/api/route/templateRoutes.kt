package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.Templates
import hu.bme.mit.ftsrg.dva.api.service.render
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.vla.TemplateNew
import hu.bme.mit.ftsrg.dva.vla.TemplatePatch
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
import io.ktor.http.HttpStatusCode.Companion.BadRequest
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NoContent
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import io.ktor.server.resources.patch
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.JsonObject
import org.koin.ktor.ext.inject
import kotlin.uuid.ExperimentalUuidApi

@OptIn(ExperimentalUuidApi::class)
fun Application.templateRoutes() {
    val repo by inject<TemplateRepo>()

    routing {
        get<Templates> {
            call.respond(repo.all())
        }

        get<Templates.Id> { req ->
            val template = repo.byID(req.id) ?: run {
                call.respond(NotFound)
                return@get
            }
            call.respond(template)
        }

        post<Templates> {
            val templateReq = call.receive<TemplateNew>()

            val template = repo.add(templateReq) ?: run {
                call.respond(InternalServerError, ErrDTO(type = "UNKNOWN", title = "Failed to create template"))
                return@post
            }
            call.respond(Created, IDDTO(template.id.toString()))
        }

        patch<Templates.Id> { req ->
            val patch = call.receive<TemplatePatch>()
            if (req.id != patch.id) {
                call.respond(
                    status = BadRequest,
                    ErrDTO(type = "BAD_REQUEST", title = "ID path parameter does not match ID in body")
                )
            }
            val updatedTemplate = repo.update(patch) ?: run {
                call.respond(NotFound)
                return@patch
            }
            call.respond(updatedTemplate)
        }

        delete<Templates.Id> { req ->
            if (repo.remove(req.id)) {
                call.respond(NoContent)
            } else {
                call.respond(NotFound)
            }
        }

        delete<Templates> {
            repo.removeAll()
            call.respond(NoContent)
        }

        post<Templates.Id.Render> { req ->
            val template = repo.byID(req.parent.id) ?: run {
                call.respond(NotFound)
                return@post
            }
            val model = call.receive<JsonObject>()
            val renderedQuality = template.render(model) ?: run {
                call.respond(BadRequest, ErrDTO(type = "BAD_REQUEST", title = "Failed to render template"))
            }
            call.respond(renderedQuality)
        }
    }
}