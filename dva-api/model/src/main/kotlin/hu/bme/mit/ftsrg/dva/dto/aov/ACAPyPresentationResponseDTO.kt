package hu.bme.mit.ftsrg.dva.dto.aov

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class ACAPyPresentationResponseDTO(val message: String, val aov: JsonObject)