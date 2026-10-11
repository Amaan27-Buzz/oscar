package io.dawnlight.oscar.mobile

import io.dawnlight.oscar.expression.*
import org.json.JSONObject

/** Only admitted state crosses into animation. No task identifiers, text or signing material. */
class MobileExpression(private val epoch: Long) {
    val source = Source(SourceKind.CORE, "mobile-${java.util.UUID.randomUUID()}")
    private var generation = 0L
    private var transition = 0L
    private var previous: Operation? = null

    fun event(state: MobileState, now: Long, composing: Boolean = false, reduced: Boolean = false): String {
        val operation = when {
            state.epoch != epoch -> Operation.UNKNOWN
            state.link == Link.DEGRADED -> Operation.ERROR
            state.link != Link.CONNECTED -> Operation.UNAVAILABLE
            state.approval != null || state.snapshot?.tasks?.any { "approve" in it.actions } == true -> Operation.WAITING
            state.snapshot?.tasks?.any { it.state == "verifying" } == true -> Operation.VERIFYING
            state.snapshot?.tasks?.any { it.state in setOf("executing", "awaiting_result", "result_received") } == true -> Operation.EXECUTING
            state.busy -> Operation.PROCESSING
            composing -> Operation.ATTENTIVE
            state.snapshot != null -> Operation.IDLE
            else -> Operation.UNKNOWN
        }
        if (operation != previous) { transition++; previous = operation }
        val observed = state.observedAt.takeIf { it > 0 } ?: now
        val expires = if (state.link == Link.CONNECTED && !state.busy) observed + 30_000 else now + 30_000
        return JSONObject().put("version", 1).put("source", JSONObject().put("kind", "core").put("id", source.id))
            .put("generation", ++generation).put("transitionId", "state-$transition")
            .put("eventTime", minOf(now, expires - 1)).put("expiresAt", expires)
            .put("kind", "state").put("priority", "normal").put("operation", operation.wire)
            .put("delivery", if (operation == Operation.ATTENTIVE) "attentive" else "composed")
            .put("availability", if (state.link == Link.CONNECTED) "available" else "unavailable")
            .put("muted", false).put("attention", if (operation == Operation.WAITING) "owner" else "none")
            .put("reducedMotion", reduced).toString()
    }
}
