package io.dawnlight.oscar.mobile

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.sp
import org.commonmark.node.*
import org.commonmark.parser.Parser
import org.commonmark.ext.gfm.tables.*
import org.commonmark.ext.gfm.strikethrough.*
import org.json.JSONArray
import org.json.JSONObject
import org.json.JSONTokener

private val responseParser = Parser.builder().extensions(listOf(TablesExtension.create(), StrikethroughExtension.create()))
    .maxOpenBlockParsers(32).build()

/** Native selectable text only: markup cannot execute HTML, fetch images or grant authority. */
@Composable fun ResponseText(source: String, maxLines: Int = Int.MAX_VALUE) {
    val formatted = remember(source) { formattedResponse(source) }
    Text(formatted, style = MaterialTheme.typography.bodyLarge, maxLines = maxLines, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
}

internal fun formattedResponse(source: String): AnnotatedString {
    require(source.length <= 24000) { "Content exceeds the validated presentation boundary" }
    // Valid structured responses are readable fields; exact approval bytes remain separately visible.
    val trimmed = source.trim()
    var nesting = 0
    var maxNesting = 0
    var quoted = false
    var escaped = false
    trimmed.forEach { char ->
        if (escaped) escaped = false
        else if (quoted && char == '\\') escaped = true
        else if (char == '"') quoted = !quoted
        else if (!quoted) {
            if (char == '{' || char == '[') { nesting++; maxNesting = maxOf(maxNesting, nesting) }
            if (char == '}' || char == ']') nesting--
        }
    }
    val structured = try {
        if (maxNesting <= 16 && (trimmed.startsWith("{") || trimmed.startsWith("["))) {
            val tokens = JSONTokener(trimmed)
            tokens.nextValue().takeIf { (it is JSONObject || it is JSONArray) && tokens.nextClean() == '\u0000' }
        } else null
    } catch (_: Exception) { null }
    if (structured is JSONObject && structured.length() == 0) return AnnotatedString("Empty object")
    if (structured is JSONArray && structured.length() == 0) return AnnotatedString("No items")
    if (structured != null) return buildAnnotatedString {
        fun field(value: Any?, depth: Int) {
            if (depth > 16) { append(value.toString()); return }
            when (value) {
                is JSONObject -> value.keys().forEach { key ->
                    append("  ".repeat(depth))
                    withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { append("$key: ") }
                    val child = value.get(key)
                    if (child is JSONObject || child is JSONArray) append('\n')
                    field(child, depth + 1)
                }
                is JSONArray -> for (i in 0 until value.length()) {
                    append("  ".repeat(depth) + "${i + 1}. "); field(value.get(i), depth + 1)
                }
                else -> { append(value.toString()); append('\n') }
            }
        }
        field(structured, 0)
    }.let { it.subSequence(0, it.text.trimEnd().length) }
    val document = try { responseParser.parse(source) } catch (_: IllegalStateException) { return AnnotatedString(source) }
    return buildAnnotatedString {
        val orderedIndices = mutableMapOf<OrderedList, Int>()
        fun render(node: Node, depth: Int = 0) {
            fun children() {
                var child = node.firstChild
                while (child != null) { render(child, depth + 1); child = child.next }
            }
            if (depth > 64) { append("[Nested content omitted]"); return }
            when (node) {
                is org.commonmark.node.Text -> append(node.literal)
                is Heading -> { withStyle(SpanStyle(fontWeight = FontWeight.Bold, fontSize = (if (node.level <= 2) 23 else 19).sp)) { children() }; append("\n\n") }
                is Paragraph -> { children(); append(if (node.parent is ListItem) "\n" else "\n\n") }
                is Emphasis -> withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { children() }
                is StrongEmphasis -> withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { children() }
                is Strikethrough -> withStyle(SpanStyle(textDecoration = TextDecoration.LineThrough)) { children() }
                is Code -> withStyle(SpanStyle(fontFamily = FontFamily.Monospace)) { append(node.literal) }
                is FencedCodeBlock -> { withStyle(SpanStyle(fontFamily = FontFamily.Monospace)) { append(node.literal.trimEnd()) }; append("\n\n") }
                is IndentedCodeBlock -> { withStyle(SpanStyle(fontFamily = FontFamily.Monospace)) { append(node.literal.trimEnd()) }; append("\n\n") }
                is SoftLineBreak, is HardLineBreak -> append('\n')
                is ListItem -> {
                    val parent = node.parent
                    if (parent is OrderedList) {
                        val number = orderedIndices.getOrPut(parent) { parent.markerStartNumber }
                        orderedIndices[parent] = number + 1
                        append("$number. ")
                    } else append("• ")
                    children()
                }
                is BulletList, is OrderedList -> { children(); append('\n') }
                is BlockQuote -> { append("│ "); children() }
                is org.commonmark.node.Link -> { children(); append(" (${node.destination})") }
                is Image -> { append("Image: "); children(); append(" (${node.destination})") }
                is HtmlInline -> append(node.literal)
                is HtmlBlock -> { append(node.literal); append('\n') }
                is ThematicBreak -> append("────────\n\n")
                is TableCell -> { if (node.previous != null) append("   ·   "); children() }
                is TableRow -> { children(); append('\n') }
                is TableHead -> withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { children() }
                else -> children()
            }
        }
        render(document)
    }.let { it.subSequence(0, it.text.trimEnd().length) }
}
