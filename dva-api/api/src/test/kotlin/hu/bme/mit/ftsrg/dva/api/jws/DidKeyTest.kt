package hu.bme.mit.ftsrg.dva.api.jws

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class DidKeyTest {

  @Test
  fun `Ed25519 key round-trips through did-key`() {
    val keyPair = generateEd25519KeyPair()
    val publicKey = keyPair.public as Ed25519PublicKey

    val didKey = ed25519PublicKeyToDidKey(publicKey)
    val roundTripped = didKeyToEd25519PublicKey(didKey)
    val roundTrippedDidKey = ed25519PublicKeyToDidKey(roundTripped)

    assertEquals(didKey, roundTrippedDidKey, "did-key round-trip must produce the same identifier")
  }

  @Test
  fun `known spec vector`() {
    val expectedDidKey = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    val decoded = didKeyToEd25519PublicKey(expectedDidKey)
    val reencoded = ed25519PublicKeyToDidKey(decoded)
    assertEquals(expectedDidKey, reencoded)
  }

  @Test
  fun `starts with did-key z6Mk`() {
    val keyPair = generateEd25519KeyPair()
    val publicKey = keyPair.public as Ed25519PublicKey
    val didKey = ed25519PublicKeyToDidKey(publicKey)
    assertTrue(didKey.startsWith("did:key:z6Mk"), "did:key identifier must start with 'did:key:z6Mk'")
  }
}