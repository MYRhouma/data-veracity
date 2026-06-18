package hu.bme.mit.ftsrg.dva.api.err

import hu.bme.mit.ftsrg.dva.api.auth.InvalidApiKeyException
import hu.bme.mit.ftsrg.dva.api.err.ErrType.*
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import io.github.oshai.kotlinlogging.KotlinLogging
import io.ktor.http.HttpStatusCode.Companion.InternalServerError
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.NotImplemented
import io.ktor.http.HttpStatusCode.Companion.Unauthorized
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.request.*
import io.ktor.server.response.*

private val logger = KotlinLogging.logger {}

fun StatusPagesConfig.addHandlers() {
    exception<InvalidApiKeyException>(::handleUnauthorized)
    exception<Throwable>(::handleException)
    status(NotFound) { call, _ -> handleNotFound(call) }
}

suspend fun handleUnauthorized(call: ApplicationCall, cause: InvalidApiKeyException) {
    logger.atWarn {
        message = "Authentication failed"
        payload = mapOf("path" to call.request.path())
    }
    call.respond(
        message = ErrDTO(type = "UNAUTHORIZED", title = cause.message ?: "Unauthorized", instance = call.request.path()),
        status = Unauthorized,
    )
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
        if (cause != null) detail = cause.message
    }.apply(init)