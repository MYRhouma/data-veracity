package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.resource.VLAs
import hu.bme.mit.ftsrg.dva.api.service.render
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
import hu.bme.mit.ftsrg.dva.vla.VLANew
import hu.bme.mit.ftsrg.dva.vla.VLANewFromTemplates
import hu.bme.mit.ftsrg.dva.vla.VLARepo
import hu.bme.mit.ftsrg.odcs.DataQuality
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.server.application.Application
import io.ktor.server.request.*
import io.ktor.server.resources.*
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.routing
import kotlinx.serialization.json.*
import org.koin.ktor.ext.inject
import kotlin.uuid.ExperimentalUuidApi

@OptIn(ExperimentalUuidApi::class)
fun Application.vlaRoutes() {
    val templateRepo by inject<TemplateRepo>()
    val vlaRepo by inject<VLARepo>()

    routing {
        get<VLAs> {
            call.respond(vlaRepo.all())
        }

        get<VLAs.Id> { req ->
            val vla = vlaRepo.byID(req.id) ?: run {
                call.respond(NotFound)
                return@get
            }
            call.respond(vla)
        }

        post<VLAs> {
            val vlaReq = call.receive<VLANew>()
            val vla = buildJsonObject {
                put("apiVersion", "v3.0.2")
                put("kind", "DataContract")
                put("version", "0.1.0")
                put("status", "active")

                vlaReq.apply {
                    description?.let { put("description", it) }
                    servers?.let { put("servers", it) }
                    schema?.let { put("schema", it) }
                    quality?.let { put("quality", Json.encodeToJsonElement(it)) }
                    price?.let { put("price", it) }
                    team?.let { put("team", it) }
                    roles?.let { put("roles", it) }
                    slaProperties?.let { put("slaProperties", it) }
                    support?.let { put("support", it) }
                    tags?.let { put("tags", it) }
                }
            }
            val id = vlaRepo.add(vla) ?: run {
                call.respond(InternalServerError, ErrDTO(type = "UNKNOWN", title = "Failed to create VLA"))
                return@post
            }

            call.respond(Created, IDDTO(id.toString()))
        }

        post<VLAs.FromTemplates> {
            val vlaReq = call.receive<VLANewFromTemplates>()
            val originalVLA = buildJsonObject {
                put("apiVersion", "v3.0.2")
                put("kind", "DataContract")
                put("version", "0.1.0")
                put("status", "active")

                vlaReq.apply {
                    description?.let { put("description", it) }
                    servers?.let { put("servers", it) }
                    schema?.let { put("schema", it) }
                    quality?.let { put("quality", Json.encodeToJsonElement(it)) }
                    price?.let { put("price", it) }
                    team?.let { put("team", it) }
                    roles?.let { put("roles", it) }
                    slaProperties?.let { put("slaProperties", it) }
                    support?.let { put("support", it) }
                    tags?.let { put("tags", it) }
                }
            }

            // Extend VLA with rendered templates
            val qualityRequirements = mutableListOf<DataQuality>()
            vlaReq.qualityTemplates?.forEach { templateInstantiation ->
                val template = templateRepo.byID(templateInstantiation.id) ?: run {
                    // TODO: respond with more detail?
                    call.respond(NotFound)
                    return@post
                }
                val quality = template.render(templateInstantiation.model) ?: run {
                    call.respond(InternalServerError, ErrDTO(type = "UNKNOWN", title = "Failed to render template"))
                    return@post
                }
                qualityRequirements.add(quality)
            }
            val extendedVLA = buildJsonObject {
                originalVLA.forEach { k, v -> put(k, v) }
                putJsonArray("quality") {
                    originalVLA["quality"]?.jsonArray?.forEach { add(it) }
                    qualityRequirements.forEach { add(Json.encodeToJsonElement(it)) }
                }
            }

            val id = vlaRepo.add(extendedVLA) ?: run {
                call.respond(InternalServerError, ErrDTO(type = "UNKNOWN", title = "Failed to create VLA"))
                return@post
            }

            call.respond(Created, IDDTO(id.toString()))
        }

        delete<VLAs> {
            vlaRepo.removeAll()
        }
    }
}