package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.ConnectionFactory
import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.log.FakeReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.FakeVerifRequestLogRepo
import hu.bme.mit.ftsrg.dva.log.ReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestLogNew
import hu.bme.mit.ftsrg.dva.log.RequestType
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogRepo
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.http.HttpStatusCode
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.testing.ApplicationTestBuilder
import io.ktor.server.testing.testApplication
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import io.ktor.server.application.install
import java.util.UUID
import kotlin.time.Clock
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalTime::class, ExperimentalUuidApi::class)
class AttestationStatusTest {

    @Test
    fun `should return attestation status by ID`() = testApplication {
        val fakeRepo = FakeReqestLogRepo()

        val testId = Uuid.random()
        val logEntry = RequestLogNew(
            type = RequestType.ATTESTATION_REQUEST,
            requestID = testId,
            exchangeID = "xchg-status-001",
            contractID = "contract-status-001",
            vlaID = Uuid.random(),
            data = Json.parseToJsonElement("""{"actor":{"name":"Test"}}"""),
            attesterID = "attester-001",
            receivedDate = Clock.System.now(),
        )
        fakeRepo.add(logEntry)

        setupApplication(fakeRepo)
        val client = createTestClient()

        val statusResp = client.get("/attestation/$testId/status")
        assertEquals(HttpStatusCode.OK, statusResp.status)

        val statusBody = statusResp.body<JsonObject>()
        assertNotNull(statusBody["requestID"])
        assertEquals("xchg-status-001", statusBody["exchangeID"]!!.jsonPrimitive.content)
    }

    @Test
    fun `should return 404 for unknown attestation ID`() = testApplication {
        val fakeRepo = FakeReqestLogRepo()

        setupApplication(fakeRepo)
        val client = createTestClient()

        val randomId = UUID.randomUUID().toString()
        val statusResp = client.get("/attestation/$randomId/status")
        assertEquals(HttpStatusCode.NotFound, statusResp.status)
    }

    private fun ApplicationTestBuilder.setupApplication(fakeRepo: ReqestLogRepo) = setupTestApplication {
        val testModule = module {
            single<ReqestLogRepo> { fakeRepo }
            single<VerifRequestLogRepo> { FakeVerifRequestLogRepo() }
            single<HttpClient> { HttpClient { install(ContentNegotiation) { json() } } }
            single<Connection> {
                ConnectionFactory().run { newConnection() }
            }
        }
        this@setupTestApplication.install(Koin) { modules(testModule) }
        aovRoutes()
    }
}