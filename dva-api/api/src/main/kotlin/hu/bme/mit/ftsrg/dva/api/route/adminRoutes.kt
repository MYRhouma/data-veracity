package hu.bme.mit.ftsrg.dva.api.route

import hu.bme.mit.ftsrg.dva.api.IssuerDidKeyDTO
import hu.bme.mit.ftsrg.dva.api.WhitelistAddRequestDTO
import hu.bme.mit.ftsrg.dva.api.WhitelistEntryDTO
import hu.bme.mit.ftsrg.dva.api.resource.Admin
import hu.bme.mit.ftsrg.dva.api.jws.SigningKeyStore
import hu.bme.mit.ftsrg.dva.jws.WhitelistRepo
import io.ktor.http.HttpStatusCode.Companion.Created
import io.ktor.http.HttpStatusCode.Companion.NoContent
import io.ktor.http.HttpStatusCode.Companion.OK
import io.ktor.http.HttpStatusCode.Companion.Unauthorized
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.resources.*
import io.ktor.server.resources.delete
import io.ktor.server.resources.get
import io.ktor.server.resources.post
import io.ktor.server.response.*
import io.ktor.server.routing.*
import org.koin.ktor.ext.inject
import java.security.MessageDigest

/**
 * Mounts the /admin routes used to manage the DVA signing key and the
 * did:key whitelist. All endpoints require a valid Bearer token.
 *
 * Security behaviour:
 * - When dva.apiKey is empty (no key configured), ALL admin endpoints return
 *   401 Unauthorized. This is a fail-closed design: an unconfigured admin key
 *   means "not set up yet", not "open to everyone".
 * - Token comparison uses [MessageDigest.isEqual] for constant-time equality
 *   so that timing differences cannot be used to brute-force the key.
 * - The Authorization header is parsed case-insensitively (both
 *   "Bearer" and "bearer" are accepted).
 */
fun Application.adminRoutes() {
  val whitelistRepo by inject<WhitelistRepo>()
  val keyStore by inject<SigningKeyStore>()
  val apiKey = environment.config.propertyOrNull("dva.apiKey")?.getString().orEmpty()

  /**
   * Returns true if the request carries a valid Bearer token.
   *
   * Fail-closed: when [apiKey] is empty (not configured) this always returns
   * false so admin endpoints are effectively disabled until a key is set.
   */
  fun ApplicationCall.checkAuth(): Boolean {
    // No key configured → admin interface is disabled entirely.
    if (apiKey.isEmpty()) return false

    val header = request.headers["Authorization"].orEmpty()

    // Strip the "Bearer " prefix case-insensitively (RFC 6750 §2.1 says the
    // scheme name is case-insensitive).
    val token = if (header.startsWith("Bearer ", ignoreCase = true)) {
      header.substring(7).trim()
    } else {
      ""
    }

    // Constant-time comparison to prevent timing-based token enumeration.
    return MessageDigest.isEqual(
      token.toByteArray(Charsets.UTF_8),
      apiKey.toByteArray(Charsets.UTF_8),
    )
  }

  routing {
    get<Admin.Keys> {
      if (!call.checkAuth()) { call.respond(Unauthorized); return@get }
      keyStore.loadOrGenerate()
      val didKey = keyStore.issuerDidKey()
      call.respond(OK, IssuerDidKeyDTO(didKey))
    }

    post<Admin.Whitelist> {
      if (!call.checkAuth()) { call.respond(Unauthorized); return@post }
      val req = call.receive<WhitelistAddRequestDTO>()
      val entry = whitelistRepo.add(req.didKey, req.label)
      call.respond(Created, WhitelistEntryDTO.from(entry))
    }

    get<Admin.Whitelist> {
      if (!call.checkAuth()) { call.respond(Unauthorized); return@get }
      call.respond(OK, whitelistRepo.all().map { WhitelistEntryDTO.from(it) })
    }

    delete<Admin.Whitelist.Entry> { req ->
      if (!call.checkAuth()) { call.respond(Unauthorized); return@delete }
      whitelistRepo.remove(req.didKey)
      call.respond(NoContent)
    }
  }
}