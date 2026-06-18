plugins {
    // Apply common conventions for JVM-based languages
    id("buildlogic.jvmbased-common-conventions")

    // Apply the org.jetbrains.kotlin.jvm plugin to add support for Kotlin.
    id("org.jetbrains.kotlin.jvm")

    // Apply the Kover plugin for coverage metrics
    id("org.jetbrains.kotlinx.kover")
}