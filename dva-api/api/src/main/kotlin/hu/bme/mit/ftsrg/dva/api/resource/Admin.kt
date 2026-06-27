package hu.bme.mit.ftsrg.dva.api.resource

import io.ktor.resources.*

@Suppress("unused")
@Resource("/admin")
class Admin {

  @Resource("keys")
  class Keys(val parent: Admin = Admin())

  @Resource("whitelist")
  class Whitelist(val parent: Admin = Admin()) {

    @Resource("{didKey}")
    class Entry(val parent: Whitelist = Whitelist(), val didKey: String)
  }
}