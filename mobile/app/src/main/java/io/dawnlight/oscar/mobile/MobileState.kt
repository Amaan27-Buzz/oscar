package io.dawnlight.oscar.mobile

import org.json.JSONObject

enum class Destination(val label: String) { OSCAR("Conversation"), AUTOMATIONS("Automations"), ACTIVITY("Activity"), DEVICES("Devices"), SETTINGS("Preferences") }
enum class Presence { IDLE, ATTENTIVE, LISTENING, THINKING, SPEAKING, WAITING, MUTED, UNAVAILABLE, ERROR }
enum class Link { DISCONNECTED, CONNECTING, CONNECTED, DEGRADED }

data class CoreTask(
    val id: String, val description: String, val state: String, val target: String,
    val nodeStatus: String, val generation: Int, val actions: List<String>,
    val evidence: List<String>, val value: String?, val blocker: String?,
    val response: String? = null,
    val responseTruncated: Boolean = false,
    val progress: CoreProgress? = null, val artifacts: List<CoreArtifact> = emptyList(), val ownership: String = "planned",
    val origin: String = "Core", val originNode: String? = null,
) {
    val label: String get() = if (state in setOf("executing", "awaiting_result", "result_received", "verifying") && nodeStatus != "online") "Executor unavailable · outcome UNKNOWN" else when (state) {
        "planned" -> "Needs approval"
        "executing" -> "Working"
        "awaiting_result" -> "Waiting for Worker"
        "result_received" -> "Reported · awaiting verification"
        "verifying" -> "Verifying"
        "verified" -> "Completed · verified"
        "partially_verified" -> "Partially verified"
        "unknown" -> "Waiting · outcome unknown"
        else -> state.replaceFirstChar { it.uppercase() }
    }
}
data class CoreProgress(val fraction: Double, val step: String, val current: Boolean)
data class CoreArtifact(val id: String, val kind: String, val status: String, val hash: String?)
data class CoreNode(val id: String, val role: String, val status: String, val paired: Boolean, val capabilities: List<String>)
data class CoreSnapshot(val tasks: List<CoreTask>, val nodes: List<CoreNode>, val observedAt: Long,
    val presence: String? = null, val setup: Map<String, String> = emptyMap(), val adaptive: List<AdaptiveDescriptor> = emptyList(), val executive: List<ExecutiveGoal>? = null)
data class ExecutiveGoal(val id: String, val goal: String, val state: String, val runs: Int, val maxRuns: Int)
data class Interaction(val text: String, val response: String, val taskId: String? = null)
data class MobileState(
    val epoch: Long = 0, val link: Link = Link.DISCONNECTED, val busy: Boolean = false,
    val snapshot: CoreSnapshot? = null, val interactions: List<Interaction> = emptyList(),
    val approval: Approval? = null, val message: String? = null,
    val observedAt: Long = 0,
    val draft: String = "", val inspected: CoreTask? = null, val privateSuppressed: Boolean = false,
    val restoring: Boolean = false,
    val replyPreview: String? = null,
    val connectedNode: String? = null,
) {
    fun coreNow(localNow: Long): Long = if (link == Link.CONNECTED && observedAt > 0 && snapshot != null)
        localNow + snapshot.observedAt - observedAt else localNow
    val presence: Presence get() = when {
        link == Link.DEGRADED -> Presence.ERROR
        link != Link.CONNECTED -> Presence.UNAVAILABLE
        busy -> Presence.THINKING
        snapshot?.tasks?.any { it.state in setOf("executing", "awaiting_result", "result_received", "verifying") } == true -> Presence.THINKING
        approval != null || snapshot?.tasks?.any { "approve" in it.actions } == true -> Presence.WAITING
        else -> Presence.ATTENTIVE
    }
    fun fenced(next: MobileState, expectedEpoch: Long): MobileState = if (epoch == expectedEpoch) next else this
    fun unavailable(message: String) = copy(epoch = epoch + 1, link = Link.DEGRADED, busy = false,
        snapshot = null, connectedNode = null, approval = null, replyPreview = null, inspected = null, interactions = emptyList(), observedAt = 0, restoring = false, message = message)
}

private val taskStates = setOf("planned", "executing", "awaiting_result", "result_received", "verifying", "verified", "partially_verified", "failed", "blocked", "cancelled", "unknown")
private val taskActions = setOf("approve", "deny", "cancel", "retry")
internal fun JSONObject.bounded(key: String, max: Int): String {
    val value = get(key)
    require(value is String && value.isNotEmpty() && value.length <= max) { "Invalid Core field" }
    return value
}
private fun JSONObject.strings(key: String, max: Int): List<String> {
    val array = getJSONArray(key)
    require(array.length() <= max)
    return (0 until array.length()).map { index ->
        val value = array.get(index)
        require(value is String && value.length in 1..256)
        value
    }
}
fun parseTask(json: JSONObject): CoreTask {
    val state = json.bounded("state", 32)
    val actions = json.strings("actions", 4)
    require(state in taskStates && actions.all { it in taskActions })
    val generation = json.get("generation")
    require(generation is Int && generation >= 0)
    val value = if (json.has("value")) json.bounded("value", 4096) else null
    val evidence = json.strings("evidence_ids", 100)
    require(value == null || (state == "verified" && evidence.isNotEmpty()))
    val blocker = if (json.has("blocker") && !json.isNull("blocker") && json.getString("blocker").isNotEmpty()) json.bounded("blocker", 1000) else null
    val status = json.bounded("node_status", 32)
    val response = if (json.has("response")) {
        require(json.bounded("response_status", 32) == "REPORTED")
        json.bounded("response", 8192)
    } else null
    require(status in setOf("online", "offline", "degraded"))
    require(!json.has("response_truncated") || json.get("response_truncated") is Boolean)
    val progress = if (json.has("progress") && !json.isNull("progress")) {
        val item = json.getJSONObject("progress")
        require(item.get("fraction") is Number && item.getString("status") == "REPORTED")
        val fraction = item.getDouble("fraction"); require(fraction.isFinite() && fraction in 0.0..1.0)
        require(item.get("current") is Boolean)
        CoreProgress(fraction, item.bounded("step", 256), item.getBoolean("current"))
    } else null
    val artifacts = if (json.has("artifacts")) {
        val items = json.getJSONArray("artifacts"); require(items.length() <= 20)
        (0 until items.length()).map {
            val item = items.getJSONObject(it); val status = item.bounded("status", 32)
            require(status in setOf("VERIFIED", "REPORTED", "UNKNOWN"))
            val hash = if (!item.has("content_hash") || item.isNull("content_hash")) null else item.bounded("content_hash", 64).also { require(it.matches(Regex("[a-f0-9]{64}"))) }
            CoreArtifact(item.bounded("id", 80), item.bounded("kind", 80), status, hash)
        }
    } else emptyList()
    val ownership = if (json.has("ownership")) json.bounded("ownership", 16) else "planned"
    require(ownership in setOf("planned", "leased", "none", "expired"))
    val origin = if (json.has("origin_surface")) json.bounded("origin_surface", 32) else "Core"
    require(origin in setOf("Core", "Desktop", "Mobile"))
    val originNode = if (json.has("origin_node") && !json.isNull("origin_node")) json.bounded("origin_node", 80) else null
    return CoreTask(json.bounded("task_id", 80), json.bounded("description", 256), state,
        json.bounded("target", 80), status, generation, if (status == "online") actions else actions.filter { it in setOf("cancel", "deny") },
        evidence, value, blocker, response, json.optBoolean("response_truncated", false), progress, artifacts, ownership, origin, originNode)
}
fun CoreSnapshot.withoutPrivate() = copy(adaptive = emptyList(), executive = null, tasks = tasks.map { it.copy(description = "Private request hidden", response = null, value = null,
    artifacts = emptyList(), progress = it.progress?.copy(step = "Worker checkpoint available"),
    blocker = it.blocker?.let { "Inspect Core before continuing" }, actions = it.actions.filter { action -> action in setOf("deny", "cancel") }) })
fun parseSnapshot(json: JSONObject): CoreSnapshot {
    val tasks = json.getJSONArray("tasks")
    val nodes = json.getJSONArray("nodes")
    require(tasks.length() <= 100 && nodes.length() <= 100)
    val parsedTasks = (0 until tasks.length()).map { parseTask(tasks.getJSONObject(it)) }
    val parsedNodes = (0 until nodes.length()).map {
        val node = nodes.getJSONObject(it)
        val capabilities = node.getJSONArray("capabilities")
        require(capabilities.length() <= 256 && node.get("paired") is Boolean && node.get("protocol_version") == 1)
        val status = node.bounded("status", 32)
        require(status in setOf("online", "offline", "degraded"))
        val identifier = node.bounded("id", 80)
        CoreNode(identifier, node.bounded("role", 80).let { if (it == "Sunday") "OSCAR Mobile" else it }, status,
            node.getBoolean("paired"), if (status == "offline") emptyList() else (0 until capabilities.length()).map { index ->
                val capability = capabilities.getJSONObject(index)
                require(capability.bounded("node_id", 80) == identifier && capability.get("version") == 1)
                capability.bounded("id", 128)
                capability.bounded("input_kind", 128)
                capability.bounded("name", 256)
            })
    }
    require(parsedTasks.map { it.id }.distinct().size == parsedTasks.size && parsedNodes.map { it.id }.distinct().size == parsedNodes.size)
    val observed = json.get("observed_at_ms")
    require(observed is Number && observed.toLong() > 0)
    val presence = json.optJSONObject("presence")?.getJSONObject("expression")?.toString()?.also {
        val event = io.dawnlight.oscar.expression.Contract.parse(it)
        require(event != null && event.source.kind == io.dawnlight.oscar.expression.SourceKind.CORE && event.source.id.startsWith("presence:"))
    }
    val setup = json.optJSONObject("setup")?.let { root -> listOf("identity", "pairing", "provider", "persona", "preferences", "policy", "sentry", "voice").associateWith { section ->
        val item = root.getJSONObject(section)
        require(item.get("configured") is Boolean)
        require(!item.has("operational") || item.get("operational") is Boolean)
        require(!item.has("connected") || item.get("connected") is Boolean)
        when { item.optBoolean("operational", false) -> "Operational"; item.optBoolean("connected", false) -> "Connected"; item.getBoolean("configured") -> "Configured"; else -> "Setup needed" }
    } } ?: emptyMap()
    val adaptive = json.optJSONArray("adaptive_views")?.let { views -> require(views.length() <= 3); (0 until views.length()).mapNotNull { parseAdaptive(views.getJSONObject(it)) } } ?: emptyList()
    val executive = json.optJSONObject("executive")?.let { root -> require(root.get("version") == 1)
        val goals = root.getJSONArray("goals"); require(goals.length() <= 64)
        (0 until goals.length()).map { index -> val goal = goals.getJSONObject(index)
            val status = goal.bounded("state", 32); require(status in setOf("proposed", "enabled", "paused", "cancelled", "expired", "completed"))
            require(goal.get("verified_runs") is Int && goal.get("max_runs") is Int && goal.getInt("max_runs") in 1..100 && goal.getInt("verified_runs") in 0..goal.getInt("max_runs"))
            ExecutiveGoal(goal.bounded("id", 80), goal.bounded("goal", 512), status, goal.getInt("verified_runs"), goal.getInt("max_runs"))
        }
    }
    return CoreSnapshot(parsedTasks, parsedNodes, observed.toLong(), presence, setup, adaptive, executive)
}
