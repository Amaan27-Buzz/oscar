package io.dawnlight.oscar.mobile

import org.json.JSONObject

enum class Destination(val label: String) { OSCAR("OSCAR"), ACTIVITY("Activity"), DEVICES("Devices"), SETTINGS("Settings") }
enum class Presence { IDLE, ATTENTIVE, LISTENING, THINKING, SPEAKING, WAITING, MUTED, UNAVAILABLE, ERROR }
enum class Link { DISCONNECTED, CONNECTING, CONNECTED, DEGRADED }

data class CoreTask(
    val id: String, val description: String, val state: String, val target: String,
    val nodeStatus: String, val generation: Int, val actions: List<String>,
    val evidence: List<String>, val value: String?, val blocker: String?,
    val response: String? = null,
    val responseTruncated: Boolean = false,
) {
    val label: String get() = when (state) {
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
data class CoreNode(val id: String, val role: String, val status: String, val paired: Boolean, val capabilities: List<String>)
data class CoreSnapshot(val tasks: List<CoreTask>, val nodes: List<CoreNode>, val observedAt: Long)
data class Interaction(val text: String, val response: String, val taskId: String? = null)
data class Approval(
    val id: String, val signingPayload: String, val expiresAt: Long, val operation: String,
    val description: String, val target: String, val capability: String, val reason: String,
    val consequence: String, val policyReason: String,
) {
    fun material(): JSONObject = JSONObject(String(java.util.Base64.getDecoder().decode(signingPayload), Charsets.UTF_8)).getJSONObject("material")
    fun acceptsPermit(permit: JSONObject): Boolean = operation == "reply" &&
        listOf("package", "key_hash", "text_hash").all { permit.get(it) is String && permit.getString(it) == material().getString(it) } && permit.getString("id") == id
    companion object {
        fun parse(json: JSONObject): Approval {
            require(json.getString("confirmation") == "biometric_or_device_credential")
            val payload = json.bounded("signing_payload", 16000)
            // The Core signs the exact bytes. UI fields are validated, never substituted into them.
            val claim = JSONObject(String(java.util.Base64.getDecoder().decode(payload), Charsets.UTF_8))
            require(claim.getInt("version") == 1 && claim.getLong("expires_at_ms") == json.getLong("expires_at_ms"))
            require(claim.getString("operation") == json.getString("operation"))
            require(json.getString("operation") in setOf("approve", "deny", "cancel", "retry", "reply"))
            val material = claim.getJSONObject("material")
            require((if (json.getString("operation") == "reply") material.getString("package") else material.getString("target")) == json.getString("target"))
            return Approval(json.bounded("challenge_id", 80), payload, json.getLong("expires_at_ms"),
                json.bounded("operation", 16), json.bounded("description", 256), json.bounded("target", 256),
                json.bounded("capability", 80), json.bounded("reason", 256), json.bounded("consequence", 256),
                json.bounded("policy_reason", 256))
        }
    }
}
data class MobileState(
    val epoch: Long = 0, val link: Link = Link.DISCONNECTED, val busy: Boolean = false,
    val snapshot: CoreSnapshot? = null, val interactions: List<Interaction> = emptyList(),
    val approval: Approval? = null, val message: String? = null,
    val observedAt: Long = 0,
    val draft: String = "", val inspected: CoreTask? = null, val privateSuppressed: Boolean = false,
    val restoring: Boolean = false,
) {
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
        snapshot = null, approval = null, inspected = null, interactions = emptyList(), observedAt = 0, restoring = false, message = message)
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
    return CoreTask(json.bounded("task_id", 80), json.bounded("description", 256), state,
        json.bounded("target", 80), status, generation, if (status == "online") actions else actions.filter { it in setOf("cancel", "deny") },
        evidence, value, blocker, response, json.optBoolean("response_truncated", false))
}
fun CoreSnapshot.withoutPrivate() = copy(tasks = tasks.map { it.copy(description = "Private request hidden", response = null, value = null,
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
    return CoreSnapshot(parsedTasks, parsedNodes, observed.toLong())
}
