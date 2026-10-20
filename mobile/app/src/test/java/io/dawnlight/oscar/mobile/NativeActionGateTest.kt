package io.dawnlight.oscar.mobile

import org.junit.Assert.*
import org.junit.Test

class NativeActionGateTest {
    private var elapsed = 100L
    private var approved: NativeAction? = null
    private val gate = NativeActionGate({ elapsed }) { it == approved }
    private fun action() = NativeAction("request", "task", "node", "session", 1, 1, gate.generation,
        1000, "android.app.launch", "example.synthetic", "example.synthetic.Form")
    private fun approve(action: NativeAction) { approved = action; gate.foreground(true) }

    @Test fun exactCurrentAskIsRequiredAndRequestCannotReplay() {
        val request = action()
        gate.foreground(true)
        assertFalse(gate.admit(request))
        approve(request)
        assertTrue(gate.admit(request))
        assertFalse(gate.admit(request))
    }
    @Test fun taskNodeSessionTargetValueAndCapabilityCannotBeSubstituted() {
        val request = action(); approve(request)
        listOf(request.copy(taskId = "other"), request.copy(nodeId = "other"), request.copy(sessionId = "other"),
            request.copy(taskGeneration = 2), request.copy(authorityEpoch = 2),
            request.copy(packageName = "example.other"), request.copy(target = "Other"), request.copy(value = "other"),
            request.copy(capability = "android.ui.click")).forEach { assertFalse(gate.admit(it)) }
        assertTrue(gate.admit(request))
    }
    @Test fun foregroundLossAndRecreationFencePriorAction() {
        val request = action(); approve(request); assertTrue(gate.admit(request))
        gate.foreground(false); gate.foreground(true)
        assertFalse(gate.current(request))
        val replacement = NativeActionGate({ elapsed }) { true }.apply { foreground(true) }
        assertFalse(replacement.admit(request))
    }
    @Test fun cancellationAndRemoteRevocationStopContinuation() {
        val request = action(); approve(request); assertTrue(gate.admit(request))
        gate.cancel(request.requestId); assertFalse(gate.current(request))
        val next = request.copy(requestId = "next"); approve(next); assertTrue(gate.admit(next))
        approved = null; assertFalse(gate.current(next))
    }
    @Test fun localRevocationRemainsFencedAfterGrantReturns() {
        val request = action(); approve(request); assertTrue(gate.admit(request))
        gate.invalidate(); approve(request); assertFalse(gate.admit(request))
    }
    @Test fun expiredAndExcessiveLeaseAreRejected() {
        val request = action(); approve(request); elapsed = request.deadlineElapsed
        assertFalse(gate.admit(request))
        val long = action().copy(deadlineElapsed = elapsed + 60_001); approve(long); assertFalse(gate.admit(long))
    }
    @Test fun malformedAndUnknownActionsAreRejectedBeforeAuthorization() {
        listOf(action().copy(requestId = ""), action().copy(taskGeneration = -1), action().copy(authorityEpoch = -1), action().copy(packageName = "*"), action().copy(value = "x".repeat(2001)),
            action().copy(target = "x".repeat(513)), action().copy(capability = "android.root")).forEach {
            approve(it); assertFalse(gate.admit(it))
        }
    }
    @Test fun verifierFailureIsNotAuthority() {
        val unavailable = NativeActionGate({ elapsed }) { throw IllegalStateException("Core unavailable") }.apply { foreground(true) }
        assertFalse(unavailable.admit(action().copy(generation = unavailable.generation)))
    }
    @Test fun boundedAdmissionFailsClosedUntilFreshGeneration() {
        val bounded = NativeActionGate({ elapsed }) { true }.apply { foreground(true) }
        val request = action().copy(generation = bounded.generation)
        repeat(128) { assertTrue(bounded.admit(request.copy(requestId = "request-$it"))) }
        assertFalse(bounded.admit(request.copy(requestId = "overflow")))
        bounded.invalidate(); assertTrue(bounded.admit(request.copy(requestId = "fresh", generation = bounded.generation)))
    }
}
