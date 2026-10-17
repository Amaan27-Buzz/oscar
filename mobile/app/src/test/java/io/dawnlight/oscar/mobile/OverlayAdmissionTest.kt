package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.util.concurrent.Executors

class OverlayAdmissionTest {
    private fun response(generation: Int = 1, time: Long = 1000) = JSONObject("""{"version":1,"visible":true,"expression":{"version":1,"source":{"kind":"core","id":"presence:canonical"},"generation":$generation,"transitionId":"same-state","eventTime":$time,"expiresAt":${time+30000},"kind":"state","priority":"normal","operation":"idle","delivery":"composed","availability":"available","muted":false,"attention":"none","reducedMotion":true}}""")
    private fun reject(action: () -> Unit) { try { action(); fail("Untrusted overlay admission") } catch (_: IllegalArgumentException) {} catch (_: IllegalStateException) {} }
    @Test fun everyLocalBoundaryMustPassBeforeWindowAdmission() {
        for (flag in 0..3) {
            val values = MutableList(4) { true }; values[flag] = false
            reject { OverlayAdmission().admit(response(), 1000, "pairing", values[0], values[1], values[2], values[3]) }
        }
        reject { OverlayAdmission().admit(response().put("visible", false), 1000, "pairing", true, true, true, true) }
        reject { OverlayAdmission().admit(response().put("visible", "true"), 1000, "pairing", true, true, true, true) }
        reject { OverlayAdmission().admit(response(), 1000, "", true, true, true, true) }
    }
    @Test fun staleMalformedAndWrongSourceNeverBecomeVisible() {
        reject { OverlayAdmission().admit(response(), 31000, "pairing", true, true, true, true) }
        val bad = response(); bad.getJSONObject("expression").put("privateText", "forbidden")
        reject { OverlayAdmission().admit(bad, 1000, "pairing", true, true, true, true) }
        val fixture = response(); fixture.getJSONObject("expression").getJSONObject("source").put("kind", "fixture")
        reject { OverlayAdmission().admit(fixture, 1000, "pairing", true, true, true, true) }
    }
    @Test fun pairingReplacementReplayAndLateCallbacksAreDenied() {
        val gate = OverlayAdmission()
        gate.admit(response(), 1000, "first", true, true, true, true)
        reject { gate.admit(response(2, 2000), 2000, "replacement", true, true, true, true) }
        reject { gate.admit(response(), 1000, "first", true, true, true, true) }
        reject { gate.admit(response(2, 2000), 2000, "first", false, true, true, true) }
        assertNotNull(gate.admit(response(2, 2000), 2000, "first", true, true, true, true))
        assertEquals(32000, gate.expiresAt)
    }
    @Test fun hideDisableRecreationAndForegroundStartRejectionInvalidateRequests() {
        val requests = OverlayRequests()
        val token = requests.request(); assertTrue(requests.consume(token))
        requests.cancel(); assertFalse(requests.current(token)); assertFalse(requests.consume(token))
        assertFalse(OverlayRequests().consume(token))
        val failedStart = requests.request(); requests.cancel(failedStart)
        assertFalse(requests.pending())
        repeat(100) { val show = requests.request(); requests.cancel(); assertFalse(requests.consume(show)) }
    }
    @Test fun staleStartAndDestroyCannotCancelTheLatestRequest() {
        val requests = OverlayRequests()
        val old = requests.request(); val current = requests.request()
        assertFalse(requests.consume(old)); requests.cancel(old)
        assertTrue(requests.consume(current)); assertFalse(requests.consume(current))
        assertTrue(requests.current(current))
    }
    @Test fun concurrentRequestsHaveExactlyOneCurrentGeneration() {
        val requests = OverlayRequests(); val pool = Executors.newFixedThreadPool(4)
        try {
            val tokens = pool.invokeAll((1..20).map { java.util.concurrent.Callable { requests.request() } }).map { it.get() }
            assertEquals(1, tokens.count { requests.current(it) })
            assertEquals(1, tokens.count { requests.consume(it) })
        } finally { pool.shutdownNow() }
    }
}
