package io.dawnlight.oscar.mobile

import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import org.junit.Assert.*
import org.junit.Test

class ResponseTextTest {
    @Test fun markdownStylesPreserveContentAndCode() {
        val rich = formattedResponse("# Plan\n\n**Focus** with *care*.\n\n- One\n- Two\n\n```json\n{\"count\":2}\n```\n\n[Source](https://example.com)\n\n| Day | Work |\n| --- | --- |\n| Mon | Read |")
        assertTrue(rich.text.startsWith("Plan\n\nFocus with care."))
        assertTrue(rich.text.contains("• One\n• Two"))
        assertTrue(rich.text.contains("{\"count\":2}"))
        assertTrue(rich.text.contains("Source (https://example.com)"))
        assertTrue(rich.text.contains("Day   ·   Work"))
        assertFalse(rich.text.contains("**"))
        assertTrue(rich.spanStyles.any { it.item.fontWeight == FontWeight.Bold })
        assertTrue(rich.spanStyles.any { it.item.fontFamily == FontFamily.Monospace })
    }
    @Test fun structuredContentIsReadableWithoutDroppingTrailingMaterial() {
        val fields = formattedResponse("{\"status\":\"reported\",\"items\":[\"One\",\"Two\"]}").text
        assertTrue(fields.contains("status: reported"))
        assertTrue(fields.contains("1. One"))
        assertFalse(fields.contains("{"))
        assertTrue(formattedResponse("{\"status\":\"reported\"}\nDo not omit this").text.contains("Do not omit this"))
    }
    @Test fun untrustedMarkupAndDeepInputsNeverExecuteOrDisappear() {
        val source = "<script>alert(1)</script>\n\n![Remote](https://example.com/pixel)\n\n[Unsafe](javascript:alert)"
        val text = formattedResponse(source).text
        assertTrue(text.contains("<script>"))
        assertTrue(text.contains("https://example.com/pixel"))
        assertTrue(text.contains("javascript:alert"))
        val deep = "[".repeat(1000) + "0" + "]".repeat(1000)
        assertTrue(formattedResponse(deep).text.contains("0"))
        assertEquals("Plain text", formattedResponse("Plain text").text)
    }
}
