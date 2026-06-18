package hu.bme.mit.ftsrg.dva.vla

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface TemplateRepo {
    suspend fun all(): List<Template>
    suspend fun byID(id: Uuid): Template?
    suspend fun add(template: TemplateNew): Template?
    suspend fun update(patch: TemplatePatch): Template?
    suspend fun remove(id: Uuid): Boolean
    suspend fun removeAll()
}