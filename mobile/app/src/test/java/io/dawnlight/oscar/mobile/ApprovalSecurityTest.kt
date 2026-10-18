package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ApprovalSecurityTest {
    private val now = 100_000L
    private fun challenge(): JSONObject {
        val operation = "approve"; val scope = "control:approve:desktop"; val request = "Exact λ request"; val review = "{\"expression\":\"2 + 3\"}"
        val claim = JSONObject().put("version", 1).put("expires_at_ms", now + 30_000).put("operation", operation).put("scope", scope)
            .put("generation", 0)
            .put("node_id", "mobile").put("session_id", "session").put("nonce", "a".repeat(64))
            .put("material", JSONObject().put("target", "desktop").put("task_id", "task").put("digest", "b".repeat(64)))
            .put("display_digest", Approval.displayDigest(operation, scope, "desktop", review, request))
        return JSONObject().put("challenge_id", "review").put("signing_payload", java.util.Base64.getEncoder().encodeToString(claim.toString().toByteArray()))
            .put("expires_at_ms", now + 30_000).put("operation", operation).put("scope", scope).put("target", "desktop")
            .put("description", "Exact decision").put("capability", "addition").put("reason", "Owner request")
            .put("consequence", "Execute one plan").put("policy_reason", "Rechecked").put("confirmation", "biometric_or_device_credential")
            .put("review", review).put("exact_request", request)
            .put("generation", 0)
    }
    @Test fun displayAudienceExpiryAndActionAreBound() {
        val json = challenge(); val approval = Approval.parse(json, now)
        val task = CoreTask("task", "Exact decision", "planned", "desktop", "online", 0, listOf("approve", "deny"), emptyList(), null, null)
        val state = MobileState(link = Link.CONNECTED, approval = approval, snapshot = CoreSnapshot(listOf(task), emptyList(), now))
        assertTrue(approval.current(state, now)); assertFalse(approval.current(state, now + 30_000))
        assertFalse(approval.current(state.copy(privateSuppressed = true), now))
        assertFalse(approval.current(state.copy(snapshot = CoreSnapshot(listOf(task.copy(actions = emptyList())), emptyList(), now)), now))
        assertFalse(approval.current(state.copy(snapshot = CoreSnapshot(listOf(task.copy(generation = 1)), emptyList(), now)), now))
        for ((field, value) in listOf("review" to "{}", "exact_request" to "Different request", "scope" to "control:approve:other")) {
            try { Approval.parse(JSONObject(json.toString()).put(field, value), now); fail("Changed displayed material accepted") } catch (_: IllegalArgumentException) { }
        }
        try { Approval.parse(json, now + 30_000); fail("Expired accepted") } catch (_: IllegalArgumentException) { }
    }
    @Test fun callerCannotMutateBoundSession() {
        val session = JSONObject().put("url", "https://example.com").put("node_id", "mobile").put("session_id", "session").put("token", "synthetic-only")
        val client = CoreClient(session); val binding = client.binding()
        session.put("node_id", "foreign").put("session_id", "replacement")
        assertEquals(binding, client.binding()); assertTrue(client.matches(Approval.parse(challenge(), now)))
    }
    @Test fun remoteReviewBindsCapabilityAndCurrentPlanDigest() {
        val json = challenge().put("scope", "grid:approve")
        val claim = JSONObject(String(java.util.Base64.getDecoder().decode(json.getString("signing_payload"))))
            .put("version", 2).put("scope", "grid:approve").put("nonce", "a".repeat(32))
            .put("display_digest", Approval.displayDigest("approve", "grid:approve", "desktop", json.getString("review"), json.getString("exact_request")))
        json.put("signing_payload", java.util.Base64.getEncoder().encodeToString(claim.toString().toByteArray()))
        val approval = Approval.parse(json, now)
        val task = CoreTask("task", "Exact decision", "planned", "desktop", "online", 0, listOf("approve"), emptyList(), null, null,
            reviewDigest = "b".repeat(64), capability = "addition")
        val state = MobileState(link = Link.CONNECTED, approval = approval, snapshot = CoreSnapshot(listOf(task), emptyList(), now))
        assertTrue(approval.current(state, now))
        assertFalse(approval.current(state.copy(snapshot = state.snapshot!!.copy(tasks = listOf(task.copy(reviewDigest = "c".repeat(64))))), now))
        assertFalse(approval.current(state.copy(snapshot = state.snapshot!!.copy(tasks = listOf(task.copy(capability = "files.write")))), now))
    }
    @Test fun freshCoreObservationQualifiesClockSkewWithoutExtendingAuthority() {
        val local = now - 1000
        val approval = Approval.parse(challenge(), now)
        val task = CoreTask("task", "Exact decision", "planned", "desktop", "online", 0, listOf("approve"), emptyList(), null, null)
        val state = MobileState(link = Link.CONNECTED, observedAt = local, approval = approval,
            snapshot = CoreSnapshot(listOf(task), emptyList(), now))
        assertEquals(now, state.coreNow(local))
        assertTrue(approval.current(state, local)); assertFalse(approval.current(state, local + 30_000))
        assertEquals(local, MobileState().coreNow(local))
    }
}
