package hu.bme.mit.ftsrg.dva.api

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class EvaluationResultDTO(
    val engine: String? = null,
    val timestamp: String,
    val success: Boolean,
    val details: String? = null,
    val error: String? = null,
)

@Serializable
data class AoVResponseDTO(
    val requestId: String,
    val issuerDidKey: String? = null,
    val jws: String? = null,
    val vcId: String? = null,
    val evaluationPassing: Boolean,
    val evaluationResults: List<EvaluationResultDTO>,
    val vcIssuedDate: String? = null,
)

@Serializable
data class AttestationVerifySyncRequestDTO(
    val jws: String,
    val attesterDidKey: String,
)

@Serializable
data class AttestationVerifySyncResponseDTO(
    val verified: Boolean,
    val reason: String? = null,
    val payload: JsonObject? = null,
)
