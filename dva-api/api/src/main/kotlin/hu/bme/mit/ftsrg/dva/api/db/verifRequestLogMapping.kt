@file:OptIn(ExperimentalUuidApi::class)

package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.VerifRequestLog
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toInstant
import kotlinx.serialization.json.Json
import org.jetbrains.exposed.v1.core.dao.id.EntityID
import org.jetbrains.exposed.v1.core.dao.id.UUIDTable
import org.jetbrains.exposed.v1.dao.UUIDEntity
import org.jetbrains.exposed.v1.dao.UUIDEntityClass
import org.jetbrains.exposed.v1.datetime.datetime
import java.net.URI
import java.util.*
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.toKotlinUuid

object VerifRequestLogsTable : UUIDTable("verification_request_logs") {
    val exchangeID = varchar("exchange_id", 255)
    val contractID = varchar("contract_id", 255)
    val attesterAgentURL = varchar("attester_agent_url", 255)
    val attesterAgentLabel = varchar("attester_agent_label", 255)
    val receivedDate = datetime("received_date")
    val verificationDate = datetime("verification_date").nullable()
    val verified = bool("verified").default(false)
    val presentationRequestData = text("presentation_request_data").nullable()
}

class VerifRequestLogEntity(id: EntityID<UUID>) : UUIDEntity(id) {
    companion object : UUIDEntityClass<VerifRequestLogEntity>(VerifRequestLogsTable)

    var exchangeID by VerifRequestLogsTable.exchangeID
    var contractID by VerifRequestLogsTable.contractID
    var attesterAgentURL by VerifRequestLogsTable.attesterAgentURL
    var attesterAgentLabel by VerifRequestLogsTable.attesterAgentLabel
    var receivedDate by VerifRequestLogsTable.receivedDate
    var verificationDate by VerifRequestLogsTable.verificationDate
    var verified by VerifRequestLogsTable.verified
    var presentationRequestData by VerifRequestLogsTable.presentationRequestData
}

@OptIn(ExperimentalTime::class)
fun VerifRequestLogEntity.toModel() = VerifRequestLog(
    id = id.value.toKotlinUuid(),
    exchangeID = exchangeID,
    contractID = contractID,
    attesterAgentURL = URI(attesterAgentURL).toURL(),
    attesterAgentLabel = attesterAgentLabel,
    receivedDate = receivedDate.toInstant(UTC),
    verificationDate = verificationDate?.toInstant(UTC),
    verified = verified,
    presentationRequestData = presentationRequestData?.let { Json.decodeFromString(it) },
)