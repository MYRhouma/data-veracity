package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.ConnectionFactory
import hu.bme.mit.ftsrg.dva.api.AoVResponseDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncRequestDTO
import hu.bme.mit.ftsrg.dva.api.AttestationVerifySyncResponseDTO
import hu.bme.mit.ftsrg.dva.api.EvaluationResultDTO
import hu.bme.mit.ftsrg.dva.api.jws.SigningKeyStore
import hu.bme.mit.ftsrg.dva.api.jws.didKeyToEd25519PublicKey
import hu.bme.mit.ftsrg.dva.api.jws.verifyEd25519
import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.jws.FakeWhitelistRepo
import hu.bme.mit.ftsrg.dva.jws.WhitelistRepo
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
import io.ktor.http.HttpStatusCode.Companion.Accepted
import io.ktor.http.HttpStatusCode.Companion.Forbidden
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.testing.*
import kotlinx.serialization.json.*
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import org.testcontainers.containers.RabbitMQContainer
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import java.nio.file.Files
import java.util.*

@Testcontainers
class AoVSyncRoutesTest {

    @Container
    val rmqContainer: RabbitMQContainer = RabbitMQContainer("rabbitmq").withExposedPorts(5672)

    @Test
    fun `attestation in sync mode returns 200 with JWS when data passes`() = testApplication {
        val keyStore = SigningKeyStore(tempKeyPath())
        setupApplication(syncMode = true, evaluationSuccess = true, keyStore = keyStore)
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

        keyStore.loadOrGenerate()
        val issuerDidKey = keyStore.issuerDidKey()
        val pub = didKeyToEd25519PublicKey(issuerDidKey)
        assertTrue(verifyEd25519(body.jws!!, pub), "JWS must verify with issuer's public key")
    }

    @Test
    fun `attestation in sync mode returns 200 with null JWS when data fails`() = testApplication {
        val keyStore = SigningKeyStore(tempKeyPath())
        setupApplication(syncMode = true, evaluationSuccess = false, keyStore = keyStore)
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
    fun `attestation in async mode returns 202 + IDDTO`() = testApplication {
        val keyStore = SigningKeyStore(tempKeyPath())
        setupApplication(syncMode = false, evaluationSuccess = true, keyStore = keyStore, useRmq = true)
        val client = createTestClient()

        val response = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }

        assertEquals(Accepted, response.status)
        val body = response.body<IDDTO>()
        assertNotNull(body.id)
    }

    @Test
    fun `attestation verify in sync mode accepts a valid JWS and returns verified true`() = testApplication {
        val keyStore = SigningKeyStore(tempKeyPath())
        setupApplication(syncMode = true, evaluationSuccess = true, keyStore = keyStore)
        val client = createTestClient()

        val issueResp = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }
        val aovBody = issueResp.body<AoVResponseDTO>()
        assertNotNull(aovBody.jws)

        keyStore.loadOrGenerate()
        val issuerDidKey = keyStore.issuerDidKey()

        val verifyResp = client.post("/attestation/verify") {
            contentType(ContentType.Application.Json)
            setBody(AttestationVerifySyncRequestDTO(jws = aovBody.jws!!, attesterDidKey = issuerDidKey))
        }

        assertEquals(OK, verifyResp.status)
        val verifyBody = verifyResp.body<AttestationVerifySyncResponseDTO>()
        assertTrue(verifyBody.verified, "verified must be true for a valid JWS")
        assertNotNull(verifyBody.payload, "payload must be decoded")
    }

    @Test
    fun `attestation verify in sync mode rejects a tampered JWS`() = testApplication {
        val keyStore = SigningKeyStore(tempKeyPath())
        setupApplication(syncMode = true, evaluationSuccess = true, keyStore = keyStore)
        val client = createTestClient()

        val issueResp = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }
        val aovBody = issueResp.body<AoVResponseDTO>()
        assertNotNull(aovBody.jws)

        keyStore.loadOrGenerate()
        val issuerDidKey = keyStore.issuerDidKey()

        val tamperedJws = tamperJws(aovBody.jws!!)

        val verifyResp = client.post("/attestation/verify") {
            contentType(ContentType.Application.Json)
            setBody(AttestationVerifySyncRequestDTO(jws = tamperedJws, attesterDidKey = issuerDidKey))
        }

        assertEquals(OK, verifyResp.status)
        val verifyBody = verifyResp.body<AttestationVerifySyncResponseDTO>()
        assertFalse(verifyBody.verified, "verified must be false for a tampered JWS")
        assertEquals("signature mismatch", verifyBody.reason)
    }

    @Test
    fun `attestation verify in sync mode respects the did-key whitelist`() = testApplication {
        val keyStore = SigningKeyStore(tempKeyPath())
        val whitelist = FakeWhitelistRepo()
        whitelist.add("did:key:z6MkwhitelistEntryOnly", "trusted-issuer")
        setupApplication(syncMode = true, evaluationSuccess = true, keyStore = keyStore, whitelist = whitelist)
        val client = createTestClient()

        val issueResp = client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(buildAttestationRequest())
        }
        val aovBody = issueResp.body<AoVResponseDTO>()
        assertNotNull(aovBody.jws)

        keyStore.loadOrGenerate()
        val issuerDidKey = keyStore.issuerDidKey()
        assertNotEquals("did:key:z6MkwhitelistEntryOnly", issuerDidKey, "sanity: issuer is NOT the whitelisted key")

        val verifyResp = client.post("/attestation/verify") {
            contentType(ContentType.Application.Json)
            setBody(AttestationVerifySyncRequestDTO(jws = aovBody.jws!!, attesterDidKey = issuerDidKey))
        }

        assertEquals(Forbidden, verifyResp.status)
        val verifyBody = verifyResp.body<AttestationVerifySyncResponseDTO>()
        assertFalse(verifyBody.verified)
        assertEquals("attester not whitelisted", verifyBody.reason)
    }

    // --- helpers ---

    private fun tempKeyPath(): String {
        val dir = Files.createTempDirectory("dva-sync-test-keys")
        return dir.resolve("test-signing-key.pem").toString()
    }

    private fun mockHttpClient(success: Boolean): HttpClient = HttpClient(MockEngine) {
        install(ContentNegotiation) { json() }
        engine {
            addHandler { _ ->
                respond(
                    content = Json.encodeToString(
                        EvaluationResultDTO(
                            engine = "JQ",
                            timestamp = "2024-01-01T00:00:00Z",
                            success = success,
                        )
                    ),
                    status = OK,
                    headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString())
                )
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
            put("dataConsumer", "/catalog/participants/consumer-sync")
            put("serviceOffering", "/catalog/serviceofferings/so-sync")
            put("status", "pending")
            putJsonObject("vla") {
                put("version", "1.0.0")
                put("kind", "DataContract")
                put("id", UUID.randomUUID().toString())
                put("status", "active")
                put("name", "sync-test")
                put("dataProduct", "sync-test")
                put("apiVersion", "v3.0.1")
                putJsonArray("schema") {
                    addJsonObject {
                        put("schemaElement", "result")
                        put("logicalType", "object")
                        putJsonArray("quality") {
                            addJsonObject {
                                put("dataQuality", "custom")
                                put("engine", "jq")
                                put("implementation", ".result.success == true")
                            }
                        }
                    }
                }
            }
        },
        data = buildJsonObject {
            putJsonObject("result") {
                put("success", true)
            }
        }
    )

    private fun tamperJws(jws: String): String {
        val parts = jws.split(".")
        require(parts.size == 3) { "JWS must have 3 parts" }
        val sig = parts[2]
        val flipped = (if (sig.first() == 'A') 'B' else 'A') + sig.substring(1)
        return "${parts[0]}.${parts[1]}.$flipped"
    }

    private fun ApplicationTestBuilder.setupApplication(
        syncMode: Boolean,
        evaluationSuccess: Boolean,
        keyStore: SigningKeyStore,
        whitelist: WhitelistRepo = FakeWhitelistRepo(),
        useRmq: Boolean = false,
    ) = setupTestApplication {
        val testModule = module {
            single<ReqestLogRepo> { FakeReqestLogRepo() }
            single<VerifRequestLogRepo> { FakeVerifRequestLogRepo() }
            single<WhitelistRepo> { whitelist }
            single { keyStore }
            single<HttpClient> { mockHttpClient(evaluationSuccess) }
            if (useRmq) {
                single<Connection> {
                    ConnectionFactory().run {
                        host = rmqContainer.host
                        port = rmqContainer.firstMappedPort
                        newConnection()
                    }
                }
            } else {
                single<Connection> {
                    ConnectionFactory().run {
                        host = "localhost"
                        newConnection()
                    }
                }
            }
        }
        this.install(Koin) { modules(testModule) }
        aovRoutes(attestationMode = if (syncMode) "sync" else "async")
    }
}
