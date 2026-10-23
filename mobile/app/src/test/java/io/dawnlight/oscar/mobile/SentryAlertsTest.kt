package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SentryAlertsTest {
    private fun management(change: (JSONObject) -> Unit = {}): ManagementView {
        val sentry = JSONObject("""{"mode":"sentry","state":"aware","allow_interrupt":true,"generation":1,
            "source_ids":["selected"],"trigger_keys":["status"],"sources":[{"id":"selected","epoch":1,"perceive":true,"act":true}],
            "alerts":[{"id":"${"a".repeat(64)}","source_id":"selected","source_epoch":1,"generation":1,"observation_id":"observation:1","key":"status","fresh_until":110.0,"simulated":true,"policy_ids":["delivery"]}]}""")
        change(sentry)
        return ManagementView("owner", "ask", "inactive", null, 0, emptyList(), emptyList(), JSONObject().put("sentry", sentry).toString())
    }
    @Test fun boundedMetadataRechecksLocalFreshnessAndCurrentSourceGrant() {
        assertEquals("selected", parseSentryAlerts(management(), 100_000).single().source)
        assertTrue(parseSentryAlerts(management(), 110_000).isEmpty())
        listOf<(JSONObject) -> Unit>(
            { it.put("generation", 2) }, { it.put("state", "sleep") },
            { it.getJSONArray("sources").getJSONObject(0).put("act", false) },
            { it.getJSONArray("alerts").getJSONObject(0).put("source_epoch", 2) }
        ).forEach { assertTrue(parseSentryAlerts(management(it), 100_000).isEmpty()) }
        assertThrows(Exception::class.java) { parseSentryAlerts(management { it.getJSONArray("alerts").getJSONObject(0).put("id", "unbounded-wire-id") }, 100_000) }
        assertTrue(parseSentryAlerts(null, 100_000).isEmpty())
    }
}
