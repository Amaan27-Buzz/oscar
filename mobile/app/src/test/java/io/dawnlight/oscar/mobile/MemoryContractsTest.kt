package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MemoryContractsTest {
    private fun memory() = JSONObject().put("available", true).put("generation", 3).put("truncated", false)
        .put("records", JSONArray().put(JSONObject().put("id", "synthetic-memory").put("content", "The project is named Copper")
            .put("digest", "a".repeat(64)).put("kind", "episodic").put("status", "REPORTED")
            .put("source_event_ids", JSONArray().put("source")).put("excerpt", false).put("can_manage", true).put("can_correct", false)))
    @Test fun boundedMemoryProjectionRetainsSeparateReadManageAndRetentionStates() {
        val parsed = parseMemory(memory())
        assertTrue(parsed.available)
        assertTrue(parsed.records.single().canManage)
        assertFalse(parsed.records.single().canCorrect)
        assertEquals(1, parsed.records.single().sources)
        assertFalse(parseMemory(JSONObject().put("available", false).put("records", JSONArray()).put("truncated", false)).available)
    }
    @Test fun malformedOrUnavailableMemoryNeverExposesRecords() {
        assertThrows(Exception::class.java) { parseMemory(memory().put("available", false)) }
        assertThrows(Exception::class.java) { parseMemory(memory().put("generation", -1)) }
        val malformed = memory(); malformed.getJSONArray("records").getJSONObject(0).put("digest", "not-a-digest")
        assertThrows(Exception::class.java) { parseMemory(malformed) }
        val duplicate = memory(); duplicate.getJSONArray("records").put(duplicate.getJSONArray("records").getJSONObject(0))
        assertThrows(Exception::class.java) { parseMemory(duplicate) }
    }
}
