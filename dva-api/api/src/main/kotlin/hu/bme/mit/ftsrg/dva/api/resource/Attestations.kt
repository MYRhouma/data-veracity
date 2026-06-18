package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Suppress("unused")
@Resource("/attestation")
class Attestations {

    @Resource("verify")
    class Verify(val parent: Attestations = Attestations())

    @Resource("{id}/status")
    class Status(val id: String, val parent: Attestations = Attestations())
}