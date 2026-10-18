package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec

class GridSyncTest {
    private fun event(id: String, sequence: Long, speaker: String, text: String) = JSONObject()
        .put("event_id", id).put("sequence", sequence).put("turn_id", "turn").put("task_id", "task").put("speaker", speaker).put("text", text)
    private fun sync(reset: Boolean, generation: String, cursor: Long, vararg events: JSONObject) = JSONObject()
        .put("reset", reset).put("archive_generation", generation).put("cursor", cursor).put("events", JSONArray(events.toList()))
    @Test fun canonicalHistoryDeduplicatesResumesAndForgets() {
        val history = GridHistory()
        val owner = event("a", 1, "owner", "Inspect fixture")
        val reply = event("b", 3, "oscar", "Verified readback")
        history.merge(sync(true, "epoch-a", 1, owner))
        assertEquals(1, history.cursor)
        val restored = GridHistory().apply { restore(history.saved()) }
        val interactions = restored.merge(sync(false, "epoch-a", 3, reply))
        assertEquals("Inspect fixture", interactions.single().text)
        assertEquals("Verified readback", interactions.single().response)
        assertEquals(interactions, restored.merge(sync(false, "epoch-a", 3, reply)))
        assertTrue(restored.merge(sync(true, "epoch-b", 5)).isEmpty())
        assertEquals(5, restored.request().getLong("cursor"))
        assertEquals("epoch-b", restored.request().getString("archive_generation"))
    }
    @Test fun historyRejectsConflictingDuplicateOutOfOrderAndStaleCursor() {
        val history = GridHistory()
        history.merge(sync(true, "a", 2, event("a", 2, "owner", "original")))
        listOf(sync(false, "a", 2, event("a", 2, "owner", "changed")),
            sync(false, "a", 1), sync(false, "b", 2),
            sync(false, "a", 4, event("c", 4, "oscar", "later"), event("b", 3, "oscar", "earlier"))).forEach { invalid ->
            try { history.merge(invalid); fail("Invalid canonical history accepted") } catch (_: IllegalArgumentException) { }
        }
    }
    @Test fun existingCanonicalLongHistoryRemainsBoundedAndReadable() {
        val history = GridHistory()
        val canonical = "é".repeat(16500)
        val page = sync(true, "archive", 1, event("legacy", 1, "owner", canonical))
        assertEquals(canonical, history.merge(page).single().text)
        val restored = GridHistory().apply { restore(history.saved()) }
        assertEquals(canonical, restored.interactions().single().text)
        assertTrue(restored.saved().toString().toByteArray().size <= 196608)
    }
    @Test fun deviceProofSignsExactBodyAndSession() {
        val key = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
        val body = "{\"version\":2,\"operation\":\"snapshot\"}".toByteArray()
        val material = CoreClient.signingMaterial("phone", "session", "ab".repeat(16), "123", body)
        val signature = OwnerWire.sign(key.private, material)
        fun valid(bytes: ByteArray): Boolean = Signature.getInstance("RSASSA-PSS").run {
            initVerify(key.public); setParameter(PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, 32, 1)); update(bytes); verify(signature)
        }
        assertTrue(valid(material))
        assertFalse(valid(CoreClient.signingMaterial("phone", "old-session", "ab".repeat(16), "123", body)))
        assertFalse(valid(CoreClient.signingMaterial("phone", "session", "ab".repeat(16), "123", body + 32)))
    }
    @Test fun gridPreservesOnlyFreshCanonicalPresence() {
        val presence = JSONObject("""{"version":1,"visible":true,"expression":{"version":1,"source":{"kind":"core","id":"presence:canonical"},"generation":1,"transitionId":"state","eventTime":100000,"expiresAt":130000,"kind":"state","priority":"normal","operation":"idle","delivery":"composed","availability":"available","muted":false,"attention":"none","reducedMotion":true}}""")
        val snapshot = JSONObject().put("version", 2).put("core_id", "core").put("node_id", "phone").put("relationship_id", "relationship")
            .put("observed_at_ms", 100000).put("nodes", JSONArray()).put("tasks", JSONArray()).put("presence", presence)
        assertEquals(presence.getJSONObject("expression").toString(), parseGridSnapshot(snapshot, "core", "phone").presence)
        snapshot.put("observed_at_ms", 130000)
        try { parseGridSnapshot(snapshot, "core", "phone"); fail("Stale canonical presence accepted") } catch (_: IllegalArgumentException) { }
        snapshot.put("observed_at_ms", 100000)
        presence.getJSONObject("expression").getJSONObject("source").put("kind", "fixture")
        try { parseGridSnapshot(snapshot, "core", "phone"); fail("Non-Core presence accepted") } catch (_: IllegalArgumentException) { }
    }
    @Test fun retryBackoffIsBoundedAndHasJitter() {
        assertEquals(5000, reconnectDelay(0, 0))
        assertEquals(61000, reconnectDelay(100, 5000))
        assertEquals(10500, reconnectDelay(1, 500))
    }
    @Test fun verifiedTaskRequiresIndependentMatchingEvidenceAndReportedResult() {
        val item = JSONObject().put("task_id", "task").put("description", "Read fixture").put("target", "desktop")
            .put("action_id", "action").put("correlation_id", "correlation")
            .put("state", "verified").put("retained_available", true).put("generation", 1).put("approval_required", false).put("review_digest", "ab".repeat(32)).put("capability", "machine.files.read").put("evidence", JSONArray())
            .put("result", JSONObject().put("task_id", "task").put("action_id", "action").put("correlation_id", "correlation").put("status", "REPORTED").put("success", true).put("value", "readback"))
        val nodes = listOf(CoreNode("desktop", "Desktop", "online", true, listOf("File read")))
        try { parseGridTask(item, nodes); fail("Fabricated verification accepted") } catch (_: IllegalArgumentException) { }
        item.put("evidence", JSONArray().put(JSONObject().put("id", "evidence").put("task_id", "task").put("correlation_id", "correlation").put("status", "VERIFIED").put("matches", true)))
        val task = parseGridTask(item, nodes)
        assertEquals("readback", task.value)
        assertTrue(task.actions.isEmpty())
        item.getJSONObject("result").put("value", "")
        assertEquals("", parseGridTask(item, nodes).value)
        val hidden = JSONObject(item.toString()).put("retained_available", false).put("result", JSONObject.NULL).put("evidence", JSONArray())
        assertEquals("unknown", parseGridTask(hidden, nodes).state)
        item.getJSONObject("result").put("task_id", "other-task")
        try { parseGridTask(item, nodes); fail("Cross-task result accepted") } catch (_: IllegalArgumentException) { }
    }
}
