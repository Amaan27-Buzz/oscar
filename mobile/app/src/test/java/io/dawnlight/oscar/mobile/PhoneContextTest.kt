package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.json.JSONArray
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class PhoneContextTest {
    private fun preparation() = JSONObject().put("observed_at_ms", 1_800_000_000_000).put("sources", JSONArray((0 until 8).map {
        JSONObject().put("id", "source-$it").put("epoch", 2).put("sequence", 4)
    }))
    @Test fun eightSourcesUseTwoRequestsIncludingMixedWithdrawals() = runBlocking {
        val requests = mutableListOf<JSONObject>()
        publishPhoneContext({ name, payload ->
            assertEquals("phone_context", name); requests.add(payload)
            if (requests.size == 1) preparation() else JSONObject().put("accepted", true)
        }, { 1000L }, { true }) { source ->
            if (source.getString("id") == "source-7") null else JSONObject().put("media_available", true)
        }
        assertEquals(2, requests.size)
        assertEquals(0, requests[0].length())
        val batch = requests[1].getJSONArray("batch")
        assertEquals(8, batch.length())
        assertEquals(4, batch.getJSONObject(0).getInt("sequence"))
        assertEquals("source-7", batch.getJSONObject(7).getString("withdraw"))
    }
    @Test fun uncertainBatchIsNotReplayedAndPrivacyChangePreventsSubmission() = runBlocking {
        var requests = 0
        try {
            publishPhoneContext({ _, _ ->
                requests++
                if (requests == 1) preparation() else throw SecurityException("unknown outcome")
            }, { 1000L }, { true }) { JSONObject() }
            fail("Uncertain submission must escape")
        } catch (_: SecurityException) { assertEquals(2, requests) }
        requests = 0
        var allowed = true
        publishPhoneContext({ _, _ -> requests++; preparation() }, { 1000L }, { allowed }) {
            allowed = false; JSONObject()
        }
        assertEquals(1, requests)
    }
    @Test fun nativeSteadyStateLeavesRequestHeadroomWithEightSourcesAndOverlay() {
        val polls = 60_000 / NATIVE_WORKER_POLL_MS
        val phone = 2 * (60_000 / PHONE_CONTEXT_PUBLISH_MS)
        val snapshots = 60_000 / reconnectDelay(0, 0)
        val overlay = 60_000 / 5000
        // Initial advertisement is included; unchanged capabilities are not re-advertised.
        assertEquals(79L, 1 + polls + phone + snapshots + overlay)
        assertTrue(1 + polls + phone + snapshots + overlay <= 90)
    }
    @Test fun sourceReviewPinsCurrentSessionSelectedPackagesAndSeparateRetention() {
        val source = phoneSourceValue("selected-phone", "a".repeat(32), "phone-source", listOf("example.selected"), false)!!
        assertEquals("phone:selected-phone", source.getString("entity_id"))
        assertEquals("a".repeat(32), source.getString("session_id"))
        assertEquals(5, source.getInt("interval_seconds"))
        assertFalse(source.getBoolean("retain"))
        assertFalse(source.has("act"))
        assertNull(phoneSourceValue("phone", "session", "source", emptyList(), false))
        assertNull(phoneSourceValue("phone", "session", "source", List(9) { "example.app$it" }, false))
        assertNull(phoneSourceValue("phone", "session", "source", listOf("example.selected", "example.selected"), false))
        assertNull(phoneSourceValue("phone", "session", "source", listOf("https://example.app"), false))
    }
    @Test fun observationsKeepExactEpochSequenceAndAuthoritativeTime() {
        val source = JSONObject().put("id", "source").put("epoch", 2).put("sequence", 4)
        val value = JSONObject().put("notifications_available", false).put("media_available", true)
        val payload = phoneContextPayload(source, value, 1_800_000_000_000)
        assertEquals(2, payload.getInt("epoch"))
        assertEquals(4, payload.getInt("sequence"))
        assertEquals(1_800_000_000_000, payload.getLong("observed_at_ms"))
        assertFalse(payload.has("retain"))
        assertThrows(Exception::class.java) { phoneContextPayload(source.put("sequence", 0), value, 1) }
    }
}
