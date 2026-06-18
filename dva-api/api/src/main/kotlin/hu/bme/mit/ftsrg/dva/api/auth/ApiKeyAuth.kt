package hu.bme.mit.ftsrg.dva.api.auth

import io.ktor.http.HttpStatusCode
import io.ktor.server.application.createApplicationPlugin
import io.ktor.server.request.header
import io.ktor.server.request.path
import io.ktor.server.response.respond

class InvalidApiKeyException : RuntimeException("Invalid or missing API key")

val ApiKeyAuth = createApplicationPlugin("ApiKeyAuth", ::ApiKeyAuthConfig) {
    val validKey = pluginConfig.apiKey

    onCall { call ->
        val requestPath = call.request.path()
        if (requestPath.startsWith("/swagger") || requestPath == "/openapi.yaml") {
            return@onCall
        }

        val providedKey = call.request.header("X-API-Key")
        if (providedKey == null || providedKey != validKey) {
            throw InvalidApiKeyException()
        }
    }
}

class ApiKeyAuthConfig {
    var apiKey: String = "changeme"
}