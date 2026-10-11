package io.dawnlight.oscar.mobile

import io.dawnlight.oscar.expression.*
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MobileExpressionTest {
    private val now = 100_000L
    @Test fun truthfulStatesArePrivateAndEpochBound() {
        val adapter = MobileExpression(2)
        val base = MobileState(epoch = 2, link = Link.CONNECTED, observedAt = now)
        assertEquals(Operation.UNKNOWN, Contract.validate(adapter.event(base, now), now)!!.operation)
        val task = CoreTask("private-id", "private-text", "verifying", "private-target", "online", 1, emptyList(), emptyList(), null, null)
        val snapshot = CoreSnapshot(listOf(task), emptyList(), now)
        val raw = adapter.event(base.copy(snapshot = snapshot), now)
        assertFalse(raw.contains("private"))
        assertEquals(Operation.VERIFYING, Contract.validate(raw, now)!!.operation)
        assertEquals(Operation.UNKNOWN, Contract.validate(adapter.event(base.copy(epoch = 3), now), now)!!.operation)
        assertEquals(Operation.UNAVAILABLE, Contract.validate(adapter.event(MobileState(epoch = 2), now), now)!!.operation)
    }
    @Test fun heartbeatDoesNotReplayTransitionAndFreshnessExpires() {
        val adapter = MobileExpression(0)
        val state = MobileState(link = Link.CONNECTED, snapshot = CoreSnapshot(emptyList(), emptyList(), now), observedAt = now)
        val first = JSONObject(adapter.event(state, now, reduced = true))
        val next = JSONObject(adapter.event(state.copy(observedAt = now + 1000), now + 1000, reduced = true))
        assertEquals(first.getString("transitionId"), next.getString("transitionId"))
        assertTrue(next.getLong("generation") > first.getLong("generation"))
        assertTrue(next.getBoolean("reducedMotion"))
        assertNull(Contract.validate(adapter.event(state, now + 30_001), now + 30_001))
    }
}
