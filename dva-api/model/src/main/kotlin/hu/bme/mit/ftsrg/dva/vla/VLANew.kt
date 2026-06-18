package hu.bme.mit.ftsrg.dva.vla

import hu.bme.mit.ftsrg.odcs.DataQuality
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

// HACK: Partial schema to avoid complexity
// TODO: Verify conformance to ODCS
@Serializable
data class VLANew(
    val description: String? = null,
    val servers: JsonArray? = null,
    val schema: JsonObject? = null,
    val quality: List<DataQuality>? = null,
    val price: JsonObject? = null,
    val team: JsonArray? = null,
    val roles: JsonArray? = null,
    val slaProperties: JsonArray? = null,
    val support: JsonArray? = null,
    val tags: JsonArray? = null,
)

@Serializable
data class VLANewFromTemplates(
    val description: String? = null,
    val servers: JsonArray? = null,
    val schema: JsonObject? = null,
    val quality: List<DataQuality>? = null,
    val price: JsonObject? = null,
    val team: JsonArray? = null,
    val roles: JsonArray? = null,
    val slaProperties: JsonArray? = null,
    val support: JsonArray? = null,
    val tags: JsonArray? = null,
    val qualityTemplates: List<TemplateInstantiation>? = null,
)

@OptIn(ExperimentalUuidApi::class)
@Serializable
data class TemplateInstantiation(val id: Uuid, val model: JsonObject)