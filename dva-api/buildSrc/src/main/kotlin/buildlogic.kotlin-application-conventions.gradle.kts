plugins {
    // Apply common Kotlin conventions
    id("buildlogic.kotlin-common-conventions")

    // Apply the application plugin to add support for building a CLI application in Java.
    application

    // Apply support for shadow JARs
    id("com.gradleup.shadow")
}