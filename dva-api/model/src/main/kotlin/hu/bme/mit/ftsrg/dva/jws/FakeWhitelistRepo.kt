package hu.bme.mit.ftsrg.dva.jws

class FakeWhitelistRepo : WhitelistRepo {
  private val entries = mutableMapOf<String, WhitelistEntry>()

  override suspend fun all(): List<WhitelistEntry> = entries.values.toList()

  override suspend fun add(didKey: String, label: String?): WhitelistEntry {
    val entry = WhitelistEntry(didKey = didKey, label = label)
    entries[didKey] = entry
    return entry
  }

  override suspend fun remove(didKey: String): Boolean {
    return entries.remove(didKey) != null
  }

  override suspend fun contains(didKey: String): Boolean = entries.containsKey(didKey)
}