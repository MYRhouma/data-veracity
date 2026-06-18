package hu.bme.mit.ftsrg.odcs

import kotlinx.serialization.Serializable

@Serializable
data class DataQuality(val engine: String, val implementation: String)