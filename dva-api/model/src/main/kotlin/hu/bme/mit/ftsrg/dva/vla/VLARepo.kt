package hu.bme.mit.ftsrg.dva.vla

import kotlinx.serialization.json.JsonObject
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface VLARepo {
    suspend fun all(): List<JsonObject>
    suspend fun byID(id: Uuid): JsonObject?
    suspend fun add(vla: JsonObject): Uuid?
    suspend fun removeAll()
}