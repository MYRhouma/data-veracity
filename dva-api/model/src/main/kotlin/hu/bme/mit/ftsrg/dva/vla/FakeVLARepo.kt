package hu.bme.mit.ftsrg.dva.vla

import kotlinx.serialization.json.*
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
class FakeVLARepo : VLARepo {
    val vlas = mutableMapOf<Uuid, JsonObject>(
        Uuid.NIL to buildJsonObject {
            put("description", "Dummy VLA")
            putJsonArray("quality") {
                addJsonObject {
                    put("engine", "dummy")
                    put("implementation", "dummy")
                }
            }
        }
    )

    override suspend fun all(): List<JsonObject> = vlas.values.toList()

    override suspend fun byID(id: Uuid): JsonObject? = vlas[id]

    override suspend fun add(vla: JsonObject): Uuid? {
        val id = Uuid.random()
        val vlaWithID = JsonObject(vla + mapOf("id" to JsonPrimitive(id.toString())))
        vlas.put(id, vlaWithID)
        return id
    }

    override suspend fun removeAll() {
        vlas.clear()
    }
}