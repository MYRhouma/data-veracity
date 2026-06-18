@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.dto.aov

import hu.bme.mit.ftsrg.serialization.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL

@Serializable
data class ACAPyPresentationRequestDTO(val dataExchangeId: String, val attesterAgentURL: URL, val attesterLabel: String)
