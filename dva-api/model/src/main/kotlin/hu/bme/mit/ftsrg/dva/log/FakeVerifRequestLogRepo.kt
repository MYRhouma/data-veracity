package hu.bme.mit.ftsrg.dva.log

import kotlin.time.ExperimentalTime
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@OptIn(ExperimentalUuidApi::class, ExperimentalTime::class)
class FakeVerifRequestLogRepo : VerifRequestLogRepo {
    private val requests = mutableMapOf<Uuid, VerifRequestLog>()

    override suspend fun all(): List<VerifRequestLog> = requests.values.toList()

    override suspend fun byID(id: Uuid): VerifRequestLog? = requests[id]

    override suspend fun add(request: VerifRequestLogNew): VerifRequestLog? {
        val entity = VerifRequestLog(
            id = Uuid.random(),
            exchangeID = request.exchangeID,
            contractID = request.contractID,
            attesterAgentURL = request.attesterAgentURL,
            attesterAgentLabel = request.attesterAgentLabel,
            receivedDate = request.receivedDate,
        )
        requests.put(entity.id, entity)
        return entity
    }

    override suspend fun update(patch: VerifRequestLogPatch): VerifRequestLog? {
        val existingRequest = requests[patch.id] ?: return null
        val updatedRequest = VerifRequestLog(
            id = existingRequest.id,
            exchangeID = existingRequest.exchangeID,
            contractID = existingRequest.contractID,
            attesterAgentURL = existingRequest.attesterAgentURL,
            attesterAgentLabel = existingRequest.attesterAgentLabel,
            receivedDate = existingRequest.receivedDate,
            verificationDate = patch.verificationDate ?: existingRequest.verificationDate,
            verified = patch.verified ?: existingRequest.verified,
            presentationRequestData = patch.presentationRequestData ?: existingRequest.presentationRequestData,
        )
        requests.put(updatedRequest.id, updatedRequest)
        return updatedRequest
    }
}