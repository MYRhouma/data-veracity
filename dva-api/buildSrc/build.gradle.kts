import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    // Support convention plugins written in Kotlin.
    // Convention plugins are build scripts in 'src/main' that automatically become available as plugins in the main build.
    `kotlin-dsl`
}

repositories {
    // Use the plugin portal to apply community plugins in convention plugins.
    gradlePluginPortal()
}

dependencies {
    implementation(libs.dependency.license.report.gradle.plugin)
    implementation(libs.kotlin.gradle.plugin)
    implementation(libs.kover.gradle.plugin)
    implementation(libs.shadow.gradle.plugin)
}

kotlin {
    compilerOptions {
        jvmTarget = JvmTarget.JVM_17
    }
}
