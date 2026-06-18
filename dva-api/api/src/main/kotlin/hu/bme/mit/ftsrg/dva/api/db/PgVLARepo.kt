package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.vla.VLARepo
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import org.jetbrains.exposed.v1.jdbc.deleteAll
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid
import kotlin.uuid.toKotlinUuid

@OptIn(ExperimentalUuidApi::class)
class PgVLARepo : VLARepo {
    override suspend fun all(): List<JsonObject> = suspendTransaction { VLAEntity.all().map { it.toModel() } }

    override suspend fun byID(id: Uuid): JsonObject? =
        suspendTransaction { VLAEntity.findById(id.toJavaUuid())?.toModel() }

    override suspend fun add(vla: JsonObject): Uuid? = suspendTransaction {
        val entity = VLAEntity.new { odcs = Json.encodeToString(vla) }
        entity.id.value.toKotlinUuid()
    }

    override suspend fun removeAll(): Unit = suspendTransaction { VLAsTable.deleteAll() }
}