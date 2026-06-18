plugins {
  id("buildlogic.kotlin-library-conventions")
  alias(libs.plugins.kotlin.serialization)
}

dependencies {
  implementation(libs.kotlinx.datetime)
  implementation(libs.kotlinx.serialization.json)
}