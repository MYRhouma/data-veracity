package hu.bme.mit.ftsrg.dva.api.db

import hu.bme.mit.ftsrg.dva.log.ReqestLogRepo
import hu.bme.mit.ftsrg.dva.log.RequestLog
import hu.bme.mit.ftsrg.dva.log.RequestLogNew
import kotlinx.datetime.TimeZone.Companion.UTC
import kotlinx.datetime.toLocalDateTime
import kotlinx.serialization.json.Json
import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid
import kotlin.uuid.toJavaUuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class PgRequestLogRepo : ReqestLogRepo {
    override suspend fun all(): List<RequestLog> = suspendTransaction {
        RequestLogEntity.all().map { it.toModel() }
    }

    override suspend fun byID(id: Uuid): RequestLog? = suspendTransaction {
        RequestLogEntity.findById(id.toJavaUuid())?.toModel()
    }

    override suspend fun byRequestID(requestID: Uuid): RequestLog? = suspendTransaction {
        RequestLogEntity.find { RequestLogsTable.requestID eq requestID.toString() }.firstOrNull()?.toModel()
    }

    override suspend fun add(request: RequestLogNew): RequestLog? = suspendTransaction {
        RequestLogEntity.new {
            type = request.type.name
            requestID = request.requestID.toString()
            exchangeID = request.exchangeID
            contractID = request.contractID
            vlaID = request.vlaID.toString()
            data = Json.encodeToString(request.data)
            attesterID = request.attesterID
            evaluationPassing = request.evaluationPassing ?: false
            evaluationResults = Json.encodeToString(request.evaluationResults)
            receivedDate = request.receivedDate.toLocalDateTime(UTC)
            evaluationDate = request.evaluationDate?.toLocalDateTime(UTC)
            vcIssuedDate = request.vcIssuedDate?.toLocalDateTime(UTC)
            vcID = request.vcID
            trancheLevel = request.trancheLevel
            tranchePercentage = request.tranchePercentage
            trancheEvaluation = request.trancheEvaluation
        }.toModel()
    }
}