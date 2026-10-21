package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

internal fun JSONObject.keysSet(): Set<String> = keys().asSequence().toSet()

/** Exact authenticated Grid delivery, shared with the Core's Android task validator. */
internal data class NativeGridDelivery(val id: String, val kind: String, val action: JSONObject, val parameters: JSONObject,
    val taskId: String, val nodeId: String, val sessionId: String, val deadline: Long, val taskGeneration: Long, val authorityEpoch: Long,
    val authority: JSONObject?) {
    fun checkRequest(): JSONObject = JSONObject().put("delivery_id", id).also { if (authority != null) it.put("authority", authority) }
    fun acceptsCheck(response: JSONObject): Boolean = response.getBoolean("authorized") &&
        response.keysSet().all { it in setOf("authorized", "authority") } && canonical(response.optJSONObject("authority")) == canonical(authority)
    fun native(generation: String, elapsed: Long, wall: Long): NativeAction = NativeAction(id, taskId, nodeId, sessionId,
        taskGeneration, authorityEpoch, generation, elapsed + (deadline - wall).coerceAtMost(60_000),
        if (kind == "readback") nativeReadbackCapability(action.getString("capability_id")) else action.getString("capability_id"),
        parameters.getString("package"), parameters.getString("target"), parameters.getString("value"))

    fun receipt(result: NativeResult): JSONObject {
        val observations = JSONArray(result.observations.map { item -> JSONObject().put("resource_id", item.resourceId)
            .put("text", item.text).put("clickable", item.clickable).put("editable", item.editable) })
        val contentObject = JSONObject().put("package", parameters.getString("package")).put("observations", observations)
        while (contentObject.toString().toByteArray(Charsets.UTF_8).size > 8192 && observations.length() > 0) observations.remove(observations.length() - 1)
        val content = contentObject.toString()
        if (kind == "readback") { require(result.state == "reported"); return JSONObject().put("content", content) }
        return JSONObject().put("id", java.util.UUID.randomUUID().toString()).put("action_id", action.getString("id"))
            .put("task_id", taskId).put("correlation_id", action.getString("correlation_id"))
            .put("executor", action.getString("capability_id")).put("success", result.state == "reported")
            .put("value", if (result.state == "reported") content else JSONObject.NULL)
            .put("error", if (result.state == "reported") JSONObject.NULL else result.detail.take(256))
            .put("status", "REPORTED").put("artifact", JSONObject.NULL)
    }

    companion object {
        fun parse(value: JSONObject, node: String, session: String, workspace: String, wall: Long): NativeGridDelivery {
            val required = setOf("id", "kind", "node_id", "session_id", "task_id", "lease_id", "action", "deadline_ms", "workspace", "review_digest", "approved", "parameters")
            require(value.keysSet().containsAll(required) && (value.keysSet() - required).all { it in setOf("authority", "task_generation", "authority_epoch") })
            require(value.getString("node_id") == node && value.getString("session_id") == session && value.getString("workspace") == workspace)
            require(value.getString("kind") in setOf("action", "readback") && value.get("approved") is Boolean)
            val deadline = value.getLong("deadline_ms")
            // Grid request proofs permit 60s clock skew; Core still checks expiry before every effect.
            require(deadline > wall && deadline - wall <= 180_000)
            val action = value.getJSONObject("action")
            require(action.keysSet() == setOf("id", "task_id", "correlation_id", "capability_id", "parameters", "idempotency_key", "initiator"))
            require(action.getString("task_id") == value.getString("task_id") && action.getString("capability_id") in nativeCapabilityIds)
            listOf(value.getString("id"), value.getString("task_id"), value.getString("lease_id"), action.getString("id"), action.getString("correlation_id"), action.getString("idempotency_key"), action.getString("initiator")).forEach {
                require(it.matches(Regex("[A-Za-z0-9_-]{1,128}")))
            }
            val exact = action.getJSONObject("parameters")
            validateNativeParameters(action.getString("capability_id"), exact)
            val parameters = value.getJSONObject("parameters")
            if (value.getString("kind") == "readback") {
                require(parameters.keysSet() == setOf("package", "target", "value") && parameters.getString("package") == exact.getString("package") &&
                    parameters.getString("target") == (if (action.getString("capability_id").startsWith("android.files.")) exact.getString("target") else "") && parameters.getString("value").isEmpty())
                validateNativeParameters(nativeReadbackCapability(action.getString("capability_id")), parameters)
            } else require(canonical(parameters) == canonical(exact))
            val review = JSONObject().put("action", action).put("target", node).put("workspace", workspace).put("deadline_ms", deadline)
            val digest = MessageDigest.getInstance("SHA-256").digest(canonical(review).toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it.toInt() and 255) }
            require(value.getString("review_digest") == digest)
            val authority = value.optJSONObject("authority")
            val generation = authority?.getLong("task_generation") ?: value.optLong("task_generation", 0)
            val epoch = authority?.getLong("epoch") ?: value.optLong("authority_epoch", 0)
            require(generation >= 0 && epoch >= 0)
            if (authority != null) require(authority.getLong("expires_at_ms") > wall)
            return NativeGridDelivery(value.getString("id"), value.getString("kind"), action, parameters,
                value.getString("task_id"), node, session, if (authority == null) deadline else minOf(deadline, authority.getLong("expires_at_ms")), generation, epoch, authority)
        }
    }
}

internal fun validateNativeParameters(capability: String, parameters: JSONObject) {
    require(parameters.keysSet() == setOf("package", "target", "value") && parameters.keysSet().all { parameters.get(it) is String })
    val pkg = parameters.getString("package"); val target = parameters.getString("target"); val value = parameters.getString("value")
    require(pkg.length <= 256 && pkg.matches(Regex("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) && target.length <= 512 && value.length <= 2000 && listOf(pkg, target, value).none { '\u0000' in it })
    require(capability in nativeCapabilityIds)
    if (capability == "android.ui.inspect") require(target.isEmpty() && value.isEmpty())
    else if (capability.startsWith("android.ui.")) require(target.startsWith("$pkg:id/") && target.length > pkg.length + 4)
    else if (capability.startsWith("android.files.")) require(target.matches(Regex("[A-Za-z0-9][A-Za-z0-9 ._-]{0,120}\\.(txt|md|json|csv|log)")) && ".." !in target)
    else if (capability.startsWith("android.clipboard.") || capability.startsWith("android.media.") || capability == "android.screen.capture") require(target.isEmpty())
    else require(target.startsWith("$pkg."))
    when (capability) {
        "android.app.launch", "android.ui.click" -> require(value.isEmpty())
        "android.ui.scroll" -> require(value in setOf("forward", "backward"))
        "android.ui.gesture" -> require(value in setOf("up", "down", "left", "right"))
        "android.files.read", "android.clipboard.read", "android.media.inspect", "android.screen.capture" -> require(value.isEmpty())
        "android.media.control" -> require(value in setOf("play", "pause", "next", "previous", "stop"))
        "android.link.open" -> { val uri = java.net.URI(value); require(uri.scheme == "https" && !uri.host.isNullOrBlank() && uri.userInfo == null) }
        "android.phone.dial" -> require(value.matches(Regex("\\+?[0-9 ()-]{1,40}")))
        "android.contact.view" -> require(value.matches(Regex("[0-9]{1,20}")) && value.toLongOrNull() != null)
        "android.message.compose" -> {
            val draft = JSONObject(value)
            require(draft.keysSet() == setOf("number", "text") && draft.get("number") is String && draft.get("text") is String &&
                draft.getString("number").matches(Regex("\\+?[0-9 ()-]{1,40}")) && draft.getString("text").length <= 1000)
        }
        "android.calendar.insert" -> {
            val draft = JSONObject(value)
            require(draft.keysSet() == setOf("title", "begin_ms", "end_ms") && draft.get("title") is String && draft.getString("title").length in 1..300 &&
                (draft.get("begin_ms") is Long || draft.get("begin_ms") is Int) && (draft.get("end_ms") is Long || draft.get("end_ms") is Int) &&
                draft.getLong("begin_ms") > 0 && draft.getLong("begin_ms") < draft.getLong("end_ms") && draft.getLong("end_ms") < 4_102_444_800_000L)
        }
        "android.settings.open" -> require(value in setOf("wifi", "bluetooth", "sound", "display", "application"))
    }
}

internal fun nativeReadbackCapability(id: String): String = when {
    id.startsWith("android.files.") -> "android.files.read"
    id.startsWith("android.clipboard.") -> "android.clipboard.read"
    id.startsWith("android.media.") -> "android.media.inspect"
    id == "android.screen.capture" -> id
    else -> "android.ui.inspect"
}

/** Python fingerprint's sorted, ASCII JSON format; no locale, floating-point or key-order drift. */
internal fun canonical(value: Any?): String = when (value) {
    null, JSONObject.NULL -> "null"
    is JSONObject -> value.keysSet().sorted().joinToString(",", "{", "}") { canonical(it) + ":" + canonical(value.get(it)) }
    is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonical(value.get(it)) }
    is String -> buildString {
        append('"'); value.forEach { c -> when (c) {
            '"' -> append("\\\""); '\\' -> append("\\\\"); '\b' -> append("\\b"); '\u000c' -> append("\\f")
            '\n' -> append("\\n"); '\r' -> append("\\r"); '\t' -> append("\\t")
            else -> if (c.code < 32 || c.code > 126) append("\\u%04x".format(c.code)) else append(c)
        } }; append('"')
    }
    is Boolean, is Int, is Long -> value.toString()
    else -> throw IllegalArgumentException("Unsupported review material")
}
