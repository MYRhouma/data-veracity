package hu.bme.mit.ftsrg.dva.dto.aov

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

@Serializable
data class AttestationRequestDTO(
    val id: String? = null,
    val exchangeID: String,
    val contract: JsonObject,
    val data: JsonElement,
    val attesterID: String,
)