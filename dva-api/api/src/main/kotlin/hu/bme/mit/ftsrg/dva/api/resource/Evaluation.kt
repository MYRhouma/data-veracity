package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Suppress("unused")
@Resource("/evaluate")
class Evaluation {

    @Resource(path = "from-template")
    class FromTemplate(val parent: Evaluation = Evaluation())
}