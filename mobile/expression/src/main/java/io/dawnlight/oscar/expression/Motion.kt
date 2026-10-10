package io.dawnlight.oscar.expression

import kotlin.math.*
import org.json.JSONObject

class Pose private constructor(private val values: List<Double>) {
    val x get() = values[0]; val y get() = values[1]; val tilt get() = values[2]; val body get() = values[3]
    val eye get() = values[4]; val width get() = values[5]; val arc get() = values[6]; val slant get() = values[7]
    val span get() = values[8]; val gx get() = values[9]; val gy get() = values[10]; val lid get() = values[11]; val opening get() = values[12]
    operator fun get(key: String) = values[keys.indexOf(key)]
    fun map() = keys.zip(values).toMap()
    fun json() = JSONObject(map())
    companion object {
        val keys = listOf("x", "y", "tilt", "body", "eye", "width", "arc", "slant", "span", "gx", "gy", "lid", "opening")
        fun of(map: Map<String, Double>): Pose { require(map.keys == keys.toSet() && map.values.all { it.isFinite() }); return Pose(keys.map { map.getValue(it) }) }
        fun json(o: JSONObject) = of(keys.associateWith { (o.get(it) as Number).toDouble() })
        fun zero() = of(keys.associateWith { 0.0 })
    }
}
data class Scene(val operation: String, val delivery: String)
data class Boundary(val availability: String = "available", val muted: Boolean = false, val owner: Boolean = false)
data class Resolved(val operation: String, val delivery: String, val muted: Boolean, val label: String)
data class MotionSettings(val intensity: Double = 1.0, val weight: Double = 1.0, val gazeX: Double = 0.0, val gazeY: Double = 0.0) {
    init { require(intensity.isFinite() && intensity in .35..1.0 && weight.isFinite() && weight in .7..1.5 && gazeX.isFinite() && abs(gazeX) <= 10 && gazeY.isFinite() && abs(gazeY) <= 7) }
}
data class Beat(val at: Double, val scene: Scene)
data class Study(val from: Pose, val velocity: Pose, val beats: List<Beat>, val duration: Double, val blink: Boolean = false, val choreography: Boolean = true)

/** Shared data plus plain JVM numeric mechanics; no Android, audio, network or Core imports. */
class MotionData(raw: String) {
    private val data = JSONObject(raw).also { require(it.getInt("version") == 1) }
    val canonical = Pose.json(data.getJSONObject("canonical"))
    private val marks = data.getJSONObject("deliveries")
    private fun path(name: String) = data.getJSONArray(name).let { rows -> (0 until rows.length()).map { i -> rows.getJSONArray(i).let { row -> (0..3).map { row.getDouble(it) } } } }
    private val speech = path("speechTravel"); private val work = path("workTravel")
    fun resolve(scene: Scene, boundary: Boundary = Boundary()): Resolved {
        var op = if (scene.operation == "available" || Operation.entries.any { it.wire == scene.operation }) scene.operation else "unknown"
        var cue = if (Delivery.entries.any { it.wire == scene.delivery }) scene.delivery else "composed"
        when {
            boundary.availability == "unavailable" || op == "unavailable" -> { op = "unavailable"; cue = "subdued" }
            boundary.availability !in listOf("available", "unavailable") || op == "unknown" -> { op = "unknown"; cue = "hesitant" }
            op == "error" -> cue = "concerned"
            boundary.owner || op == "waiting" -> { op = "waiting"; cue = if (boundary.owner || cue == "attentive") "attentive" else "subdued" }
            boundary.muted || op == "muted" -> { op = "muted"; cue = "composed" }
            op in listOf("processing", "executing", "verifying") -> cue = "focused"
            op == "listening" || (op == "attentive" && cue !in listOf("interrupted", "resting", "curious")) -> cue = "attentive"
            op == "speaking" && cue in listOf("asleep", "interrupted", "subdued") -> cue = "composed"
        }
        val muted = boundary.muted || scene.operation == "muted" || op == "muted"
        return Resolved(op, cue, muted, op + if (muted && op != "muted") " · conversational mute" else "")
    }
    fun pose(scene: Scene, settings: MotionSettings = MotionSettings()): Pose {
        val r = resolve(scene); val p = canonical.map().toMutableMap()
        val marking = marks.optJSONObject(r.delivery)
        marking?.keys()?.asSequence()?.forEach { p[it] = marking.getDouble(it) }
        when (r.operation) {
            "verifying" -> p.putAll(mapOf("eye" to .51, "arc" to 0.0, "gx" to 0.0, "tilt" to 0.0, "lid" to 0.0, "opening" to .4))
            "executing" -> p.putAll(mapOf("x" to -42.0, "y" to -18.0, "gx" to 8.0, "tilt" to -8.0, "opening" to .8))
            "processing" -> p.putAll(mapOf("x" to -32.0, "y" to -24.0, "gx" to -6.0, "gy" to -5.0, "tilt" to -8.0, "opening" to .5))
            "muted" -> p.putAll(mapOf("eye" to .7, "arc" to 0.0, "gx" to 0.0))
            "speaking" -> p.putAll(mapOf("x" to -42.0, "y" to -6.0, "tilt" to 6.0, "opening" to .95))
        }
        Pose.keys.forEach { p[it] = canonical[it] + (p.getValue(it) - canonical[it]) * settings.intensity }
        if (r.delivery in listOf("attentive", "surprised", "interrupted") || r.operation == "speaking") p["opening"] = if (r.operation == "speaking") .95 else marking?.optDouble("opening", 0.0) ?: 0.0
        if (r.delivery == "asleep") p.putAll(mapOf("eye" to 0.0, "opening" to 0.0, "arc" to 5.0, "slant" to 0.0))
        if (r.operation !in listOf("unavailable", "unknown", "muted", "error", "waiting")) {
            p["gx"] = (p.getValue("gx") + settings.gazeX).coerceIn(-14.0, 14.0); p["gy"] = (p.getValue("gy") + settings.gazeY).coerceIn(-10.0, 10.0)
        }
        return Pose.of(p)
    }
    fun blend(from: Pose, to: Pose, ms: Double, settings: MotionSettings, velocity: Pose = Pose.zero()): Pose {
        val t = ms.coerceIn(0.0, 700.0); if (t == 0.0) return from
        return Pose.of(Pose.keys.associateWith { key ->
            if (key in listOf("x", "y", "tilt", "body")) {
                val travel = if (velocity[key] == 0.0) max(0.0, t - 45) else t
                val weight = settings.weight * if (key == "body") 1.35 else 1.0
                val w = 19 / sqrt(weight); val z = .84; val d = w * sqrt(1 - z * z); val a = from[key] - to[key]; val b = (velocity[key] + z * w * a) / d
                if (t >= 700) to[key] else to[key] + exp(-z * w * travel / 1000) * (a * cos(d * travel / 1000) + b * sin(d * travel / 1000))
            } else {
                val duration = if (key in listOf("gx", "gy")) 95.0 else if (key in listOf("arc", "slant", "span")) 170.0 else 210.0
                val u = (t / duration).coerceIn(0.0, 1.0); from[key] + (to[key] - from[key]) * u * u * (3 - 2 * u)
            }
        })
    }
    private fun travel(points: List<List<Double>>, ms: Double): List<Double> {
        val segment = points.indexOfFirst { it[0] > ms }
        if (ms <= points.first()[0] || segment < 1) return listOf(0.0, 0.0, 0.0)
        val a = points[segment - 1]; val b = points[segment]; val before = points[max(0, segment - 2)]; val after = points[min(points.lastIndex, segment + 1)]
        val duration = b[0] - a[0]; val u = (ms - a[0]) / duration
        return (1..3).map { axis ->
            val start = if (segment == 1) 0.0 else (b[axis] - before[axis]) / (b[0] - before[0])
            val end = if (segment == points.lastIndex) 0.0 else (after[axis] - a[axis]) / (after[0] - a[0])
            (2*u*u*u-3*u*u+1)*a[axis]+(u*u*u-2*u*u+u)*duration*start+(-2*u*u*u+3*u*u)*b[axis]+(u*u*u-u*u)*duration*end
        }
    }
    fun study(from: Pose, scene: Scene, velocity: Pose = Pose.zero(), blink: Boolean = false): Study {
        val release = mapOf("surprised" to 850.0, "amused" to 1400.0, "pleased" to 1400.0, "interrupted" to 650.0)[scene.delivery]
        val beats = mutableListOf(Beat(0.0, scene))
        if (release != null) beats += Beat(release, Scene(scene.operation, if (scene.delivery == "interrupted") "attentive" else "composed"))
        return Study(from, velocity, beats, (release ?: 0.0) + if (scene.operation in listOf("speaking", "executing")) 5200.0 else 1800.0, blink)
    }
    private fun perform(from: Pose, r: Resolved, local: Double, settings: MotionSettings, velocity: Pose, reduced: Boolean, blink: Boolean, choreography: Boolean): Pose {
        val target = pose(Scene(r.operation, r.delivery), settings)
        val p = (if (reduced) target else blend(from, target, local, settings, velocity)).map().toMutableMap()
        if (choreography && !reduced && !r.muted && r.operation in listOf("speaking", "executing")) {
            val offset = travel(if (r.operation == "speaking") speech else work, local)
            listOf("x", "y", "tilt").forEachIndexed { i, key -> p[key] = p.getValue(key) + offset[i] * settings.intensity }
            if (r.operation == "speaking") {
                val stress = exp(-((local-1200)/180).pow(2)) + .7 * exp(-((local-2300)/220).pow(2))
                p["eye"] = (p.getValue("eye") - .12*stress).coerceIn(0.0, 1.3); p["opening"] = (p.getValue("opening") - .16*stress).coerceIn(0.0, 1.0)
            }
        }
        if (blink && !reduced && local > 80 && local < 240 && r.operation !in listOf("unavailable", "unknown", "muted", "error")) {
            val close = 1-sin(PI*(local-80)/160); p["eye"] = p.getValue("eye")*close; p["opening"] = p.getValue("opening")*close
        }
        return Pose.of(p)
    }
    fun sample(study: Study, ms: Double, settings: MotionSettings = MotionSettings(), reduced: Boolean = false, boundary: Boundary = Boundary()): Pair<Pose, Resolved> {
        val t = ms.coerceIn(0.0, study.duration); var from = study.from; var velocity = study.velocity; var current = study.beats.first(); var start = 0.0
        for (next in study.beats.drop(1)) {
            if (t < next.at) break
            val old = resolve(current.scene, boundary); val elapsed = next.at - start
            val at = perform(from, old, elapsed, settings, velocity, reduced, study.blink, study.choreography)
            val before = perform(from, old, max(0.0, elapsed-.01), settings, velocity, reduced, study.blink, study.choreography)
            velocity = Pose.of(Pose.keys.associateWith { (at[it]-before[it])*100000 }); from = at; current = next; start = next.at
        }
        val resolved = resolve(current.scene, boundary)
        return perform(from, resolved, t-start, settings, velocity, reduced, study.blink, study.choreography) to resolved
    }
}
