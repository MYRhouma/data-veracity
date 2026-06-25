package hu.bme.mit.ftsrg.dva.jws

/** Point of injection for the did:key whitelist backed by the connector's DVA instance. */
interface WhitelistRepo {
  suspend fun all(): List<WhitelistEntry>
  suspend fun add(didKey: String, label: String?): WhitelistEntry
  suspend fun remove(didKey: String): Boolean
  suspend fun contains(didKey: String): Boolean
}

data class WhitelistEntry(val didKey: String, val label: String?)