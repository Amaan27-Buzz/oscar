package io.dawnlight.oscar.mobile

import org.junit.Assert.*
import org.junit.Test

class GridPresentationTest {
    @Test fun lostSourceWithdrawsIdentityAndPrivateWork() {
        val state = MobileState(link = Link.CONNECTED, connectedNode = "phone", snapshot = CoreSnapshot(emptyList(), emptyList(), 1))
        val lost = state.unavailable("UNKNOWN")
        assertNull(lost.connectedNode); assertNull(lost.snapshot); assertEquals(Presence.ERROR, lost.presence)
        val task = CoreTask("t", "request", "executing", "desktop", "offline", 1, listOf("cancel"), emptyList(), null, null)
        assertEquals("Executor unavailable · outcome UNKNOWN", task.label)
    }
}
