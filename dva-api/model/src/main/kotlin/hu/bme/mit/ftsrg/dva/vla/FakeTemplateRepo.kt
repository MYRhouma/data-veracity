package hu.bme.mit.ftsrg.dva.vla

import hu.bme.mit.ftsrg.dva.vla.CriterionType.VALID_INVALID
import hu.bme.mit.ftsrg.dva.vla.QualityAspect.SYNTAX
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
class FakeTemplateRepo : TemplateRepo {
    private val templates = mutableMapOf(
        Uuid.NIL to Template(
            id = Uuid.NIL,
            name = "JSON Schema",
            description = "Data should conform to a JSON schema with the given URL",
            criterionType = VALID_INVALID,
            targetAspect = SYNTAX,
            evaluationMethod = EvaluationMethod(
                engine = Engine.SCHEMA,
                variableSchema = buildJsonObject {
                    put("type", "object")
                    putJsonObject("properties") {
                        putJsonObject("schemaURL") {
                            put("type", "string")
                            put("format", "uri")
                        }
                    }
                },
                implementationTemplate = "{{ schemaURL }}"
            )
        )
    )

    override suspend fun all(): List<Template> {
        return templates.values.toList()
    }

    override suspend fun byID(id: Uuid): Template? {
        return templates[id]
    }

    override suspend fun add(template: TemplateNew): Template? {
        val entity = Template(
            id = Uuid.random(),
            name = template.name,
            description = template.description,
            criterionType = template.criterionType,
            targetAspect = template.targetAspect,
            evaluationMethod = template.evaluationMethod
        )
        templates.put(entity.id, entity)
        return entity
    }

    override suspend fun update(patch: TemplatePatch): Template? {
        val existingTemplate = templates[patch.id] ?: return null

        val patchedTemplate = Template(
            id = patch.id,
            name = patch.name ?: existingTemplate.name,
            description = patch.description ?: existingTemplate.description,
            criterionType = patch.criterionType ?: existingTemplate.criterionType,
            targetAspect = patch.targetAspect ?: existingTemplate.targetAspect,
            evaluationMethod = patch.evaluationMethod ?: existingTemplate.evaluationMethod
        )

        templates.put(patch.id, patchedTemplate)
        return patchedTemplate
    }

    override suspend fun remove(id: Uuid): Boolean {
        if (templates[id] == null) return false
        templates.remove(id)
        return true
    }

    override suspend fun removeAll() {
        templates.clear()
    }
}