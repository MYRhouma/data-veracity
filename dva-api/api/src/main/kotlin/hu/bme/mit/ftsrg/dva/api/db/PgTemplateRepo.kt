package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.vla.Template
import hu.bme.mit.ftsrg.dva.vla.TemplateNew
import hu.bme.mit.ftsrg.dva.vla.TemplatePatch
import hu.bme.mit.ftsrg.dva.vla.TemplateRepo
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.v1.core.SqlExpressionBuilder.eq
import org.jetbrains.exposed.v1.jdbc.deleteAll
import org.jetbrains.exposed.v1.jdbc.deleteWhere
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid

@OptIn(ExperimentalUuidApi::class)
class PgTemplateRepo : TemplateRepo {
    override suspend fun all(): List<Template> = suspendTransaction {
        TemplateEntity.all().map { it.toModel() }
    }

    override suspend fun byID(id: Uuid): Template? = suspendTransaction {
        TemplateEntity.findById(id.toJavaUuid())?.toModel()
    }

    override suspend fun add(template: TemplateNew): Template? = suspendTransaction {
        TemplateEntity.new {
            name = template.name
            description = template.description ?: ""
            criterionType = template.criterionType.name
            targetAspect = template.targetAspect.name
            evaluationMethod = EvaluationMethodEntity.new {
                engine = template.evaluationMethod.engine.name
                variableSchema = Json.encodeToString(template.evaluationMethod.variableSchema)
                implementationTemplate = template.evaluationMethod.implementationTemplate
            }
        }.toModel()
    }

    override suspend fun update(patch: TemplatePatch): Template? = suspendTransaction {
        TemplateEntity.findById(patch.id.toJavaUuid())?.apply {
            name = patch.name ?: name
            description = patch.description ?: description
            criterionType = patch.criterionType?.name ?: criterionType
            targetAspect = patch.targetAspect?.name ?: targetAspect
            patch.evaluationMethod?.let { newMethod ->
                evaluationMethod.engine = newMethod.engine.name
                evaluationMethod.variableSchema = Json.encodeToString(newMethod.variableSchema)
                evaluationMethod.implementationTemplate = newMethod.implementationTemplate
            }
        }?.toModel()
    }

    override suspend fun remove(id: Uuid): Boolean = suspendTransaction {
        val rowsDeleted = TemplatesTable.deleteWhere {
            TemplatesTable.id eq id.toJavaUuid()
        }
        rowsDeleted == 1
    }

    override suspend fun removeAll(): Unit = suspendTransaction { TemplatesTable.deleteAll() }
}