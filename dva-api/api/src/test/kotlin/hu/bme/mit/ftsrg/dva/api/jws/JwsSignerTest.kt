package hu.bme.mit.ftsrg.dva.api.jws

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertThrows
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class JwsSignerTest {

  @Test
  fun `signs and verifies a valid AoV`() {
    val keyPair = generateEd25519KeyPair()
    val privateKey = keyPair.private as Ed25519PrivateKey
    val publicKey = keyPair.public as Ed25519PublicKey

    val claims = AovClaims(
      vcId = "urn:uuid:11111111-2222-3333-4444-555555555555",
      validSince = "2024-01-01T00:00:00Z",
      subject = "did:web:data-consumer.example",
      issuerId = "did:web:data-provider.example",
      recordId = "rec-0001",
      contractId = "contract-0001",
      dataExchangeId = "xchg-0001",
      payload = "checksum:sha256:abcdef0123456789",
    )

    val issuerDidKey = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

    val jws = signEd25519(claims, privateKey, issuerDidKey)

    assertTrue(jws.isNotEmpty(), "JWS must not be empty")
    assertEquals(3, jws.split(".").size, "Compact JWS must have 3 dot-separated parts")

    val verified = verifyEd25519(jws, publicKey)
    assertTrue(verified, "verifyEd25519 must return true for a valid signature")
  }

  @Test
  fun `tampered payload fails verification`() {
    val keyPair = generateEd25519KeyPair()
    val privateKey = keyPair.private as Ed25519PrivateKey
    val publicKey = keyPair.public as Ed25519PublicKey

    val claims = AovClaims(
      vcId = "urn:uuid:11111111-2222-3333-4444-555555555555",
      validSince = "2024-01-01T00:00:00Z",
      subject = "did:web:data-consumer.example",
      issuerId = "did:web:data-provider.example",
      recordId = "rec-0001",
      contractId = "contract-0001",
      dataExchangeId = "xchg-0001",
      payload = "checksum:sha256:abcdef0123456789",
    )

    val jws = signEd25519(claims, privateKey, "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK")

    val parts = jws.split(".")
    val originalPayloadSegment = parts[1]
    val firstChar = originalPayloadSegment.first()
    val flippedChar = if (firstChar == 'A') 'B' else 'A'
    val tamperedPayloadSegment = flippedChar + originalPayloadSegment.substring(1)
    val tamperedJws = "${parts[0]}.$tamperedPayloadSegment.${parts[2]}"

    val verified = verifyEd25519(tamperedJws, publicKey)
    assertFalse(verified, "verifyEd25519 must return false (not throw) for a tampered payload")
  }

  @Test
  fun `rejection of a clearly-malformed JWS`() {
    val keyPair = generateEd25519KeyPair()
    val publicKey = keyPair.public as Ed25519PublicKey

    assertThrows(Exception::class.java) {
      verifyEd25519("not.a.jws.at.all", publicKey)
    }
  }
}