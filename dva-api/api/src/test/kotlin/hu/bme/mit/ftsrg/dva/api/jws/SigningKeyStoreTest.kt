package hu.bme.mit.ftsrg.dva.api.jws

import kotlinx.coroutines.runBlocking
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Path

class SigningKeyStoreTest {

  @Test
  fun `generates key on first run when file missing`(@TempDir tempDir: Path) = runBlocking {
    val keyPath = tempDir.resolve("dva-signing-key.pem").toString()
    val store = SigningKeyStore(keyPath)
    val pair = store.loadOrGenerate()

    val keyFile = Path.of(keyPath).toFile()
    assertTrue(keyFile.exists(), "key file must be created after loadOrGenerate")
    assertTrue(keyFile.length() > 0, "key file must not be empty")

    val didKey = store.issuerDidKey()
    val pair2 = store.loadOrGenerate()
    assertEquals(pair, pair2, "loadOrGenerate must cache the pair")
    assertEquals(didKey, store.issuerDidKey())
  }

  @Test
  fun `persists and reloads the same key across instances`(@TempDir tempDir: Path) = runBlocking {
    val keyPath = tempDir.resolve("dva-signing-key.pem").toString()
    val store1 = SigningKeyStore(keyPath)
    store1.loadOrGenerate()
    val didKey1 = store1.issuerDidKey()

    val store2 = SigningKeyStore(keyPath)
    store2.loadOrGenerate()
    val didKey2 = store2.issuerDidKey()

    assertEquals(didKey1, didKey2, "did:key must be stable across instances with same key file")
    assertNotEquals("", didKey1, "did:key must be non-empty")
  }

  @Test
  fun `derived did-key starts with z6Mk`(@TempDir tempDir: Path) = runBlocking {
    val store = SigningKeyStore(tempDir.resolve("dva-signing-key.pem").toString())
    store.loadOrGenerate()
    val didKey = store.issuerDidKey()
    assertTrue(didKey.startsWith("did:key:z6Mk"), "did:key must start with did:key:z6Mk, was: $didKey")
  }
}