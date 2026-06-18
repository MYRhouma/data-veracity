package hu.bme.mit.ftsrg.dva.api.service

import com.github.jknack.handlebars.Handlebars
import hu.bme.mit.ftsrg.dva.vla.Template
import hu.bme.mit.ftsrg.odcs.DataQuality
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonPrimitive

fun Template.render(data: JsonObject): DataQuality? {
    val handlebars = Handlebars()
    val implementationTemplate = handlebars.compileInline(evaluationMethod.implementationTemplate)
    return DataQuality(
        engine = evaluationMethod.engine.toString(),
        implementation = implementationTemplate.apply(data.unquotingToMap())
    )
}

private fun JsonObject.unquotingToMap(): Map<String, String> {
    return toMap().entries.associate { (k, v) ->
        k to when {
            v is JsonPrimitive && v.jsonPrimitive.isString -> v.jsonPrimitive.content.removeSurrounding("\"")
            else -> v.toString()
        }
    }
}