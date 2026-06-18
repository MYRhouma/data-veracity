package hu.bme.mit.ftsrg.dva.evaluation

import hu.bme.mit.ftsrg.odcs.DataQuality
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Serializable
data class Evaluate(
    val requirement: DataQuality,
    val data: JsonObject,
)

@OptIn(ExperimentalUuidApi::class)
@Serializable
data class EvaluateFromTemplate(
    val templateID: Uuid,
    val templateModel: JsonObject,
    val data: JsonObject,
)
