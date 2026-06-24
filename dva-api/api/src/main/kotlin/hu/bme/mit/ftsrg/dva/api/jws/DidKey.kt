package hu.bme.mit.ftsrg.dva.api.jws

import java.math.BigInteger
import java.security.KeyFactory
import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.interfaces.EdECPrivateKey
import java.security.interfaces.EdECPublicKey
import java.security.spec.EdECPoint
import java.security.spec.EdECPublicKeySpec
import java.security.spec.NamedParameterSpec

public typealias Ed25519PublicKey = EdECPublicKey
public typealias Ed25519PrivateKey = EdECPrivateKey

private const val ED25519_RAW_SIZE = 32
private val ED25519_MULTICODEC_PREFIX = byteArrayOf(0xed.toByte(), 0x01)
private const val MULTIBASE_BASE58BTC_PREFIX = 'z'
private const val DID_KEY_SCHEME = "did:key:"
private const val BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

private object Base58Bitcoin {
  private val INDEX = HashMap<Char, Int>().apply {
    BASE58_ALPHABET.forEachIndexed { i, c -> put(c, i) }
  }

  fun encode(input: ByteArray): String {
    val zeroCount = input.takeWhile { it == 0.toByte() }.size
    var num = BigInteger(1, input)
    val sb = StringBuilder()
    while (num > BigInteger.ZERO) {
      val (div, rem) = num.divideAndRemainder(BigInteger.valueOf(58))
      num = div
      sb.append(BASE58_ALPHABET[rem.toInt()])
    }
    repeat(zeroCount) { sb.append('1') }
    return sb.reverse().toString()
  }

  fun decode(input: String): ByteArray {
    var num = BigInteger.ZERO
    for (c in input) {
      val idx = INDEX[c] ?: throw IllegalArgumentException("invalid base58 character: $c")
      num = num.multiply(BigInteger.valueOf(58)).add(BigInteger.valueOf(idx.toLong()))
    }
    val bytes = if (num == BigInteger.ZERO) ByteArray(0) else num.toByteArray()
    val stripped = if (bytes.isNotEmpty() && bytes[0] == 0.toByte()) bytes.copyOfRange(1, bytes.size) else bytes
    val leadingOnes = input.takeWhile { it == '1' }.length
    return ByteArray(leadingOnes) + stripped
  }
}

internal fun ByteArray.toLittleEndianFixed(size: Int): ByteArray {
  require(this.size <= size) { "value too large for $size-byte little-endian field: ${this.size}" }
  val out = ByteArray(size)
  val reversedSource = this.reversedArray()
  reversedSource.copyInto(out, 0, 0, reversedSource.size)
  return out
}

/**
 * Returns the raw 32-byte Ed25519 public-key encoding of [publicKey]: little-endian Y
 * with the parity bit of X stored in the most significant bit of byte 31 (RFC 8032).
 */
public fun rawBytes(publicKey: Ed25519PublicKey): ByteArray {
  val point = publicKey.point
  val yBigEndian = point.y.toByteArray().let {
    if (it.isNotEmpty() && it[0] == 0.toByte()) it.copyOfRange(1, it.size) else it
  }
  val out = yBigEndian.toLittleEndianFixed(ED25519_RAW_SIZE)
  if (point.isXOdd) {
    out[ED25519_RAW_SIZE - 1] = (out[ED25519_RAW_SIZE - 1].toInt() or 0x80).toByte()
  }
  return out
}

/**
 * Reconstructs an [Ed25519PublicKey] from its raw 32-byte RFC 8032 encoding.
 */
public fun ed25519PublicKeyFromRaw(raw: ByteArray): Ed25519PublicKey {
  require(raw.size == ED25519_RAW_SIZE) { "Ed25519 public key must be exactly 32 bytes, got ${raw.size}" }
  val xOdd = (raw[ED25519_RAW_SIZE - 1].toInt() and 0x80) != 0
  val yLittleEndian = raw.copyOf()
  yLittleEndian[ED25519_RAW_SIZE - 1] = (yLittleEndian[ED25519_RAW_SIZE - 1].toInt() and 0x7f).toByte()
  val yBigEndian = yLittleEndian.reversedArray()
  val y = BigInteger(1, yBigEndian)
  val point = EdECPoint(xOdd, y)
  val spec = EdECPublicKeySpec(NamedParameterSpec("Ed25519"), point)
  return KeyFactory.getInstance("EdDSA").generatePublic(spec) as Ed25519PublicKey
}

/**
 * Generates a fresh Ed25519 [KeyPair] using the JDK 15+ `EdDSA` `KeyPairGenerator`.
 */
public fun generateEd25519KeyPair(): KeyPair =
  KeyPairGenerator.getInstance("Ed25519").generateKeyPair()

/**
 * Encodes an Ed25519 public key as a `did:key` identifier using the
 * `multibase(base58btc(multicodec-prefix 0xed01 || raw-public-key))` form
 * defined by the W3C did:key specification.
 */
public fun ed25519PublicKeyToDidKey(publicKey: Ed25519PublicKey): String {
  val raw = rawBytes(publicKey)
  val multicodec = ED25519_MULTICODEC_PREFIX + raw
  return DID_KEY_SCHEME + MULTIBASE_BASE58BTC_PREFIX + Base58Bitcoin.encode(multicodec)
}

/**
 * Decodes a `did:key` identifier whose multicodec prefix is `0xed01` (Ed25519)
 * back into an [Ed25519PublicKey].
 */
public fun didKeyToEd25519PublicKey(didKey: String): Ed25519PublicKey {
  require(didKey.startsWith(DID_KEY_SCHEME)) { "not a did:key identifier: $didKey" }
  val multibase = didKey.removePrefix(DID_KEY_SCHEME)
  require(multibase.startsWith(MULTIBASE_BASE58BTC_PREFIX.toString())) {
    "only base58btc multibase ('z') is supported, got: $multibase"
  }
  val decoded = Base58Bitcoin.decode(multibase.substring(1))
  require(decoded.size == ED25519_MULTICODEC_PREFIX.size + ED25519_RAW_SIZE) {
    "decoded multicodec is ${decoded.size} bytes, expected ${ED25519_MULTICODEC_PREFIX.size + ED25519_RAW_SIZE}"
  }
  require(decoded[0] == ED25519_MULTICODEC_PREFIX[0] && decoded[1] == ED25519_MULTICODEC_PREFIX[1]) {
    "multicodec prefix 0x${(decoded[0].toInt() and 0xff).toString(16)}${(decoded[1].toInt() and 0xff).toString(16)} is not the Ed25519 prefix 0xed01"
  }
  val raw = decoded.copyOfRange(ED25519_MULTICODEC_PREFIX.size, decoded.size)
  return ed25519PublicKeyFromRaw(raw)
}