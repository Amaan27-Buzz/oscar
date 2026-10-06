package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MobileContractsTest {
    private fun task(state: String = "planned", status: String = "online", generation: Int = 0) = JSONObject("""{
        "task_id":"task-1","description":"2 + 3","state":"$state","target":"desktop",
        "node_status":"$status","generation":$generation,"actions":["approve","deny","cancel"],
        "evidence_ids":[],"blocker":""
    }""")
    private fun rejected(block: () -> Unit) {
        try { block(); fail("Invalid remote payload accepted") } catch (_: Exception) { }
    }
    @Test fun invalidPayloadAndUnknownStateFailClosed() {
        rejected { parseTask(task("invented-success")) }
        rejected { parseTask(task().put("generation", "0")) }
        rejected { parseTask(task().put("actions", listOf("power-off"))) }
        rejected { parseTask(task().put("task_id", "x".repeat(81))) }
        rejected { parseTask(task(generation = -1)) }
        rejected { parseTask(task().put("value", "5")) }
        rejected { parseTask(task().put("response", "unverified fixture").put("response_status", "VERIFIED")) }
    }
    @Test fun offlineNodesWithdrawExecutionActions() {
        assertEquals(listOf("deny", "cancel"), parseTask(task(status = "offline")).actions)
        assertEquals("Needs approval", parseTask(task()).label)
        assertEquals("Completed · verified", parseTask(task("verified")).label)
        val snapshot = JSONObject().put("tasks", org.json.JSONArray(listOf(task(status = "offline")))).put("nodes", org.json.JSONArray(listOf(
            JSONObject("""{"id":"desktop","role":"Desktop","status":"offline","paired":true,"capabilities":[{"kind":"addition"}]}"""))))
            .put("observed_at_ms", 1L)
        assertTrue(parseSnapshot(snapshot).nodes.first().capabilities.isEmpty())
    }
    @Test fun staleGenerationAndRestartCannotRestoreAuthority() {
        val disconnected = MobileState(epoch = 4)
        val stale = MobileState(epoch = 3, link = Link.CONNECTED, busy = true)
        assertEquals(disconnected, disconnected.fenced(stale, 3))
        val failed = stale.unavailable("No action confirmed")
        assertNull(failed.snapshot); assertNull(failed.approval); assertFalse(failed.busy)
        assertEquals(Presence.UNAVAILABLE, MobileState().presence)
        assertEquals(Presence.ERROR, failed.presence)
    }
    @Test fun orbReflectsCurrentStateOnly() {
        assertEquals(Presence.ATTENTIVE, MobileState(link = Link.CONNECTED).presence)
        assertEquals(Presence.THINKING, MobileState(link = Link.CONNECTED, busy = true).presence)
        val snapshot = CoreSnapshot(listOf(parseTask(task())), emptyList(), 1)
        assertEquals(Presence.WAITING, MobileState(link = Link.CONNECTED, snapshot = snapshot).presence)
        assertEquals(9, Presence.entries.size)
    }
    @Test fun endpointRejectsCredentialsRedirectPathsAndInsecureRemote() {
        listOf("http://example.com", "https://owner@example.com", "https://example.com/path", "https://example.com?token=test", "https://example.com/").forEach {
            try { CoreClient.validateEndpoint(it); fail("Unsafe origin accepted") } catch (_: SecurityException) { }
        }
        CoreClient.validateEndpoint("https://example.com")
        CoreClient.validateEndpoint("http://127.0.0.1:8000")
    }
    @Test fun approvalDisplayAndDeliveryStayBoundToSignedMaterial() {
        val material = JSONObject().put("package", "example.source").put("key_hash", "a".repeat(64)).put("text_hash", "b".repeat(64))
        val claim = JSONObject().put("version", 1).put("operation", "reply").put("expires_at_ms", 1000L).put("material", material)
        val encoded = java.util.Base64.getEncoder().encodeToString(claim.toString().toByteArray())
        val json = JSONObject().put("challenge_id", "challenge").put("signing_payload", encoded).put("expires_at_ms", 1000L)
            .put("operation", "reply").put("description", "Neutral fixture reply").put("target", "example.source")
            .put("capability", "notification.reply").put("reason", "Owner request").put("consequence", "Source handoff")
            .put("policy_reason", "Policy rechecked").put("confirmation", "biometric_or_device_credential")
        val approval = Approval.parse(json)
        val permit = JSONObject(material.toString()).put("id", "challenge")
        assertTrue(approval.acceptsPermit(permit))
        assertFalse(approval.acceptsPermit(permit.put("package", "another.source")))
        rejected { Approval.parse(json.put("target", "another.source")) }
    }
}
