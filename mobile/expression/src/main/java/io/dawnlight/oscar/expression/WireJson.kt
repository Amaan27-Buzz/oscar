package io.dawnlight.oscar.expression

import org.json.JSONObject
import org.json.JSONTokener

/** Strict bounded object syntax for this contract; Android/JVM JSONObject parsers are lenient. */
internal class WireJson(private val input: String) {
    private var at = 0
    private val string = Regex("\"(?:[^\"\\\\\\x00-\\x1f]|\\\\(?:[\"\\\\/bfnrt]|u[0-9a-fA-F]{4}))*\"")
    private val number = Regex("-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
    private fun whitespace() { while (at < input.length && input[at] in " \t\r\n") at++ }
    private fun character(value: Char): Boolean { whitespace(); if (at >= input.length || input[at] != value) return false; at++; return true }
    private fun token(pattern: Regex): String {
        whitespace(); val match = pattern.find(input, at) ?: error("Invalid JSON token")
        require(match.range.first == at); at = match.range.last + 1; return match.value
    }
    private fun objectValue(depth: Int): Map<String, Any?> {
        require(depth <= 2 && character('{'))
        val values = linkedMapOf<String, Any?>(); if (character('}')) return values
        while (true) {
            val key = JSONTokener(token(string)).nextValue() as String
            require(character(':')); whitespace(); require(at < input.length)
            val value: Any? = when (input[at]) {
                '{' -> objectValue(depth + 1)
                '"' -> JSONTokener(token(string)).nextValue()
                't' -> { require(input.startsWith("true", at)); at += 4; true }
                'f' -> { require(input.startsWith("false", at)); at += 5; false }
                'n' -> { require(input.startsWith("null", at)); at += 4; JSONObject.NULL }
                else -> JSONTokener(token(number)).nextValue()
            }
            // Match JSON.parse's last-key behavior consistently on Android and the JVM.
            values[key] = value
            if (character('}')) return values
            require(character(','))
        }
    }
    fun decode(): JSONObject {
        val values = objectValue(1); whitespace(); require(at == input.length)
        return JSONObject(values)
    }
}
