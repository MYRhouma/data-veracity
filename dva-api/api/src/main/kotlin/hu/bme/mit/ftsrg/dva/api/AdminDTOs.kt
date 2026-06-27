package hu.bme.mit.ftsrg.dva.api

import hu.bme.mit.ftsrg.dva.jws.WhitelistEntry
import kotlinx.serialization.Serializable

@Serializable
data class WhitelistAddRequestDTO(val didKey: String, val label: String? = null)

@Serializable
data class WhitelistEntryDTO(val didKey: String, val label: String? = null) {
  companion object {
    fun from(entry: WhitelistEntry): WhitelistEntryDTO = WhitelistEntryDTO(entry.didKey, entry.label)
  }
}

@Serializable
data class IssuerDidKeyDTO(val issuerDidKey: String)