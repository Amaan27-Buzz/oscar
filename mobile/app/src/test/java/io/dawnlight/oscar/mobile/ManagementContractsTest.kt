package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.util.Base64

class ManagementContractsTest {
    @Test fun delegatedConversationRequiresExactFullAccessReadback() {
        fun response() = JSONObject().put("id", "goal").put("mode", "full").put("state", "enabled")
        assertEquals("goal", parseStartedResponsibility(response()))
        listOf(response().put("mode", "ask"), response().put("state", "verified"),
            response().put("hidden", true), response().put("id", "bad\nidentity"),
            response().put("id", "x".repeat(81))).forEach {
            assertThrows(Exception::class.java) { parseStartedResponsibility(it) }
        }
    }
    @org.junit.Test fun weatherReviewPinsExplicitCoordinatesWithoutDeviceLocation() {
        val value = weatherSourceValue("weather-oslo", "Oslo", "59.9139", "10.7522", false)!!
        org.junit.Assert.assertEquals("weather:weather-oslo", value.getString("entity_id"))
        org.junit.Assert.assertEquals(600, value.getInt("interval_seconds"))
        org.junit.Assert.assertEquals(59.9139, value.getDouble("latitude"), 0.0)
        org.junit.Assert.assertFalse(value.getBoolean("retain"))
        org.junit.Assert.assertFalse(value.has("device_location"))
        listOf("NaN", "91", "59.91391", "https://example.com").forEach {
            org.junit.Assert.assertNull(weatherSourceValue("weather-oslo", "Oslo", it, "10.7522", false))
        }
        org.junit.Assert.assertNull(weatherSourceValue("weather-oslo", "Oslo\n", "59", "10", false))
    }

    @Test fun planningRequiresExplicitPrivacyAndFiniteScopeBeforeSignedReview() {
        val model = ManagedCapability("models.reason", "core", "session", "model_reasoning", "model", listOf("models"))
        val action = ManagedCapability("math.add", "core", "session", "addition", "low", listOf("math"))
        val request = planningRoutine("Planner", "Calculate a sum", "private", listOf(model, action))
        assertEquals("plan_draft", request.getString("operation"))
        assertEquals("private", request.getJSONObject("value").getString("mode"))
        assertEquals(2, request.getJSONObject("value").getJSONArray("capabilities").length())
        assertFalse(request.getJSONObject("value").has("context"))
        assertThrows(Exception::class.java) { planningRoutine("Planner", "Goal", "auto", listOf(action)) }
        assertThrows(Exception::class.java) { planningRoutine("Planner", "Goal", "public", listOf(model, action)) }
        val malformed = management().put("planner_drafts", JSONArray().put(JSONObject().put("id", "draft").put("goal", "Goal")))
        assertThrows(Exception::class.java) { parseManagement(malformed) }
        val approval = Approval.management(challenge("assistance", request), "assistance", request, snapshot().managementStamp(), 1000)
        assertEquals("assistance_complete", approval.completion)
    }

    private fun management() = JSONObject("""{"version":1,"relationship_id":"owner","core_node_id":"core","truncated":false,"observed_at_ms":1000,
        "authority":{"mode":"ask","status":"inactive","epoch":0},"ask_rules":["existing-ask"],
        "capabilities":[{"id":"files.write","node_id":"desktop","session_id":"session","input_kind":"file_write","risk":"high","permissions":["files:write"]}],
        "sentry":{"mode":"manual","state":"sleep","source_ids":[],"trigger_keys":[],"allow_interrupt":false,"generation":1,"sources":[]}}""")
    private fun connections() = JSONObject("""{"identity":{"display_name":"OSCAR"},"accounts":[],"plugins":[],"providers":[],"truncated":false,"observed_at_ms":1000}""")
    private fun snapshot() = CoreSnapshot(emptyList(), emptyList(), 1000, management = parseManagement(management()), connections = parseConnections(connections()))
    private fun challenge(family: String, change: JSONObject): JSONObject {
        val material = JSONObject().put("task_id", "new").put("target", "OSCAR change").put("change", change).put("digest", "a".repeat(64))
        if (family == "authority") material.put("relationship", "new").put("epoch", 0)
        if (family == "assistance") material.put("review", JSONObject().put("change", change).put("current", JSONObject().put("steps", JSONArray())))
        val review = canonicalJson(when (family) { "authority" -> material; "assistance" -> material.getJSONObject("review"); else -> change })
        val claim = JSONObject().put("version", 2).put("node_id", "mobile").put("session_id", "session").put("operation", "approve")
            .put("scope", "grid:approve").put("generation", 0).put("material", material).put("nonce", "b".repeat(32)).put("expires_at_ms", 20_000)
            .put("display_digest", Approval.displayDigest("approve", "grid:approve", "OSCAR change", review, "Review exact change"))
        return JSONObject().put("challenge_id", "review").put("signing_payload", Base64.getEncoder().encodeToString(claim.toString().toByteArray()))
            .put("operation", "approve").put("scope", "grid:approve").put("generation", 0).put("expires_at_ms", 20_000).put("target", "OSCAR change")
            .put("review", review).put("exact_request", "Review exact change").put("description", "Review exact change")
            .put("capability", when (family) { "authority" -> "authority.manage"; "assistance" -> "assistance.manage"; else -> "connections.manage" })
            .put("reason", "Owner review").put("consequence", "Exact change only").put("policy_reason", "Rechecked")
    }
    @Test fun signedManagementIsPinnedToProposalRouteAndCurrentReadback() {
        val snapshot = snapshot(); val change = change("pause", "goal")
        val approval = Approval.management(challenge("assistance", change), "assistance", change, snapshot.managementStamp(), 1000)
        assertEquals("assistance_complete", approval.completion)
        val state = MobileState(link = Link.CONNECTED, snapshot = snapshot, observedAt = 1000, approval = approval)
        assertTrue(approval.current(state, 1001))
        assertFalse(approval.current(state.copy(privateSuppressed = true), 1001))
        assertFalse(approval.current(state.unavailable("Disconnected"), 1001))
        val changed = snapshot.copy(management = parseManagement(management().apply { getJSONObject("authority").put("epoch", 1) }))
        assertFalse(approval.current(state.copy(snapshot = changed), 1001))
        assertFalse(approval.current(state, 20_000))
        assertThrows(Exception::class.java) { Approval.management(challenge("assistance", change), "management", change, snapshot.managementStamp(), 1000) }
        assertThrows(Exception::class.java) { Approval.management(challenge("assistance", change), "assistance", change("delete", "goal"), snapshot.managementStamp(), 1000) }
    }
    @Test fun changedDisplayOrConfirmationCannotBeSigned() {
        val change = change("pause", "goal"); val json = challenge("assistance", change)
        assertThrows(Exception::class.java) { Approval.management(JSONObject(json.toString()).put("review", "{}"), "assistance", change, "stamp", 1000) }
        assertThrows(Exception::class.java) { Approval.management(JSONObject(json.toString()).put("exact_request", "Another change"), "assistance", change, "stamp", 1000) }
        assertThrows(Exception::class.java) { Approval.management(JSONObject(json.toString()).put("confirmation", "none"), "assistance", change, "stamp", 1000) }
        val hidden = JSONObject(json.toString()).put("review", canonicalJson(change))
        assertThrows(Exception::class.java) { Approval.management(hidden, "assistance", change, "stamp", 1000) }
        assertThrows(Exception::class.java) { Approval.management(json, "assistance", change, "stamp", 20_000) }
    }
    @Test fun delegationUsesExactSessionCoverageAndExplicitAskResolution() {
        val view = parseManagement(management())!!; val connections = parseConnections(connections())
        val full = delegationRequest(view, connections, "full", 900)
        assertEquals("session", full.getJSONArray("capabilities").getJSONObject(0).getString("session_id"))
        assertEquals(listOf("existing-ask"), full.getJSONArray("resolve_ask_rules").texts(256))
        assertEquals(0, delegationRequest(view, connections, "secure", 900).getJSONArray("resolve_ask_rules").length())
        val approval = Approval.management(challenge("authority", full), "authority", full, snapshot().managementStamp(), 1000)
        assertEquals("authority_complete", approval.completion)
        assertThrows(Exception::class.java) { delegationRequest(view, connections.copy(truncated = true), "full", 900) }
        assertThrows(Exception::class.java) { delegationRequest(view, connections, "full", 0) }
    }
    @Test fun routineAuthoringPinsRealFileExecutorAndBoundedSchedule() {
        val cap = parseManagement(management())!!.capabilities.single()
        val schedule = routineSchedule("", "60", "3")
        val routine = fileRoutine("Daily brief", "Write brief", "brief.txt", "Exact contents", cap, schedule)
        val step = routine.getJSONObject("value").getJSONArray("steps").getJSONObject(0)
        assertEquals("desktop", step.getString("node_id")); assertEquals("files.write", step.getString("capability_id"))
        assertEquals("Exact contents", step.getJSONObject("intent").getString("content"))
        assertEquals(3, routine.getJSONObject("value").getInt("max_runs"))
        assertThrows(Exception::class.java) { routineSchedule("", "59", "2") }
        assertThrows(Exception::class.java) { routineSchedule("", "", "2") }
        assertThrows(Exception::class.java) { routineSchedule("not a date", "", "1") }
        assertThrows(Exception::class.java) { fileRoutine("name", "goal", "file", "x", cap.copy(kind = "file_read"), schedule) }
    }
    @Test fun projectionsArePrivateAndFreshObservationDoesNotInvalidateUnchangedReview() {
        val snapshot = snapshot()
        val refreshed = snapshot.copy(management = parseManagement(management().put("observed_at_ms", 2000)), connections = parseConnections(connections().put("observed_at_ms", 2000)))
        assertEquals(snapshot.managementStamp(), refreshed.managementStamp())
        assertNull(snapshot.withoutPrivate().management); assertNull(snapshot.withoutPrivate().connections)
        assertNull(parseManagement(management().put("truncated", true)))
        assertThrows(Exception::class.java) { parseManagement(management().apply { getJSONObject("authority").put("mode", "full") }) }
        val executive = JSONObject().put("version", 1).put("goals", JSONArray()).put("management", management())
        val wire = JSONObject().put("version", 2).put("core_id", "core").put("node_id", "mobile").put("relationship_id", "owner")
            .put("observed_at_ms", 1000).put("tasks", JSONArray()).put("nodes", JSONArray()).put("executive", executive).put("connections", connections())
        assertEquals("ask", parseGridSnapshot(wire, "core", "mobile").management!!.mode)
        assertNotNull(parseGridSnapshot(wire, "core", "mobile").connections)
    }
    @Test fun dayBriefIsBoundedAndWithdrawnOnConnectionLoss() {
        val wire = JSONObject().put("version", 1).put("observed_at", 1000).put("truncated", false)
            .put("sources", JSONArray().put(JSONObject().put("id", "clock").put("epoch", 1).put("adapter", "time").put("state", "current")
                .put("epistemic", "KNOWN").put("value", "{\"datetime\":\"2026-10-21T10:00:00Z\"}")
                .put("evidence", JSONArray().put(JSONObject().put("id", "source-evidence").put("fresh_until", 1060)))))
            .put("schedule", JSONObject().put("overlaps", JSONArray()).put("incomplete", false).put("truncated", false))
        val brief = parseDayBrief(wire)
        assertEquals(1060.0, brief.sources.single().freshUntil!!, 0.0)
        assertNull(MobileState(dayBrief = brief).unavailable("Disconnected").dayBrief)
        assertThrows(Exception::class.java) { parseDayBrief(JSONObject(wire.toString()).put("observed_at", -1)) }
        assertThrows(Exception::class.java) { parseDayBrief(JSONObject(wire.toString()).put("sources", JSONArray((0..8).map { wire.getJSONArray("sources").getJSONObject(0) }))) }
    }
}
