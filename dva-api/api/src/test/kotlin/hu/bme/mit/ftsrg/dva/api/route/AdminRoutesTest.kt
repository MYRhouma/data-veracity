package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.jws.SigningKeyStore
import hu.bme.mit.ftsrg.dva.api.testutil.createTestClient
import hu.bme.mit.ftsrg.dva.api.testutil.setupTestApplication
import hu.bme.mit.ftsrg.dva.api.IssuerDidKeyDTO
import hu.bme.mit.ftsrg.dva.api.WhitelistEntryDTO
import hu.bme.mit.ftsrg.dva.api.WhitelistAddRequestDTO
import hu.bme.mit.ftsrg.dva.jws.FakeWhitelistRepo
import hu.bme.mit.ftsrg.dva.jws.WhitelistRepo
import io.ktor.client.call.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.http.ContentType.*
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.NoContent
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.server.application.install
import io.ktor.server.testing.*
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.koin.dsl.module
import org.koin.ktor.plugin.Koin
import java.nio.file.Files

class AdminRoutesTest {

  @Test
  fun `gets the instance issuer did-key`() = testApplication {
    setupApplication()
    val client = createTestClient()
    client.get("/admin/keys").apply {
      assertEquals(OK, status)
      val dto = body<IssuerDidKeyDTO>()
      assertTrue(dto.issuerDidKey.startsWith("did:key:z6Mk"), "issuer did:key starts with z6Mk")
    }
  }

  @Test
  fun `adds and lists a whitelist entry`() = testApplication {
    setupApplication()
    val client = createTestClient()
    client.post("/admin/whitelist") {
      contentType(Application.Json)
      setBody(WhitelistAddRequestDTO(didKey = "did:key:z6Mktest1", label = "provider"))
    }.apply {
      assertEquals(Created, status)
      val entry = body<WhitelistEntryDTO>()
      assertEquals("did:key:z6Mktest1", entry.didKey)
      assertEquals("provider", entry.label)
    }
    client.get("/admin/whitelist").apply {
      assertEquals(OK, status)
      val list = body<List<WhitelistEntryDTO>>()
      assertEquals(1, list.size)
      assertEquals("did:key:z6Mktest1", list[0].didKey)
      assertEquals("provider", list[0].label)
    }
  }

  @Test
  fun `supports optional label`() = testApplication {
    setupApplication()
    val client = createTestClient()
    client.post("/admin/whitelist") {
      contentType(Application.Json)
      setBody(WhitelistAddRequestDTO(didKey = "did:key:z6Mktest2", label = null))
    }.apply { assertEquals(Created, status) }
    client.get("/admin/whitelist").apply {
      assertEquals(OK, status)
      val list = body<List<WhitelistEntryDTO>>()
      val match = list.firstOrNull { it.didKey == "did:key:z6Mktest2" }
      assertTrue(match != null, "added entry must be visible")
      assertNull(match!!.label, "label must be null when not provided")
    }
  }

  @Test
  fun `deletes a whitelist entry`() = testApplication {
    setupApplication()
    val client = createTestClient()
    client.post("/admin/whitelist") {
      contentType(Application.Json)
      setBody(WhitelistAddRequestDTO(didKey = "did:key:z6Mktest3", label = "temp"))
    }.apply { assertEquals(Created, status) }
    client.delete("/admin/whitelist/did:key:z6Mktest3").apply {
      assertEquals(NoContent, status)
    }
    client.get("/admin/whitelist").apply {
      assertEquals(OK, status)
      val list = body<List<WhitelistEntryDTO>>()
      assertTrue(list.none { it.didKey == "did:key:z6Mktest3" }, "entry must be gone")
    }
  }

  private fun ApplicationTestBuilder.setupApplication() = setupTestApplication {
    val keyDir = Files.createTempDirectory("dva-keys")
    val keyPath = keyDir.resolve("test-signing-key.pem")
    val testModule = module {
      single<WhitelistRepo> { FakeWhitelistRepo() }
      single { SigningKeyStore(keyPath.toString()) }
    }
    this.install(Koin) { modules(testModule) }
    adminRoutes()
  }
}