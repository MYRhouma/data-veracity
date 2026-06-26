@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.jws.WhitelistEntry
import hu.bme.mit.ftsrg.dva.jws.WhitelistRepo
import org.jetbrains.exposed.v1.core.SqlExpressionBuilder.eq
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import org.jetbrains.exposed.v1.jdbc.deleteWhere
import java.util.*
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.toKotlinUuid

object DidKeyWhitelistTable : UUIDTable("did_key_whitelist") {
    val didKey = varchar("did_key", 255).uniqueIndex()
    val label = varchar("label", 255).nullable()
}

class WhitelistEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<WhitelistEntity>(DidKeyWhitelistTable)

    var didKey by DidKeyWhitelistTable.didKey
    var label by DidKeyWhitelistTable.label
}

fun WhitelistEntity.toModel() = WhitelistEntry(
    didKey = didKey,
    label = label,
)

class PgWhitelistRepo : WhitelistRepo {
    override suspend fun all() = suspendTransaction {
        WhitelistEntity.all().map { it.toModel() }
    }

    override suspend fun add(didKey: String, label: String?) = suspendTransaction {
        WhitelistEntity.new {
            this.didKey = didKey
            this.label = label
        }.toModel()
    }

    override suspend fun remove(didKey: String): Boolean = suspendTransaction {
        val rowsDeleted = DidKeyWhitelistTable.deleteWhere { DidKeyWhitelistTable.didKey eq didKey }
        rowsDeleted > 0
    }

    override suspend fun contains(didKey: String): Boolean = suspendTransaction {
        WhitelistEntity.find { DidKeyWhitelistTable.didKey eq didKey }.count() > 0
    }
}
