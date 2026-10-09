package io.dawnlight.oscar.expression

import org.json.JSONObject

enum class Operation(val wire: String) { IDLE("idle"), ATTENTIVE("attentive"), LISTENING("listening"), PROCESSING("processing"), EXECUTING("executing"), VERIFYING("verifying"), WAITING("waiting"), SPEAKING("speaking"), MUTED("muted"), UNAVAILABLE("unavailable"), ERROR("error"), UNKNOWN("unknown") }
enum class Delivery(val wire: String) { COMPOSED("composed"), ATTENTIVE("attentive"), CURIOUS("curious"), FOCUSED("focused"), AMUSED("amused"), PLEASED("pleased"), SURPRISED("surprised"), CONCERNED("concerned"), HESITANT("hesitant"), SUBDUED("subdued"), RESTING("resting"), ASLEEP("asleep"), INTERRUPTED("interrupted") }
enum class SourceKind(val wire: String) { CORE("core"), LAB("lab"), FIXTURE("fixture") }
enum class EventKind(val wire: String) { STATE("state"), ACCENT("accent"), INTERRUPT("interrupt"), CANCEL("cancel") }
enum class Availability(val wire: String) { AVAILABLE("available"), UNAVAILABLE("unavailable"), UNKNOWN("unknown") }
enum class Attention(val wire: String) { NONE("none"), OWNER("owner") }
enum class Priority(val wire: String) { NORMAL("normal"), URGENT("urgent") }
enum class Accent(val wire: String) { PHRASE("phrase"), ENGAGEMENT("engagement"), BLINK("blink") }
data class Source(val kind: SourceKind, val id: String)
class ExpressionEvent internal constructor(
    val source: Source, val generation: Long, val transitionId: String, val eventTime: Long, val expiresAt: Long,
    val kind: EventKind, val priority: Priority, val operation: Operation, val delivery: Delivery,
    val availability: Availability, val muted: Boolean, val attention: Attention, val reducedMotion: Boolean,
    val accent: Accent?,
)
enum class AnimationOutcome(val wire: String) { SETTLED("settled"), ACCENT_FINISHED("accent_finished"), SUPERSEDED("superseded"), CANCELLED("cancelled"), EXPIRED("expired"), INVALID("invalid"), LIFECYCLE("lifecycle") }
enum class AnimationPhase(val wire: String) { SETTLING("settling"), ACCENT("accent"), HELD("held"), CANCELLED("cancelled") }
enum class EffectivePriority(val wire: String) { CRITICAL("critical"), ATTENTION("attention"), PRIVACY("privacy"), URGENT("urgent"), ACTIVITY("activity"), DELIVERY("delivery") }
data class AnimationRecord(val generation: Long, val transitionId: String, val outcome: AnimationOutcome)

/** Provenance is not authentication. The surface must bind this to its already trusted publisher. */
object Contract {
    private val required = setOf("version", "source", "generation", "transitionId", "eventTime", "expiresAt", "kind", "priority", "operation", "delivery", "availability", "muted", "attention", "reducedMotion")
    fun identifier(value: String) = value.matches(Regex("[A-Za-z0-9:_-]{1,64}"))
    private fun integer(o: JSONObject, key: String): Long? {
        val value = (o.opt(key) as? Number)?.toDouble() ?: return null
        return if (value.isFinite() && value >= 0 && value <= 9007199254740991.0 && value % 1.0 == 0.0) value.toLong() else null
    }
    private inline fun <reified T : Enum<T>> enum(o: JSONObject, key: String, wire: (T) -> String): T? {
        val value = o.opt(key) as? String ?: return null
        return enumValues<T>().firstOrNull { wire(it) == value }
    }
    fun parse(raw: String): ExpressionEvent? = try {
        if (raw.length > 4096) null else decode(WireJson(raw).decode())
    } catch (_: Exception) { null }
    fun fresh(event: ExpressionEvent, now: Long) = now in 0..9007199254740991L && event.eventTime <= now+250 && event.expiresAt > now
    fun validate(raw: String, now: Long): ExpressionEvent? = parse(raw)?.takeIf { fresh(it,now) }
    private fun decode(o: JSONObject): ExpressionEvent? {
        val keys = o.keys().asSequence().toSet()
        if (!keys.containsAll(required) || (keys - required - "accent").isNotEmpty() || integer(o, "version") != 1L) return null
        val s = o.opt("source") as? JSONObject ?: return null
        if (s.keys().asSequence().toSet() != setOf("kind", "id")) return null
        val source = Source(enum<SourceKind>(s, "kind") { it.wire } ?: return null, s.opt("id") as? String ?: return null)
        val generation = integer(o, "generation") ?: return null
        val transitionId = o.opt("transitionId") as? String ?: return null
        val time = integer(o, "eventTime") ?: return null
        val expires = integer(o, "expiresAt") ?: return null
        if (!identifier(source.id) || !identifier(transitionId) || expires <= time || expires - time > 30000) return null
        val kind = enum<EventKind>(o, "kind") { it.wire } ?: return null
        val accent = if (kind == EventKind.ACCENT) enum<Accent>(o, "accent") { it.wire } ?: return null else null
        if (kind != EventKind.ACCENT && o.has("accent")) return null
        return ExpressionEvent(source, generation, transitionId, time, expires, kind,
            enum<Priority>(o, "priority") { it.wire } ?: return null,
            enum<Operation>(o, "operation") { it.wire } ?: return null,
            enum<Delivery>(o, "delivery") { it.wire } ?: return null,
            enum<Availability>(o, "availability") { it.wire } ?: return null,
            o.opt("muted") as? Boolean ?: return null,
            enum<Attention>(o, "attention") { it.wire } ?: return null,
            o.opt("reducedMotion") as? Boolean ?: return null, accent)
    }
}
