package hu.bme.mit.ftsrg.dva.log

import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class FakeReqestLogRepo : ReqestLogRepo {
    private val requests = mutableMapOf<Uuid, RequestLog>()

    override suspend fun all(): List<RequestLog> = requests.values.toList()

    override suspend fun byID(id: Uuid): RequestLog? = requests[id]

    override suspend fun byRequestID(requestID: Uuid): RequestLog? =
        requests.values.firstOrNull { it.requestID == requestID }

    override suspend fun add(request: RequestLogNew): RequestLog? {
        val entity = RequestLog(
            id = Uuid.random(),
            type = request.type,
            requestID = request.requestID,
            exchangeID = request.exchangeID,
            contractID = request.contractID,
            vlaID = request.vlaID,
            data = request.data,
            attesterID = request.attesterID,
            evaluationPassing = request.evaluationPassing,
            evaluationResults = request.evaluationResults,
            receivedDate = request.receivedDate,
            evaluationDate = request.evaluationDate,
            vcIssuedDate = request.vcIssuedDate,
            vcID = request.vcID,
        )
        requests.put(entity.id, entity)
        return entity
    }
}