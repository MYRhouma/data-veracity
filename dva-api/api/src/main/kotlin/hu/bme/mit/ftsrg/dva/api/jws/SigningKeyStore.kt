package hu.bme.mit.ftsrg.dva.api.jws

import io.github.oshai.kotlinlogging.KLogger
import io.github.oshai.kotlinlogging.KotlinLogging
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.attribute.PosixFilePermission
import java.security.KeyFactory
import java.security.KeyPair
import java.security.interfaces.EdECPrivateKey
import java.security.interfaces.EdECPublicKey
import java.util.Base64

/**
 * Persistent Ed25519 signing-key holder for the drop-in JWS AoV issuer. The
 * keypair is loaded from the file at [path] on first call; if the file does
 * not exist, a fresh keypair is generated and persisted as
 * `base64(PKCS#8 private)|base64(X.509 public)`. Subsequent calls return the
 * cached pair.
 *
 * Security guarantees:
 * - The key file is written with POSIX permissions 0600 (owner read/write only).
 * - The parent directory is created with 0700 (owner access only).
 * - If the file exists but is malformed, the application throws a fatal error
 *   rather than silently regenerating; auto-rotation would invalidate all
 *   previously issued AoV tokens.
 *
 * @param path filesystem location where the keypair is stored as
 *   `base64(PKCS#8 private)|base64(X.509 public)`.
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
      // The file exists — attempt to parse it as base64(PKCS8)|base64(X509).
      // If it is malformed we throw a fatal error: silently regenerating would
      // invalidate every AoV token previously issued with the old key.
      val content = runCatching { String(Files.readAllBytes(file)) }.getOrElse {
        throw IllegalStateException(
          "Cannot read signing key file at $path: ${it.message}. " +
            "Remove the file manually if you intend to generate a new key."
        )
      }
      val parts = content.split("|")
      check(parts.size == 2) {
        "Signing key file at $path is malformed (expected 'base64(priv)|base64(pub)', got ${parts.size} segment(s)). " +
          "Remove the file manually if you intend to generate a new key."
      }
      val privBytes = runCatching { Base64.getDecoder().decode(parts[0]) }.getOrElse {
        throw IllegalStateException("Cannot base64-decode private key from $path: ${it.message}")
      }
      val pubBytes = runCatching { Base64.getDecoder().decode(parts[1]) }.getOrElse {
        throw IllegalStateException("Cannot base64-decode public key from $path: ${it.message}")
      }
      val kf = KeyFactory.getInstance("EdDSA")
      val priv = kf.generatePrivate(java.security.spec.PKCS8EncodedKeySpec(privBytes)) as EdECPrivateKey
      val pub = kf.generatePublic(java.security.spec.X509EncodedKeySpec(pubBytes)) as EdECPublicKey
      logger.info { "Loaded existing Ed25519 signing key from $path" }
      return KeyPair(pub, priv)
    }

    // File does not exist — generate a fresh keypair and persist it.
    val newPair = generateEd25519KeyPair()

    // Create parent directory with restricted permissions (0700) before writing.
    val parent = file.parent ?: Path.of(".")
    Files.createDirectories(parent)
    restrictDirectory(parent)

    val privB64 = Base64.getEncoder().encodeToString(newPair.private.encoded)
    val pubB64 = Base64.getEncoder().encodeToString(newPair.public.encoded)
    Files.write(file, "$privB64|$pubB64".toByteArray(Charsets.UTF_8))

    // Restrict the key file to owner read/write only (0600).
    // Wrapped in runCatching so non-POSIX filesystems (Windows) don't crash.
    runCatching {
      Files.setPosixFilePermissions(
        file,
        setOf(PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE),
      )
    }

    logger.info { "Generated new Ed25519 signing key and persisted to $path" }
    return newPair
  }

  /** Sets the directory permissions to 0700 (owner only) on POSIX systems. */
  private fun restrictDirectory(dir: Path) {
    runCatching {
      Files.setPosixFilePermissions(
        dir,
        setOf(
          PosixFilePermission.OWNER_READ,
          PosixFilePermission.OWNER_WRITE,
          PosixFilePermission.OWNER_EXECUTE,
        ),
      )
    }
  }
}