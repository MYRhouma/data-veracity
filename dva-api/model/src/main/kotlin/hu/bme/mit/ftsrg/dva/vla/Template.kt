@file:UseSerializers(UuidSerializer::class)
@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.vla

import hu.bme.mit.ftsrg.serialization.UuidSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import kotlinx.serialization.json.JsonObject
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Serializable
data class Template(
    val id: Uuid,
    val name: String,
    val description: String? = null,
    val criterionType: CriterionType,
    val targetAspect: QualityAspect,
    val evaluationMethod: EvaluationMethod
)

@Serializable
data class EvaluationMethod(val engine: Engine, val variableSchema: JsonObject, val implementationTemplate: String)

@Serializable
enum class Engine { SCHEMA, GREAT_EXPECTATIONS, JQ }

@Serializable
enum class CriterionType { VALID_INVALID, IN_RANGE, GREATER_THAN, LESS_THAN }

@Serializable
enum class QualityAspect { SYNTAX, TIMELINESS, ACCURACY, COMPLETENESS, CONSISTENCY }

@Serializable
data class TemplateNew(
    val name: String,
    val description: String? = null,
    val criterionType: CriterionType,
    val targetAspect: QualityAspect,
    val evaluationMethod: EvaluationMethod
)

@Serializable
data class TemplatePatch(
    val id: Uuid,
    val name: String? = null,
    val description: String? = null,
    val criterionType: CriterionType? = null,
    val targetAspect: QualityAspect? = null,
    val evaluationMethod: EvaluationMethod? = null
)