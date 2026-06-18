package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*
import kotlin.uuid.ExperimentalUuidApi
import kotlin.uuid.Uuid

@Suppress("unused")
@Resource("/template")
class Templates {

    @OptIn(ExperimentalUuidApi::class)
    @Resource("{id}")
    class Id(val parent: Templates = Templates(), val id: Uuid) {

        @Resource("render")
        class Render(val parent: Id)
    }
}