package hu.bme.mit.ftsrg.dva.api

import kotlinx.serialization.Serializable

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
    val jws: String? = null,
    val evaluationPassing: Boolean,
    val evaluationResults: List<EvaluationResultDTO>,
)

@Serializable
data class AttestationVerifySyncRequestDTO(
    val jws: String,
)

@Serializable
data class AttestationVerifySyncResponseDTO(
    val verified: Boolean,
    val reason: String? = null,
)