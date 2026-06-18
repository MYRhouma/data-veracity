package hu.bme.mit.ftsrg.dva.api.testutil

import hu.bme.mit.ftsrg.dva.api.auth.ApiKeyAuth
import hu.bme.mit.ftsrg.dva.api.err.addHandlers
import io.ktor.client.*
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.request.header
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.plugins.calllogging.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.resources.*
import io.ktor.server.testing.*
import kotlinx.serialization.json.Json
import org.slf4j.event.Level
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation as ClientContentNegotiation
import io.ktor.server.application.install as serverInstall
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation as ServerContentNegotiation

const val TEST_API_KEY = "test-api-key-12345"

fun ApplicationTestBuilder.setupTestApplication(block: Application.() -> Unit = {}) = application {
    setupApplicationBase()
    block()
}

fun ApplicationTestBuilder.createTestClient(block: HttpClientConfig<*>.() -> Unit = {}): HttpClient = createClient {
    install(ClientContentNegotiation) { json() }
    defaultRequest { header("X-API-Key", TEST_API_KEY) }
    block()
}

private fun Application.setupApplicationBase() {
    serverInstall(CallLogging) { level = Level.DEBUG }
    serverInstall(ApiKeyAuth) {
        apiKey = TEST_API_KEY
    }
    serverInstall(StatusPages) { addHandlers() }
    serverInstall(ServerContentNegotiation) { json(Json { explicitNulls = true }) }
    serverInstall(Resources)
}