@file:UseSerializers(UuidSerializer::class, URLSerializer::class)
@file:OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)

package hu.bme.mit.ftsrg.dva.log

import hu.bme.mit.ftsrg.serialization.URLSerializer
import hu.bme.mit.ftsrg.serialization.UuidSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.json.JsonElement
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Serializable
data class RequestLog(
    val id: Uuid,
    val type: RequestType,
    val requestID: Uuid,
    val exchangeID: String,
    val contractID: String,
    val vlaID: Uuid?,
    val data: JsonElement,
    val attesterID: String,
    val evaluationPassing: Boolean? = null,
    val evaluationResults: String? = null,
    val receivedDate: Instant,
    val evaluationDate: Instant? = null,
    val vcIssuedDate: Instant? = null,
    val vcID: String? = null,
)

@Serializable
enum class RequestType { ATTESTATION_REQUEST, PROOF_REQUEST }

@Serializable
data class RequestLogNew(
    val type: RequestType,
    val requestID: Uuid,
    val exchangeID: String,
    val contractID: String,
    val vlaID: Uuid,
    val data: JsonElement,
    val attesterID: String,
    val evaluationPassing: Boolean? = null,
    val evaluationResults: String? = null,
    val receivedDate: Instant,
    val evaluationDate: Instant? = null,
    val vcIssuedDate: Instant? = null,
    val vcID: String? = null,
)