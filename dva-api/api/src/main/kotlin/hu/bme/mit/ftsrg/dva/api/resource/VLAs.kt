package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Suppress("unused")
@Resource("/vla")
class VLAs {

    @OptIn(ExperimentalUuidApi::class)
    @Resource("{id}")
    class Id(val parent: VLAs = VLAs(), val id: Uuid)

    @Resource("from-templates")
    class FromTemplates(val parent: VLAs = VLAs())
}