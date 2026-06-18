package hu.bme.mit.ftsrg.dva.log

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface ReqestLogRepo {
    suspend fun all(): List<RequestLog>
    suspend fun byID(id: Uuid): RequestLog?
    suspend fun byRequestID(requestID: Uuid): RequestLog?
    suspend fun add(request: RequestLogNew): RequestLog?
}