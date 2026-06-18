package hu.bme.mit.ftsrg.dva.log

import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class)
interface VerifRequestLogRepo {
    suspend fun all(): List<VerifRequestLog>
    suspend fun byID(id: Uuid): VerifRequestLog?
    suspend fun add(request: VerifRequestLogNew): VerifRequestLog?
    suspend fun update(patch: VerifRequestLogPatch): VerifRequestLog?
}