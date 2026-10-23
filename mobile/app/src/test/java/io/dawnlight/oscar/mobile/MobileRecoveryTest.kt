package io.dawnlight.oscar.mobile

import org.junit.Assert.*
import org.junit.Test

class MobileRecoveryTest {
    @Test fun lossWithdrawsPrivateReadbackButPreservesUnsentDraft() {
        val task = CoreTask("t", "private", "planned", "d", "online", 0, listOf("approve", "deny"), emptyList(), null, null, "private reply",
            responseStatus = "RECALLED", sourceEventIds = listOf("private-source"))
        val state = MobileState(epoch = 9, link = Link.CONNECTED, draft = "unsent", snapshot = CoreSnapshot(listOf(task), emptyList(), 1),
            interactions = listOf(Interaction("private", "reply")), inspected = task)
        val failed = state.unavailable("UNKNOWN")
        assertEquals("unsent", failed.draft); assertNull(failed.inspected); assertNull(failed.snapshot)
        assertTrue(failed.interactions.isEmpty()); assertEquals(10, failed.epoch)
        val hidden = state.snapshot!!.withoutPrivate().tasks.single()
        assertEquals(listOf("deny"), hidden.actions); assertNull(hidden.response); assertFalse(hidden.description.contains("private"))
        assertNull(hidden.responseStatus); assertTrue(hidden.sourceEventIds.isEmpty())
        assertEquals(failed, failed.fenced(state, 9))
    }
    @Test fun executionEvidenceLabelsAreSeparate() {
        fun task(state: String) = CoreTask("t", "request", state, "desktop", "online", 0, emptyList(), emptyList(), null, null)
        assertEquals("Verifying", task("verifying").label)
        assertEquals("Reported · awaiting verification", task("result_received").label)
        assertEquals("Waiting · outcome unknown", task("unknown").label)
        assertEquals("Partially verified", task("partially_verified").label)
    }
}
