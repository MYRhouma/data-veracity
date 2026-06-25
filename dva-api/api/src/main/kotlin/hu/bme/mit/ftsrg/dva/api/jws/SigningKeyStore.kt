package hu.bme.mit.ftsrg.dva.api.jws

import io.github.oshai.kotlinlogging.KLogger
import io.github.oshai.kotlinlogging.KotlinLogging
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.security.KeyFactory
import java.security.KeyPair
import java.security.interfaces.EdECPrivateKey
import java.security.interfaces.EdECPublicKey
import java.util.Base64

/**
 * Persistent Ed25519 signing-key holder for the drop-in JWS AoV issuer. The
 * private key is loaded from the file at [path] on first call; if the file
 * is missing or malformed, a fresh keypair is generated and the private key
 * is persisted. Subsequent calls return the cached pair.
 *
 * @param path filesystem location where the 32 raw private-key bytes are
 *   stored, base64-encoded.
 */
public class SigningKeyStore(private val path: String) {

  private val logger: KLogger = KotlinLogging.logger {}
  private val mutex = Mutex()
  private var cached: KeyPair? = null

  /**
   * Loads (or generates, then persists) the Ed25519 keypair. Thread-safe via
   * an internal mutex; the cached pair is reused on subsequent calls.
   */
  public suspend fun loadOrGenerate(): KeyPair {
    cached?.let { return it }
    return mutex.withLock {
      cached?.let { return it }
      val pair = readOrGenerate()
      cached = pair
      pair
    }
  }

  /**
   * Returns the `did:key` identifier of the persisted public key, derivable
   * from the cached keypair. Throws if [loadOrGenerate] has not been called.
   */
  public fun issuerDidKey(): String {
    val pair = cached ?: error("SigningKeyStore.loadOrGenerate() must be called before issuerDidKey()")
    val pub = pair.public as EdECPublicKey
    return ed25519PublicKeyToDidKey(pub)
  }

  private fun readOrGenerate(): KeyPair {
    val file = Paths.get(path)
    if (Files.exists(file)) {
      val parts = runCatching {
        String(Files.readAllBytes(file)).split("|")
      }.getOrNull()
      if (parts != null && parts.size == 2) {
        val privBytes = runCatching { Base64.getDecoder().decode(parts[0]) }.getOrNull()
        val pubBytes = runCatching { Base64.getDecoder().decode(parts[1]) }.getOrNull()
        if (privBytes != null && pubBytes != null) {
          val kf = KeyFactory.getInstance("EdDSA")
          val priv = kf.generatePrivate(java.security.spec.PKCS8EncodedKeySpec(privBytes)) as EdECPrivateKey
          val pub = kf.generatePublic(java.security.spec.X509EncodedKeySpec(pubBytes)) as EdECPublicKey
          logger.info { "Loaded existing Ed25519 signing key from $path" }
          return KeyPair(pub, priv)
        }
      }
      logger.warn { "Existing signing key at $path was malformed; regenerating" }
    }
    val newPair = generateEd25519KeyPair()
    Files.createDirectories(file.parent ?: Path.of("."))

    val privB64 = Base64.getEncoder().encodeToString(newPair.private.encoded)
    val pubB64 = Base64.getEncoder().encodeToString(newPair.public.encoded)
    Files.write(file, "$privB64|$pubB64".toByteArray(Charsets.UTF_8))
    logger.info { "Generated new Ed25519 signing key and persisted to $path" }
    return newPair
  }
}