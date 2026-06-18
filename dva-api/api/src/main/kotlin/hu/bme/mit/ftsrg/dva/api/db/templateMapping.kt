package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.vla.*
import kotlinx.coroutines.Dispatchers
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import org.jetbrains.exposed.v1.core.Transaction
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import org.jetbrains.exposed.v1.jdbc.transactions.experimental.newSuspendedTransaction
import java.util.*
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.toKotlinUuid

object TemplatesTable : UUIDTable() {
    val name = varchar("name", 255)
    val description = text("description")
    val criterionType = varchar("criterion_type", 255)
    val targetAspect = varchar("target_aspect", 255)
    val evaluationMethod = reference("evaluation_method_id", EvaluationMethodsTable.id)
}

class TemplateEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<TemplateEntity>(TemplatesTable)

    var name by TemplatesTable.name
    var description by TemplatesTable.description
    var criterionType by TemplatesTable.criterionType
    var targetAspect by TemplatesTable.targetAspect
    var evaluationMethod by EvaluationMethodEntity referencedOn TemplatesTable.evaluationMethod
}

object EvaluationMethodsTable : UUIDTable("evaluation_methods") {
    val engine = varchar("engine", 255)
    val variableShema = text("variable_schema")
    val implementationTemplate = text("implementation_template")
}

class EvaluationMethodEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<EvaluationMethodEntity>(EvaluationMethodsTable)

    var engine by EvaluationMethodsTable.engine
    var variableSchema by EvaluationMethodsTable.variableShema
    var implementationTemplate by EvaluationMethodsTable.implementationTemplate
}

@OptIn(ExperimentalUuidApi::class)
fun TemplateEntity.toModel() = Template(
    id = id.value.toKotlinUuid(),
    name = name,
    description = description,
    criterionType = CriterionType.valueOf(criterionType),
    targetAspect = QualityAspect.valueOf(targetAspect),
    evaluationMethod = evaluationMethod.toModel(),
)

fun EvaluationMethodEntity.toModel() = EvaluationMethod(
    engine = Engine.valueOf(engine),
    variableSchema = Json.decodeFromString<JsonObject>(variableSchema),
    implementationTemplate = implementationTemplate,
)