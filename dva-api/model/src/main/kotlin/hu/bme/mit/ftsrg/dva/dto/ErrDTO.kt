package hu.bme.mit.ftsrg.dva.dto

import kotlinx.serialization.Serializable

/**
 * An RFC 7807 problem detail response DTO.
 */
@Serializable
data class ErrDTO(
    var type: String? = null,
    var title: String? = null,
    var detail: String? = null,
    var instance: String? = null
)