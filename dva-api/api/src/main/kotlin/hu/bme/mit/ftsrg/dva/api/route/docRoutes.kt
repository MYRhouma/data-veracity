package hu.bme.mit.ftsrg.dva.api.route

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.html.*
import io.ktor.server.plugins.swagger.*
import io.ktor.server.routing.*
import kotlinx.html.*

fun Application.docRoutes(openapiPath: String) {
    routing {
        get("/") {
            val name = "DVA"
            call.respondHtml(HttpStatusCode.OK) {
                head {
                    title {
                        +name
                    }
                }
                body {
                    h1 {
                        +"Welcome to the $name web UI"
                    }
                    p {
                        +"Click "
                        a(href = "/swagger") {
                            +"here"
                        }
                        +" to see the API documentation and test the service."
                    }
                }
            }
        }
        swaggerUI("swagger", swaggerFile = openapiPath)
    }
}