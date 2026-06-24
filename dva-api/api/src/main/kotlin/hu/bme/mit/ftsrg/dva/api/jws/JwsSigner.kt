package hu.bme.mit.ftsrg.dva.api.jws

import com.nimbusds.jose.JWSObject
import com.nimbusds.jose.util.Base64URL
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.add
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import kotlinx.serialization.json.putJsonObject
import java.nio.charset.StandardCharsets
import java.security.Signature

/**
 * The eight AnonCreds attributes of an Attestation-of-Veracity (AoV) credential,
 * carried verbatim as `credentialSubject` claims of the signed VC.
 */
public data class AovClaims(
  public val vcId: String,
  public val validSince: String,
  public val subject: String,
  public val issuerId: String,
  public val recordId: String,
  public val contractId: String,
  public val dataExchangeId: String,
  public val payload: String,
)

private const val JWS_HEADER_ALG = "EdDSA"
private const val JWS_HEADER_TYPE = "VC+LD-JSON+JWS"
private const val VC_CONTEXT = "https://www.w3.org/2018/credentials/v1"
private const val VC_TYPE = "VerifiableCredential"
private const val AOV_TYPE = "AttestationOfVeracity"

private fun JsonObject.toBase64Url(): String =
  Base64URL.encode(Json.encodeToString(JsonObject.serializer(), this).toByteArray(StandardCharsets.UTF_8)).toString()

private fun buildAovPayload(claims: AovClaims, issuerDidKey: String): JsonObject = buildJsonObject {
  putJsonArray("@context") { add(VC_CONTEXT) }
  putJsonArray("type") {
    add(VC_TYPE)
    add(AOV_TYPE)
  }
  put("issuer", issuerDidKey)
  put("validFrom", claims.validSince)
  putJsonObject("credentialSubject") {
    put("vc_id", claims.vcId)
    put("valid_since", claims.validSince)
    put("subject", claims.subject)
    put("issuer_id", claims.issuerId)
    put("record_id", claims.recordId)
    put("contract_id", claims.contractId)
    put("data_exchange_id", claims.dataExchangeId)
    put("payload", claims.payload)
  }
}

private fun buildJwsHeader(): JsonObject = buildJsonObject {
  put("alg", JWS_HEADER_ALG)
  put("typ", JWS_HEADER_TYPE)
}

/**
 * Builds a JSON-LD Verifiable Credential describing the supplied [claims], then
 * JWS-signs its compact serialization (header `alg=EdDSA`, `typ=VC+LD-JSON+JWS`)
 * with the supplied Ed25519 private key via the JDK 15+ `Signature("Ed25519")`
 * primitive, returning the compact JWS string.
 *
 * @param claims the AoV credential-subject claims to sign.
 * @param privateKey the raw Ed25519 private key.
 * @param issuerDidKey the `did:key` identifier of the issuer, embedded in `issuer`.
 * @return the compact JWS string `header.payload.signature`.
 */
public fun signEd25519(claims: AovClaims, privateKey: Ed25519PrivateKey, issuerDidKey: String): String {
  val headerB64 = buildJwsHeader().toBase64Url()
  val payloadB64 = buildAovPayload(claims, issuerDidKey).toBase64Url()
  val signingInput = "$headerB64.$payloadB64".toByteArray(StandardCharsets.UTF_8)

  val signer = Signature.getInstance("Ed25519")
  signer.initSign(privateKey)
  signer.update(signingInput)
  val signature = signer.sign()

  val signatureB64 = Base64URL.encode(signature).toString()
  return "$headerB64.$payloadB64.$signatureB64"
}

/**
 * Parses and verifies a compact JWS signed with Ed25519.
 *
 * Malformed JWS input (wrong number of parts, bad base64url, etc.) propagates as
 * an exception. A cryptographically invalid signature returns `false` rather
 * than throwing, so callers can decide whether to treat the failure as fatal.
 *
 * @param jws the compact JWS string to verify.
 * @param publicKey the raw Ed25519 public key.
 * @return `true` if the signature is valid, `false` if the signature does not verify.
 */
public fun verifyEd25519(jws: String, publicKey: Ed25519PublicKey): Boolean {
  val parsed = JWSObject.parse(jws)
  val signingInput = parsed.signingInput
  val signatureBytes = parsed.signature.decode()

  val verifier = Signature.getInstance("Ed25519")
  verifier.initVerify(publicKey)
  verifier.update(signingInput)
  return try {
    verifier.verify(signatureBytes)
  } catch (e: java.security.SignatureException) {
    false
  }
}