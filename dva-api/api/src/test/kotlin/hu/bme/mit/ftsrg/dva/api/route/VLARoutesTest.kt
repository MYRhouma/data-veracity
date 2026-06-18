package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.dto.IDDTO
import hu.bme.mit.ftsrg.dva.vla.FakeTemplateRepo
import hu.bme.mit.ftsrg.dva.vla.FakeVLARepo
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
import hu.bme.mit.ftsrg.dva.vla.VLARepo
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.NotFound
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.server.application.*
import io.ktor.server.testing.*
import kotlinx.serialization.json.*
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
class VLARoutesTest {

    @Test
    fun `should return list of VLAs`() = testApplication {
        setupApplication()

        val client = createTestClient()
        client.get("/vla").apply {
            assertEquals(OK, status)
            // Fake VLA repository seeds itself with 1 template
            assertEquals(1, body<List<JsonObject>>().size)
        }
    }

    @Test
    fun `should return VLA by ID`() = testApplication {
        setupApplication()

        val client = createTestClient()
        client.get("/vla/${Uuid.NIL}").apply {
            assertEquals(OK, status)
            assertNotNull(body<JsonObject>())
        }
    }

    @Test
    fun `should create VLA`() = testApplication {
        setupApplication()

        val client = createTestClient()
        client.post("/vla") {
            contentType(ContentType.Application.Json)
            setBody(buildJsonObject {
                put("description", "Data is recent and valid")
                putJsonObject("schema") {
                    putJsonObject("properties") {
                        putJsonObject("timestamp") {
                            put("type", "string")
                        }
                        putJsonObject("result") {
                            put("type", "integer")
                        }
                    }
                }
                putJsonArray("quality") {
                    addJsonObject {
                        put("engine", "jq")
                        put("implementation", ".timestamp >= 20250101T000000Z")
                    }
                    addJsonObject {
                        put("engine", "jq")
                        put("implementation", ".result >= 1 && .result <= 5")
                    }
                }
            })
        }.apply {
            assertEquals(Created, status)

            val id = body<IDDTO>().id
            client.get("/vla/${id}").apply {
                assertEquals(OK, status)

                val retrieved = body<JsonObject>()
                assertEquals(id, retrieved["id"]?.jsonPrimitive?.content)
            }

            client.get("/vla").apply {
                assertEquals(OK, status)
                assertEquals(2, body<List<JsonObject>>().size)
            }
        }
    }

    @Test
    fun `should create VLA from templates`() = testApplication {
        setupApplication()

        val client = createTestClient()
        client.post("/vla/from-templates") {
            contentType(ContentType.Application.Json)
            setBody(buildJsonObject {
                putJsonArray("qualityTemplates") {
                    addJsonObject {
                        put("id", Uuid.NIL.toString())
                        putJsonObject("model") {
                            put("schemaURL", "http://example.com")
                        }
                    }
                }
            })
        }.apply {
            assertEquals(Created, status)

            val id = body<IDDTO>().id
            client.get("/vla/${id}").apply {
                assertEquals(OK, status)

                val retrieved = body<JsonObject>()
                assertEquals(id, retrieved["id"]?.jsonPrimitive?.content)
                assertEquals(
                    "http://example.com",
                    retrieved["quality"]?.jsonArray[0]?.jsonObject["implementation"]?.jsonPrimitive?.content
                )
            }
            client.get("/vla").apply {
                assertEquals(OK, status)
                assertEquals(2, body<List<JsonObject>>().size)
            }
        }
    }

    @Test
    fun `should return 404 when VLA not found`() = testApplication {
        setupApplication()

        val client = createTestClient()
        val randomUUID = Uuid.random()
        client.get("/vla/$randomUUID").apply {
            assertEquals(NotFound, status)
        }
    }

    private fun ApplicationTestBuilder.setupApplication() = setupTestApplication {
        val testModule = module {
            single<VLARepo> { FakeVLARepo() }
            single<TemplateRepo> { FakeTemplateRepo() }
        }
        this.install(Koin) { modules(testModule) }

        vlaRoutes()
    }
}