package io.dawnlight.oscar.mobile

import io.dawnlight.oscar.expression.Contract
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class CoreClockTest {
    @Test fun newerObservationCannotReviveExpiredStateAfterClockRollback() {
        val first = CoreClock.observe(100000, 100000, 1000, 1000)
        val replay = CoreClock.observe(100000, 100000, 30999, 31000, first)
        assertEquals(130000, replay.now(31000))
        assertNull(Contract.validate(event(100000), replay.now(31000)))
        val ahead = CoreClock.observe(100000, 105000, 1000, 1200)
        assertNotNull(Contract.validate(event(100000), ahead.now(1200)))
    }
    private fun event(time: Long) = JSONObject("""{"version":1,"source":{"kind":"core","id":"presence:canonical"},"generation":1,"transitionId":"state","eventTime":$time,"expiresAt":${time+30000},"kind":"state","priority":"normal","operation":"idle","delivery":"composed","availability":"available","muted":false,"attention":"none","reducedMotion":true}""").toString()
    @Test fun authenticatedObservationHandlesClockSkewAndChargesTransportWithoutChangingEvent() {
        val raw = event(100000)
        assertNull(Contract.validate(raw, 99000))
        val clock = CoreClock.observe(100000, 99000, 1000, 1200)
        assertNotNull(Contract.validate(raw, clock.now(1200)))
        assertEquals(100200, clock.now(1200))
        assertEquals(100700, clock.now(1700))
        assertNull(Contract.validate(raw, clock.now(31000)))
        // A fresh wrapper cannot make an expired canonical event fresh.
        assertNull(Contract.validate(raw, CoreClock.observe(130000, 130000, 1000, 1000).now(1000)))
        // Future-expression allowance stays at the canonical 250 ms.
        assertNull(Contract.validate(event(100251), CoreClock.observe(100000, 100000, 1000, 1000).now(1000)))
    }
    @Test fun invalidObservationTransportOrMonotonicRollbackFailsClosed() {
        fun reject(work: () -> Unit) { try { work(); fail("Invalid Core clock accepted") } catch (_: IllegalArgumentException) {} }
        reject { CoreClock.observe(130001, 100000, 1000, 1000) }
        reject { CoreClock.observe(100000, 100000, 1000, 999) }
        reject { CoreClock.observe(100000, 100000, 1000, 16001) }
        reject { CoreClock.observe(100000, 100000, 1000, 1000).now(999) }
    }
}
