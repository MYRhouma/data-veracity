package hu.bme.mit.ftsrg.dva.api.rabbit

import com.rabbitmq.client.Connection
import com.rabbitmq.client.ConnectionFactory
import org.slf4j.Logger
import java.lang.Thread.sleep
import java.net.ConnectException

fun ConnectionFactory.connectWithRetry(
    maxRetries: Int = Int.MAX_VALUE,
    initialDelay: Long = 1000,
    maxDelay: Long = 60000,
    backoffMultiplier: Double = 2.0,
    logger: Logger? = null
): Connection {
    var attempt = 0
    var currentDelay: Long = initialDelay

    while (attempt < maxRetries) {
        try {
            logger?.debug("Connecting to RabbitMQ at $host; attempt $attempt")
            return newConnection()
        } catch (e: ConnectException) {
            logger?.error("Connection attempt failed: ${e.message}", e)
            attempt++

            if (attempt >= maxRetries) {
                throw RuntimeException("Unable to connect to RabbitMQ at $host after $maxRetries attempts", e)
            }

            logger?.debug("Retrying in $currentDelay ms")
            try {
                sleep(currentDelay)
            } catch (ie: InterruptedException) {
                Thread.currentThread().interrupt()
                throw RuntimeException("Connection attempts interrupted", ie)
            }

            currentDelay = minOf((currentDelay * backoffMultiplier).toLong(), maxDelay)
        }
    }

    throw RuntimeException("Unable to connect to RabbitMQ at $host after $maxRetries attempts")
}