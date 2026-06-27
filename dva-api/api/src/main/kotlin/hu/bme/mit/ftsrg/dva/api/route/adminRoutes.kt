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

/**
 * Mounts the /admin routes used to manage the DVA signing key and the
 * did:key whitelist. Endpoints are guarded by a minimal Bearer auth: when
 * the application config exposes a non-empty dva.apiKey, callers must
 * present Authorization: Bearer key. When the configured key is empty
 * (default), auth is disabled and any caller is accepted.
 */
fun Application.adminRoutes() {
  val whitelistRepo by inject<WhitelistRepo>()
  val keyStore by inject<SigningKeyStore>()
  val apiKey = environment.config.propertyOrNull("dva.apiKey")?.getString().orEmpty()

  fun ApplicationCall.checkAuth(): Boolean {
    if (apiKey.isEmpty()) return true
    val header = request.headers["Authorization"].orEmpty()
    val token = header.removePrefix("Bearer ").trim()
    return token == apiKey
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