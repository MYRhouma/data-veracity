package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.api.err.ErrType
import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.server.testing.*
import org.junit.jupiter.api.Test
import kotlin.test.assertEquals

class ApplicationTest {

    @Test
    fun `should respond with not found error on nonexistent path requested`() = testApplication {
        setupTestApplication()
        val client = createTestClient()
        client.get("/nonexistent").apply {
            assertEquals(HttpStatusCode.NotFound, status)
            assertEquals(ErrType.NOT_FOUND.uri.path, body<ErrDTO>().type)
        }
    }
}