@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestType
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toInstant
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import org.jetbrains.exposed.v1.datetime.datetime
import java.util.*
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toKotlinUuid

object RequestLogsTable : UUIDTable("request_logs") {
    val type = varchar("type", 255)
    val requestID = varchar("request_id", 255)
    val exchangeID = varchar("exchange_id", 255)
    val contractID = varchar("contract_id", 255)
    val vlaID = varchar("vla_id", 255)
    val data = text("data")
    val attesterID = varchar("attester_id", 255)
    val evaluationPassing = bool("evaluation_passing").nullable()
    val evaluationResults = text("evaluation_results").nullable()
    val receivedDate = datetime("received_date")
    val evaluationDate = datetime("evaluation_date").nullable()
    val vcIssuedDate = datetime("vc_issued_date").nullable()
    val vcID = varchar("vc_id", 255).nullable()
}

class RequestLogEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<RequestLogEntity>(RequestLogsTable)

    var type by RequestLogsTable.type
    var requestID by RequestLogsTable.requestID
    var exchangeID by RequestLogsTable.exchangeID
    var contractID by RequestLogsTable.contractID
    var vlaID by RequestLogsTable.vlaID
    var data by RequestLogsTable.data
    var attesterID by RequestLogsTable.attesterID
    var evaluationPassing by RequestLogsTable.evaluationPassing
    var evaluationResults by RequestLogsTable.evaluationResults
    var receivedDate by RequestLogsTable.receivedDate
    var evaluationDate by RequestLogsTable.evaluationDate
    var vcIssuedDate by RequestLogsTable.vcIssuedDate
    var vcID by RequestLogsTable.vcID
}

@OptIn(ExperimentalTime::class)
fun RequestLogEntity.toModel() = RequestLog(
    id = id.value.toKotlinUuid(),
    type = RequestType.valueOf(type),
    requestID = Uuid.parse(requestID),
    exchangeID = exchangeID,
    contractID = contractID,
    vlaID = Uuid.parse(vlaID),
    data = Json.decodeFromString(data),
    attesterID = attesterID,
    evaluationPassing = evaluationPassing,
    evaluationResults = evaluationResults,
    receivedDate = receivedDate.toInstant(UTC),
    evaluationDate = evaluationDate?.toInstant(UTC),
    vcIssuedDate = vcIssuedDate?.toInstant(UTC),
    vcID = vcID,
)