package hu.bme.mit.ftsrg.dva.api.route

import com.rabbitmq.client.Connection
import com.rabbitmq.client.ConnectionFactory
import hu.bme.mit.ftsrg.dva.api.jws.SigningKeyStore
import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.dto.aov.AttestationRequestDTO
import hu.bme.mit.ftsrg.dva.jws.FakeWhitelistRepo
import hu.bme.mit.ftsrg.dva.jws.WhitelistRepo
import hu.bme.mit.ftsrg.dva.log.FakeReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.FakeVerifRequestLogRepo
import hu.bme.mit.ftsrg.dva.log.ReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.VerifRequestLogRepo
import io.ktor.client.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.testing.*
import kotlinx.serialization.json.*
import org.junit.jupiter.api.Assertions
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import org.testcontainers.containers.RabbitMQContainer
import org.testcontainers.junit.jupiter.Container
import org.testcontainers.junit.jupiter.Testcontainers
import java.nio.file.Files
import java.util.*

@Testcontainers
class AoVRoutesTest {

    @Container
    val rmqContainer: RabbitMQContainer = RabbitMQContainer("rabbitmq").withExposedPorts(5672)

    @Test
    fun `should create attestation request`() = testApplication {
        setupApplication()
        val client = createTestClient()

        val request = AttestationRequestDTO(
            id = "request-test-0000",
            exchangeID = "xchg-0000",
            attesterID = "attester-0000",
            contract = buildJsonObject {
                put("id", "contract-0001")
                put("dataProvider", "/catalog/participants/provider-test-id")
                put("dataConsumer", "/catalog/participants/consumer-test-did")
                put("serviceOffering", "/catalog/serviceofferings/serviceoffering-test-did")

                putJsonArray("purpose") {
                    addJsonObject {
                        put("purpose", "/catalog/serviceofferings")
                        put("piiCategory", buildJsonArray {})
                    }
                }

                putJsonArray("negotiators") {
                    addJsonObject {
                        put("did", "/catalog/participants/provider-test-id")
                    }
                    addJsonObject {
                        put("did", "/catalog/participants/consumer-test-id")
                    }
                }

                put("status", "pending")

                putJsonArray("policy") {
                    addJsonObject {
                        put("uid", "/policy/policy-0-uid")
                        putJsonArray("permission") {
                            addJsonObject {
                                put("target", "/target/3f8d1b0e-8e2e-4b69-9b1f-089fe2f3e9d7")
                                put("action", "use")
                            }
                        }
                    }
                }

                putJsonObject("vla") {
                    put("version", "1.0.0")
                    put("kind", "DataContract")
                    put("id", UUID.randomUUID().toString())
                    put("status", "active")
                    put("name", "test")
                    put("dataProduct", "test")
                    put("apiVersion", "v3.0.1")

                    putJsonArray("schema") {
                        addJsonObject {
                            put("schemaElement", "xapi_statement")
                            put("logicalType", "object")
                            putJsonArray("properties") {
                                addJsonObject {
                                    put("schemaElement", "id")
                                    put("logicalType", "string")
                                }
                                addJsonObject {
                                    put("schemaElement", "actor")
                                    put("logicalType", "object")
                                    put("required", true)
                                }
                                addJsonObject {
                                    put("schemaElement", "verb")
                                    put("logicalType", "object")
                                    put("required", true)
                                }
                                addJsonObject {
                                    put("schemaElement", "object")
                                    put("logicalType", "object")
                                    put("required", true)
                                }
                                addJsonObject {
                                    put("schemaElement", "result")
                                    put("logicalType", "object")
                                }
                                addJsonObject {
                                    put("schemaElement", "context")
                                    put("logicalType", "object")
                                }
                                addJsonObject {
                                    put("schemaElement", "timestamp")
                                    put("logicalType", "string")
                                }
                                addJsonObject {
                                    put("schemaElement", "stored")
                                    put("logicalType", "string")
                                }
                                addJsonObject {
                                    put("schemaElement", "version")
                                    put("logicalType", "string")
                                }
                            }
                            putJsonArray("quality") {
                                addJsonObject {
                                    put("dataQuality", "custom")
                                    put("engine", "greatExpectations")
                                    put(
                                        "implementation",
                                        """
                        type: ExpectColumnValuesToBeBetween
                        kwargs:
                          column: timestamp
                          min_value: '2025-01-01T00:00:00Z'
                          max_value: '2026-01-01T00:00:00Z'
                      """.trimIndent()
                                    )
                                }
                            }
                        }
                    }
                }
            },
            data = Json.parseToJsonElement(
                """
        {
          "actor": {
            "name": "Jean Dupont",
            "mbox": "mailto:jeandupont@example.com"
          },
          "verb": {
            "id": "http://adlnet.gov/expapi/verbs/interacted",
            "display": {
              "en-US": "interacted"
            }
          },
          "object": {
            "id": "https://navy.mil/netc/xapi/activities/simulations/b9e16535-4fc9-4c66-ac87-3ad7ce515f5c/events/0221144",
            "definition": {
              "name": {
                "en-US": "Event in Simulator"
              },
              "description": {
                "en-US": "You're wearing all your PPE"
              },
              "type": "http://adlnet.gov/expapi/activities/interaction"
            }
          },
          "context": {
            "registration": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "extensions": {
              "https://w3id.org/xapi/cmi5/context/extensions/sessionid": "moodle-session-12345"
            }
          },
          "result": {
              "success":true,
              "extensions": {
              "http://id.tincanapi.com/extension/severity": "info"
            }
          },
          "timestamp": "2024-03-16T30:25:00Z"
        }
      """
            )
        )
        client.post("/attestation") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.apply {
            Assertions.assertEquals(HttpStatusCode.Accepted, status)
        }
    }

    private fun ApplicationTestBuilder.setupApplication() = setupTestApplication {
        val keyDir = Files.createTempDirectory("dva-aov-keys")
        val keyPath = keyDir.resolve("test-signing-key.pem")
        val testModule = module {
            single<ReqestLogRepo> { FakeReqestLogRepo() }
            single<VerifRequestLogRepo> { FakeVerifRequestLogRepo() }
            single<HttpClient> { HttpClient { install(ContentNegotiation) { json() } } }
            single<Connection> {
                ConnectionFactory().run {
                    host = rmqContainer.host
                    port = rmqContainer.firstMappedPort
                    newConnection()
                }
            }
            single<WhitelistRepo> { FakeWhitelistRepo() }
            single { SigningKeyStore(keyPath.toString()) }
        }
        this.install(Koin) { modules(testModule) }

        aovRoutes(attestationMode = "async")
    }
}
