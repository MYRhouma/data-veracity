package hu.bme.mit.ftsrg.dva.api.db

import io.ktor.server.application.*
import org.jetbrains.exposed.v1.jdbc.Database
import org.jetbrains.exposed.v1.jdbc.SchemaUtils.create
import org.jetbrains.exposed.v1.jdbc.transactions.transaction

fun Application.configureDatabases() {
    val pgURL = environment.config.property("postgres.url").getString()
    val pgUser = environment.config.property("postgres.user").getString()
    val pgPass = environment.config.property("postgres.password").getString()

    Database.connect(
        "jdbc:$pgURL",
        user = pgUser,
        password = pgPass,
    )

    transaction {
        create(TemplatesTable, RequestLogsTable, VerifRequestLogsTable, VLAsTable)
    }
}