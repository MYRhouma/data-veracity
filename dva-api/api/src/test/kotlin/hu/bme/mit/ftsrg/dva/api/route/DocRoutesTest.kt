package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.server.testing.*
import org.junit.jupiter.api.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class DocRoutesTest {

    @Test
    fun `should return HTML page when root route is requested`() = testApplication {
        setupApplication()
        client.get("/").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertTrue {
                headers["Content-Type"]?.contains(ContentType.Text.Html.toString()) ?: false
            }
        }
    }

    @Test
    fun `should return swagger documentation page when slash swagger is requested`() = testApplication {
        setupApplication()
        client.get("/swagger").apply {
            assertEquals(HttpStatusCode.OK, status)
            assertTrue {
                headers["Content-Type"]?.contains(ContentType.Text.Html.toString()) ?: false
            }
        }
    }

    private fun ApplicationTestBuilder.setupApplication() =
        setupTestApplication { docRoutes(openapiPath = "../../docs/spec/openapi.yaml") }
}