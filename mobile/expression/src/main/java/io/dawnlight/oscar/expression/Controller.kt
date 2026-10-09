package io.dawnlight.oscar.expression

import kotlin.math.max

data class ExpressionSnapshot(val pose: Pose, val resolved: Resolved, val source: Source, val generation: Long,
    val animation: AnimationPhase, val moving: Boolean, val expiresAt: Long?, val priority: EffectivePriority)
private data class Transition(val from: Pose, val velocity: Pose, val started: Long, val duration: Double,
    val generation: Long, val id: String, val accent: Study?)

/** Single UI/event-loop owner. Animation outcomes have no task, permission or audio authority. */
class ExpressionController(val source: Source, val data: MotionData, val settings: MotionSettings = MotionSettings()) {
    init { require(Contract.identifier(source.id)) }
    private var frame: ExpressionEvent? = null
    private var transition: Transition? = null
    private var held = data.pose(Scene("unknown", "hesitant"), settings)
    private var generation = -1L
    private val records = mutableListOf<AnimationRecord>()
    private var invalid = false
    private var cancelled = false
    private var settledDelivery: String? = null
    private var forceReduced = false
    private fun reduced() = forceReduced || frame?.reducedMotion == true
    private fun resolved(): Resolved {
        val f = frame
        if (invalid || f == null) return data.resolve(Scene("unknown", "hesitant"), Boundary(muted = f?.muted == true || f?.operation == Operation.MUTED))
        val cue = settledDelivery ?: if (f.kind == EventKind.INTERRUPT) "interrupted" else f.delivery.wire
        return data.resolve(Scene(f.operation.wire, cue), Boundary(f.availability.wire, f.muted, f.attention == Attention.OWNER))
    }
    private fun poseAt(now: Double): Pose {
        val t = transition ?: return held
        val r = resolved(); val elapsed = max(0.0, now-t.started)
        if (reduced()) return t.accent?.let { data.sample(it,elapsed,settings,reduced=true).first } ?: data.pose(Scene(r.operation, r.delivery), settings)
        return t.accent?.let { data.sample(it, elapsed, settings).first }
            ?: data.blend(t.from, data.pose(Scene(r.operation, r.delivery), settings), elapsed, settings, t.velocity)
    }
    private fun velocity(now: Long): Pose {
        if (transition == null || reduced()) return Pose.zero()
        val a = poseAt(now.toDouble()); val b = poseAt(now+.01)
        return Pose.of(Pose.keys.associateWith { (b[it]-a[it])*100000 })
    }
    private fun finish(outcome: AnimationOutcome) {
        transition?.let { records += AnimationRecord(it.generation, it.id, outcome); if (records.size > 32) records.removeAt(0) }
        transition = null
    }
    private fun invalidate(outcome: AnimationOutcome) {
        finish(outcome); invalid = true; cancelled = true
        val r = resolved(); held = data.pose(Scene(r.operation, r.delivery), settings)
    }
    fun receive(raw: String, now: Long): String {
        val event = Contract.parse(raw) ?: run { invalidate(AnimationOutcome.INVALID); return "invalid" }
        if (event.source != source) { invalidate(AnimationOutcome.INVALID); return "source_mismatch" }
        if (event.generation <= generation) return "stale"
        if (!Contract.fresh(event,now)) { invalidate(AnimationOutcome.INVALID); return "invalid" }
        snapshot(now)
        val previous = resolved(); val from = poseAt(now.toDouble()); val velocity = velocity(now)
        val old = frame; val wasInvalid = invalid; val wasCancelled = cancelled
        frame = event; generation = event.generation; invalid = false; cancelled = false
        val r = resolved()
        if (event.kind == EventKind.ACCENT) {
            val permitted = when(event.accent) {
                Accent.PHRASE -> previous.operation == "speaking" && r.operation == "speaking"
                Accent.ENGAGEMENT -> previous.operation == "executing" && r.operation == "executing"
                Accent.BLINK -> r.operation !in listOf("unavailable", "unknown", "muted", "waiting", "error")
                null -> false
            }
            if (old == null || !permitted || r.muted) { invalidate(AnimationOutcome.INVALID); return "invalid" }
        }
        if (event.kind == EventKind.STATE && old != null && !wasInvalid && !wasCancelled && old.transitionId == event.transitionId &&
            old.operation == event.operation && old.delivery == event.delivery && old.availability == event.availability &&
            old.muted == event.muted && old.attention == event.attention && old.reducedMotion == event.reducedMotion) return "accepted"
        settledDelivery = null
        finish(if (event.kind == EventKind.CANCEL) AnimationOutcome.CANCELLED else AnimationOutcome.SUPERSEDED)
        if (event.kind == EventKind.CANCEL) { held = from; cancelled = true; return "accepted" }
        val target = resolved(); val scene = Scene(target.operation, target.delivery)
        val reaction = target.delivery in listOf("amused", "pleased", "surprised", "interrupted") && target.operation in listOf("idle", "attentive")
        val accent = if (event.kind == EventKind.ACCENT) Study(from, velocity, listOf(Beat(0.0, scene)), if (event.accent == Accent.BLINK) 700.0 else 5200.0, event.accent == Accent.BLINK, event.accent != Accent.BLINK)
            else if (reaction) data.study(from, scene, velocity).copy(choreography = false) else null
        transition = Transition(from, velocity, now, if (reduced() && !reaction) 0.0 else accent?.duration ?: 700.0, event.generation, event.transitionId, accent)
        held = from; snapshot(now); return "accepted"
    }
    fun snapshot(now: Long): ExpressionSnapshot {
        val f = frame
        if (f != null && !invalid && (now >= f.expiresAt || now < f.eventTime-250)) invalidate(AnimationOutcome.EXPIRED)
        val pose = poseAt(now.toDouble()); val t = transition
        val delivery = t?.accent?.let { data.sample(it, max(0.0, (now-t.started).toDouble()), settings, reduced()).second.delivery }
        if (t != null && now-t.started >= t.duration) {
            settledDelivery = delivery; held = pose; finish(if (t.accent != null) AnimationOutcome.ACCENT_FINISHED else AnimationOutcome.SETTLED)
        }
        val r = resolved().let { if (delivery == null) it else it.copy(delivery = delivery) }
        val priority = when {
            r.operation in listOf("unavailable", "unknown", "error") -> EffectivePriority.CRITICAL
            r.operation == "waiting" -> EffectivePriority.ATTENTION
            r.muted -> EffectivePriority.PRIVACY
            frame?.priority == Priority.URGENT || frame?.kind == EventKind.INTERRUPT -> EffectivePriority.URGENT
            r.operation in listOf("listening", "speaking", "processing", "executing", "verifying") -> EffectivePriority.ACTIVITY
            else -> EffectivePriority.DELIVERY
        }
        return ExpressionSnapshot(pose, r, source, generation, if (transition != null) if (transition?.accent != null) AnimationPhase.ACCENT else AnimationPhase.SETTLING else if (cancelled) AnimationPhase.CANCELLED else AnimationPhase.HELD, transition != null, if (invalid) null else frame?.expiresAt, priority)
    }
    fun suspend() { invalidate(AnimationOutcome.LIFECYCLE) }
    fun setReducedMotion(reduced: Boolean, now: Long) {
        forceReduced = reduced
        if (frame == null) return
        if (reduced()) {
            val r = resolved(); held = data.pose(Scene(r.operation, r.delivery), settings)
            if ((transition?.accent?.beats?.size ?: 0) <= 1) finish(AnimationOutcome.CANCELLED)
        }
        snapshot(now)
    }
    fun takeAnimationRecords(): List<AnimationRecord> = records.toList().also { records.clear() }
}
