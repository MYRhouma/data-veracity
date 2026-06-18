@file:UseSerializers(UuidSerializer::class, URLSerializer::class)
@file:OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)

package hu.bme.mit.ftsrg.dva.log

import hu.bme.mit.ftsrg.serialization.URLSerializer
import hu.bme.mit.ftsrg.serialization.UuidSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.json.JsonObject
import java.net.URL
import kotlin.time.ExperimentalTime
import kotlin.time.Instant
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid


@Serializable
data class VerifRequestLog(
    val id: Uuid,
    val exchangeID: String,
    val contractID: String,
    val attesterAgentURL: URL,
    val attesterAgentLabel: String,
    val receivedDate: Instant,
    val verificationDate: Instant? = null,
    val verified: Boolean = false,
    val presentationRequestData: JsonObject? = null,
)

@Serializable
data class VerifRequestLogNew(
    val exchangeID: String,
    val contractID: String,
    val attesterAgentURL: URL,
    val attesterAgentLabel: String,
    val receivedDate: Instant,
)

@Serializable
data class VerifRequestLogPatch(
    val id: Uuid,
    val verificationDate: Instant? = null,
    val verified: Boolean? = null,
    val presentationRequestData: JsonObject? = null,
)