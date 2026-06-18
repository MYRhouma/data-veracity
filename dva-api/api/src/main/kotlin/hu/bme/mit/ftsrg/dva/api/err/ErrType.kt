package hu.bme.mit.ftsrg.dva.api.err

import hu.bme.mit.ftsrg.dva.dto.ErrDTO
import java.net.URI

enum class ErrType(val uri: URI, val title: String) {
    ALREADY_EXISTS(URI("/errors/exists"), "Resource already exists"),
    NOT_FOUND(URI("/errors/not_found"), "Resource Not Found"),
    UNIMPLEMENTED(URI("/errors/unimplemented"), "Unimplemented feature"),
    UNKNOWN(URI("/errors/unknown"), "Unknown Error"),
}

fun errDTO(type: ErrType, init: ErrDTO.() -> Unit = {}): ErrDTO =
    ErrDTO(type = type.uri.path, title = type.title).apply(init)