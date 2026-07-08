package hu.bme.mit.ftsrg.dva.api.err

import hu.bme.mit.ftsrg.dva.api.err.ErrType.*
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.NotImplemented
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.response.*

private val logger = KotlinLogging.logger {}

fun StatusPagesConfig.addHandlers() {
    exception<Throwable>(::handleException)
    status(NotFound) { call, _ -> handleNotFound(call) }
}

suspend fun handleException(call: ApplicationCall, cause: Throwable) {
    logger.atWarn {
        message = "Handling exception: $cause"
        this.cause = cause
        payload = mapOf("stacktrace" to cause.stackTraceToString())
    }

    when (cause) {
        is UnimplementedErr -> {
            call.respond(message = call.toErrorDTO(UNIMPLEMENTED, cause), status = NotImplemented)
        }

        else -> {
            call.respond(message = call.toErrorDTO(UNKNOWN, cause), status = InternalServerError)
        }
    }
}

suspend fun handleNotFound(call: ApplicationCall) {
    logger.atWarn {
        message = "Handling not found error"
        payload = mapOf("path" to call.request.path())
    }
    call.respond(message = call.toErrorDTO(NOT_FOUND), status = NotFound)
}

private fun ApplicationCall.toErrorDTO(
    type: ErrType,
    cause: Throwable? = null,
    init: ErrDTO.() -> Unit = {}
): ErrDTO =
    errDTO(type) {
        instance = request.path()
    }.apply {
        // Return a safe, generic detail string to the caller.
        // Full exception message and stack trace are already logged server-side
        // by handleException(); exposing them in the HTTP body would leak
        // library names, internal paths, and control-flow details to clients.
        if (cause != null) detail = "An internal error occurred. Check server logs for details."
    }.apply(init)