package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.AoVResponseDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncRequestDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncResponseDTO
import hu.bme.mit.ftsrg.dva.api.EvaluationResultDTO
import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.log.FakeReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.FakeVerifRequestLogRepo
import hu.bme.mit.ftsrg.dva.log.ReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogRepo
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.mock.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.testing.*
import kotlinx.serialization.json.*
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import java.util.*

/**
 * Tests for the slimmed aovRoutes.kt that delegates VLA resolution,
 * evaluation, and VC issuance to the VLA MANAGER API, DVA PROCESSING,
 * and DVA VC MANAGER respectively.
 *
 * The mock HttpClient intercepts all three outbound calls and returns
 * canned responses — no real external services or Postgres needed.
 */
class AoVSyncRoutesTest {

    @Test
    fun `attestation returns 200 with JWS when data passes`() = testApplication {
        setupApplication(evaluationSuccess = true, issueJws = true)
        val client = createTestClient()

        val response = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }

        assertEquals(OK, response.status)
        val body = response.body<AoVResponseDTO>()
        assertTrue(body.evaluationPassing, "evaluationPassing must be true")
        assertNotNull(body.jws, "JWS must be present when data passes")
        assertNotNull(body.vcId, "vcId must be present")
        assertNotNull(body.issuerDidKey, "issuerDidKey must be present")
        assertEquals(3, body.jws!!.split(".").size, "JWS must have 3 parts")
    }

    @Test
    fun `attestation returns 200 with null JWS when data fails`() = testApplication {
        setupApplication(evaluationSuccess = false, issueJws = false)
        val client = createTestClient()

        val response = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }

        assertEquals(OK, response.status)
        val body = response.body<AoVResponseDTO>()
        assertFalse(body.evaluationPassing, "evaluationPassing must be false")
        assertNull(body.jws, "JWS must be null when data fails")
        assertNull(body.vcIssuedDate, "vcIssuedDate must be null when data fails")
    }

    @Test
    fun `attestation verify delegates to VC MANAGER and returns verified true`() = testApplication {
        setupApplication(evaluationSuccess = true, issueJws = true, verifyResult = true)
        val client = createTestClient()

        // Issue first
        val issueResp = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }
        val aovBody = issueResp.body<AoVResponseDTO>()
        assertNotNull(aovBody.jws)

        // Verify — the mock VC MANAGER returns verified=true
        val verifyResp = client.post("/attestation/verify") {
            contentType(ContentType.Application.Json)
            setBody(AttestationVerifySyncRequestDTO(
                jws = aovBody.jws!!,
                attesterDidKey = aovBody.issuerDidKey!!
            ))
        }

        assertEquals(OK, verifyResp.status)
        val verifyBody = verifyResp.body<AttestationVerifySyncResponseDTO>()
        assertTrue(verifyBody.verified, "verified must be true")
        assertNotNull(verifyBody.payload, "payload must be decoded")
    }

    @Test
    fun `attestation verify delegates to VC MANAGER and returns verified false for tampered JWS`() = testApplication {
        setupApplication(evaluationSuccess = true, issueJws = true, verifyResult = false, verifyReason = "signature mismatch")
        val client = createTestClient()

        val issueResp = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }
        val aovBody = issueResp.body<AoVResponseDTO>()

        val verifyResp = client.post("/attestation/verify") {
            contentType(ContentType.Application.Json)
            setBody(AttestationVerifySyncRequestDTO(
                jws = aovBody.jws!!,
                attesterDidKey = aovBody.issuerDidKey!!
            ))
        }

        assertEquals(OK, verifyResp.status)
        val verifyBody = verifyResp.body<AttestationVerifySyncResponseDTO>()
        assertFalse(verifyBody.verified, "verified must be false for a tampered JWS")
        assertEquals("signature mismatch", verifyBody.reason)
    }

    // --- helpers ---

    /**
     * Builds a MockEngine-based HttpClient that responds to:
     * - GET /vla/{id} → returns a VLA JSON with a schema+quality array
     * - POST /evaluate-batch → returns one EvaluationResultDTO (success depends on param)
     * - POST /aov/issue → returns a fake JWS + did:key + vcId
     * - POST /aov/verify → returns verified=true or false
     */
    private fun mockHttpClient(
        evaluationSuccess: Boolean,
        issueJws: Boolean,
        verifyResult: Boolean = true,
        verifyReason: String? = null,
    ): HttpClient = HttpClient(MockEngine) {
        install(ContentNegotiation) { json() }
        engine {
            addHandler { request ->
                val url = request.url.toString()
                when {
                    // VLA MANAGER API: GET /vla/{id}
                    url.contains("/vla/") && request.method == HttpMethod.Get -> {
                        val vla = buildJsonObject {
                            put("id", UUID.randomUUID().toString())
                            put("apiVersion", "v3.0.2")
                            put("kind", "DataContract")
                            putJsonArray("schema") {
                                addJsonObject {
                                    putJsonArray("quality") {
                                        addJsonObject {
                                            put("engine", "JQ")
                                            put("implementation", "{ success: true }")
                                        }
                                    }
                                }
                            }
                        }
                        respond(
                            content = Json.encodeToString(JsonObject.serializer(), vla),
                            status = OK,
                            headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
                        )
                    }
                    // DVA PROCESSING: POST /evaluate-batch
                    url.contains("/evaluate-batch") -> {
                        val results = listOf(
                            EvaluationResultDTO(
                                engine = "JQ",
                                timestamp = "2024-01-01T00:00:00Z",
                                success = evaluationSuccess,
                            )
                        )
                        respond(
                            content = Json.encodeToString(results),
                            status = OK,
                            headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
                        )
                    }
                    // DVA VC MANAGER: POST /aov/issue
                    url.contains("/aov/issue") -> {
                        if (issueJws) {
                            val issueResp = buildJsonObject {
                                put("jws", "eyJhbGciOiJFZERTQSIsInR5cCI6IlZDK0xELUpTT04rSldTIn0.eyJ0ZXN0IjoidGVzdCJ9.aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890abcdefghijklmnopqrstuvwxyz1234567890")
                                put("vcId", UUID.randomUUID().toString())
                                put("issuerDidKey", "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK")
                                put("vcIssuedDate", "2024-01-01T00:00:00Z")
                            }
                            respond(
                                content = Json.encodeToString(JsonObject.serializer(), issueResp),
                                status = OK,
                                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
                            )
                        } else {
                            respond(
                                content = "{}",
                                status = OK,
                                headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
                            )
                        }
                    }
                    // DVA VC MANAGER: POST /aov/verify
                    url.contains("/aov/verify") -> {
                        val verifyResp = buildJsonObject {
                            put("verified", verifyResult)
                            if (verifyReason != null) put("reason", verifyReason)
                            if (verifyResult) {
                                putJsonObject("payload") {
                                    put("@context", JsonArray(listOf(JsonPrimitive("https://www.w3.org/2018/credentials/v1"))))
                                }
                            }
                        }
                        respond(
                            content = Json.encodeToString(JsonObject.serializer(), verifyResp),
                            status = OK,
                            headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
                        )
                    }
                    else -> respond(
                        content = "{}",
                        status = HttpStatusCode.NotFound,
                    )
                }
            }
        }
    }

    private fun buildAttestationRequest(): AttestationRequestDTO = AttestationRequestDTO(
        id = null,
        exchangeID = "xchg-sync-0001",
        attesterID = "attester-sync-0001",
        contract = buildJsonObject {
            put("id", "contract-sync-0001")
            put("dataProvider", "/catalog/participants/provider-sync")
        },
        data = buildJsonObject {
            putJsonObject("result") { put("success", true) }
        },
        vlaId = UUID.randomUUID().toString(),
    )

    private fun ApplicationTestBuilder.setupApplication(
        evaluationSuccess: Boolean,
        issueJws: Boolean,
        verifyResult: Boolean = true,
        verifyReason: String? = null,
    ) = setupTestApplication {
        val testModule = module {
            single<ReqestLogRepo> { FakeReqestLogRepo() }
            single<VerifRequestLogRepo> { FakeVerifRequestLogRepo() }
            single<HttpClient> { mockHttpClient(evaluationSuccess, issueJws, verifyResult, verifyReason) }
        }
        this.install(Koin) { modules(testModule) }
        aovRoutes()
    }
}