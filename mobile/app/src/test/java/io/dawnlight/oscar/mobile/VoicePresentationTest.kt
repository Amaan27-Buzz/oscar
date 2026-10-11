package io.dawnlight.oscar.mobile
import org.junit.Assert.*
import org.junit.Test
class VoicePresentationTest {
    @Test fun cancelledEpochRejectsLateSpeechAndCapture() {
        val current = VoiceStatus(4)
        assertEquals(current, current.admitted(3, VoicePhase.SPEAKING, "obsolete"))
        assertEquals(VoicePhase.LISTENING, current.admitted(4, VoicePhase.LISTENING, "active").phase)
    }
    @Test fun cancellationDoesNotClaimListeningOrConsent() {
        VoicePresentation.invalidate()
        val token = VoicePresentation.begin()
        VoicePresentation.invalidate()
        VoicePresentation.report(token, VoicePhase.LISTENING, "obsolete")
        assertEquals(VoicePhase.IDLE, VoicePresentation.state.value.phase)
    }
    @Test fun delayedStartsRequireCurrentOwnerInvocationAndBothRealGrants() {
        val pending = VoiceStatus(9, VoicePhase.STARTING)
        assertTrue(pending.admitsCapture(9, true, true, true))
        assertFalse(pending.admitsCapture(8, true, true, true))
        assertFalse(pending.admitsCapture(9, false, true, true))
        assertFalse(pending.admitsCapture(9, true, false, true))
        assertFalse(pending.admitsCapture(9, true, true, false))
        val cancelled = pending.admitted(9, VoicePhase.IDLE, "Microphone off")
        assertFalse(cancelled.admitsCapture(9, true, true, true))
    }
    @Test fun failureDenialAndUnavailableRetireLateCallbacksAndDestroyStatus() {
        for (terminal in listOf(VoicePhase.FAILED, VoicePhase.MUTED, VoicePhase.UNAVAILABLE)) {
            val failed = VoiceStatus(12, VoicePhase.STARTING).admitted(12, terminal, "Reference terminal state")
            assertEquals(failed, failed.admitted(12, VoicePhase.IDLE, "Microphone off"))
            assertEquals(failed, failed.admitted(12, VoicePhase.LISTENING, "obsolete capture"))
            assertEquals(failed, failed.admitted(12, VoicePhase.SPEAKING, "obsolete output"))
            assertFalse(failed.admitsCapture(12, true, true, true))
        }
    }
}
