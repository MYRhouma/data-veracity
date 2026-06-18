package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Suppress("unused")
@Resource("/info")
class Info {

    @Resource("requests")
    class Requests(val parent: Info = Info())

    @Resource("presentations")
    class Presentations(val parent: Info = Info())

    @Resource("credentials")
    class Credentials(val parent: Info = Info())
}