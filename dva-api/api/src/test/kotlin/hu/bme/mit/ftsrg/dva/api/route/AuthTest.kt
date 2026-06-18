package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import io.ktor.client.request.get
import io.ktor.client.statement.bodyAsText
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.request.header
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.Application
import io.ktor.server.routing.routing
import io.ktor.server.testing.testApplication
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class AuthTest {

    @Test
    fun `should reject request without API key`() = testApplication {
        setupTestApplication {
            routing { }
        }
        val client = createClient { }
        client.get("/attestation").apply {
            assertEquals(HttpStatusCode.Unauthorized, status)
            assertTrue(bodyAsText().contains("Invalid or missing API key"))
        }
    }

    @Test
    fun `should reject request with wrong API key`() = testApplication {
        setupTestApplication {
            routing { }
        }
        val client = createClient {
            defaultRequest { header("X-API-Key", "wrong-key") }
        }
        client.get("/attestation").apply {
            assertEquals(HttpStatusCode.Unauthorized, status)
        }
    }

    @Test
    fun `should allow swagger path without API key`() = testApplication {
        setupTestApplication {
            routing { }
        }
        val client = createClient { }
        client.get("/swagger").apply {
            assertTrue(status != HttpStatusCode.Unauthorized)
        }
    }
}