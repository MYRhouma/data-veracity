@file:UseSerializers(URLSerializer::class)

package hu.bme.mit.ftsrg.dva.dto.aov

import hu.bme.mit.ftsrg.serialization.URLSerializer
import kotlinx.serialization.Serializable
import kotlinx.serialization.UseSerializers
import java.net.URL

@Serializable
data class AttestationVerificationRequestDTO(
    val id: String? = null,
    val exchangeID: String,
    val contractID: String,
    val attesterAgentURL: URL,
    val attesterAgentLabel: String
)
