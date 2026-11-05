package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ModelChoicesTest {
    private fun source() = JSONObject().put("selected", "google::current").put("available", JSONArray(listOf("google::other"))).put("free_only", true)
    @Test fun preservesUnavailableSelectionAndCurrentFreePolicy() {
        val models = parseModels(source())
        assertEquals("google::current", models.selected)
        assertEquals(listOf("google::other"), models.available)
        assertTrue(models.freeOnly)
        assertEquals("", parseModels(source().put("selected", "")).selected)
    }
    @Test fun rejectsMalformedAndUnboundedCoreChoices() {
        for (bad in listOf(source().put("free_only", "true"), source().put("available", JSONArray(listOf(12))),
            source().put("available", JSONArray(listOf("same", "same"))), source().put("available", JSONArray((0..100).map { "model-$it" })))) {
            try { parseModels(bad); fail("Malformed model projection accepted") } catch (_: IllegalArgumentException) { }
        }
    }
}
