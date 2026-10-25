package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject

internal fun parseStartedResponsibility(root: JSONObject): String {
    require(root.keys().asSequence().toSet() == setOf("id", "mode", "state"))
    require(root.getString("mode") == "full" && root.getString("state") == "enabled")
    return root.bounded("id", 80).also { require(it.none(Char::isISOControl)) }
}

data class ManagedCapability(val id: String, val node: String, val session: String, val kind: String, val risk: String, val permissions: List<String>)
data class BriefSource(val id: String, val adapter: String, val state: String, val epistemic: String, val value: String?, val freshUntil: Double?, val epoch: Int, val accountId: String?, val accountGeneration: Int?)
data class TaskAttention(val sourceId: String, val taskId: String, val reason: String)
internal val taskAttentionLabels = mapOf("overdue" to "Overdue", "due_today" to "Due today", "high_importance" to "Reported high importance", "upcoming" to "Upcoming", "no_due_date" to "No due date", "due_unknown" to "Due date or time needs clarification")
data class DayBrief(val observedAt: Double, val sources: List<BriefSource>, val overlaps: Int, val incomplete: Boolean,
    val attention: List<TaskAttention> = emptyList(), val attentionIncomplete: Boolean = false, val unknownDueTimes: Int = 0,
    val attentionFreshUntil: Double? = null) {
    fun attentionLines(currentSources: Set<String>, nowSeconds: Double): List<String> {
        if (!nowSeconds.isFinite() || nowSeconds <= 0 || attentionFreshUntil?.let { nowSeconds < it } != true || sources.any { it.id !in currentSources }) return emptyList()
        return attention.mapNotNull { item ->
            val source = sources.find { it.id == item.sourceId && it.adapter == "connected_tasks" } ?: return@mapNotNull null
            val task = runCatching { JSONObject(source.value!!).objects("tasks", 8).find { it.getString("id") == item.taskId } }.getOrNull() ?: return@mapNotNull null
            "${task.optString("title", "Untitled task").take(1024)} · ${taskAttentionLabels[item.reason]}"
        }
    }
}
internal fun parseDayBrief(root: JSONObject): DayBrief {
    require(root.toString().toByteArray().size <= 50_000 && root.get("version") == 1)
    val observed = root.getDouble("observed_at"); require(observed.isFinite() && observed > 0)
    require(root.get("truncated") is Boolean)
    val sources = root.objects("sources", 8).map { source ->
        val value = if (source.isNull("value")) null else source.boundedText("value", 16_000)
        val evidence = source.objects("evidence", 64).map {
            it.bounded("id", 128)
            it.getDouble("fresh_until").also { time -> require(time.isFinite() && time > 0) }
        }
        val epoch = source.get("epoch"); require(epoch is Int && epoch >= 0)
        val account = if (source.isNull("account_id")) null else source.bounded("account_id", 128)
        val generation = if (account == null) null else source.getInt("account_generation").also { require(it > 0) }
        BriefSource(source.bounded("id", 128), source.bounded("adapter", 32), source.bounded("state", 32),
            source.bounded("epistemic", 32), value, evidence.minOrNull(), epoch, account, generation)
    }
    val schedule = root.getJSONObject("schedule")
    val overlaps = schedule.objects("overlaps", 16).size
    require(schedule.get("incomplete") is Boolean && schedule.get("truncated") is Boolean)
    val attention = root.optJSONObject("attention")
    val items = attention?.objects("tasks", 8)?.map {
        val reason = it.bounded("reason", 32); require(reason in taskAttentionLabels)
        val source = it.bounded("source_id", 128)
        require(sources.any { s -> s.id == source && s.adapter == "connected_tasks" })
        TaskAttention(source, it.bounded("task_id", 1024), reason)
    } ?: emptyList()
    require(items.map { it.sourceId to it.taskId }.toSet().size == items.size)
    val unknown = attention?.get("unknown_due_times") ?: 0
    require(unknown is Int && unknown in 0..64)
    if (attention != null) require(attention.get("incomplete") is Boolean && attention.get("truncated") is Boolean)
    val attentionExpiry = attention?.getDouble("fresh_until")?.also { require(it.isFinite() && it > 0) }
    return DayBrief(observed, sources, overlaps, root.getBoolean("truncated") || schedule.getBoolean("incomplete") || schedule.getBoolean("truncated"),
        items, attention?.let { it.getBoolean("incomplete") || it.getBoolean("truncated") } ?: false, unknown, attentionExpiry)
}
data class ManagementView(val relationship: String, val mode: String, val status: String, val expires: Long?, val epoch: Int,
    val capabilities: List<ManagedCapability>, val askRules: List<String>, val source: String)
data class ConnectionView(val source: String, val truncated: Boolean) {
    fun json() = JSONObject(source)
    fun accounts() = json().objects("accounts", 128)
    fun plugins() = json().objects("plugins", 128)
    fun providers() = json().objects("providers", 128)
}
internal fun JSONObject.objects(key: String, limit: Int): List<JSONObject> {
    val items = getJSONArray(key); require(items.length() <= limit)
    return (0 until items.length()).map { items.getJSONObject(it) }
}
internal fun JSONArray.texts(limit: Int, maxLength: Int = 256): List<String> {
    require(length() <= limit)
    return (0 until length()).map { get(it).also { value -> require(value is String && value.length in 1..maxLength) } as String }
}
/** Stable equality for signed JSON objects without depending on wire key order. */
internal fun canonicalJson(value: Any?): String = when (value) {
    null, JSONObject.NULL -> "null"
    is JSONObject -> value.keys().asSequence().toList().sorted().joinToString(",", "{", "}") { JSONObject.quote(it) + ":" + canonicalJson(value.get(it)) }
    is JSONArray -> (0 until value.length()).joinToString(",", "[", "]") { canonicalJson(value.get(it)) }
    is String -> JSONObject.quote(value)
    is Boolean, is Number -> value.toString()
    else -> error("Unsupported JSON value")
}
internal fun parseManagement(root: JSONObject): ManagementView? {
    require(root.get("version") == 1 && root.get("truncated") is Boolean)
    if (root.getBoolean("truncated")) return null
    val authority = root.getJSONObject("authority")
    val mode = authority.bounded("mode", 16); require(mode in setOf("ask", "secure", "full"))
    val status = authority.bounded("status", 16); require(status in setOf("active", "inactive"))
    require((mode == "ask") == (status == "inactive"))
    val epoch = authority.get("epoch"); require(epoch is Int && epoch >= 0)
    val expires = if (mode == "ask") null else authority.getLong("expires_at_ms").also { require(it > 0) }
    val caps = root.objects("capabilities", 256).map {
        ManagedCapability(it.bounded("id", 128), it.bounded("node_id", 80), it.bounded("session_id", 80),
            it.bounded("input_kind", 128), it.bounded("risk", 32), it.getJSONArray("permissions").texts(64))
    }
    require(caps.map { it.node + ":" + it.id }.distinct().size == caps.size)
    val sentry = root.getJSONObject("sentry")
    require(sentry.bounded("mode", 32) in setOf("manual", "trigger_only", "sentry") && sentry.bounded("state", 32) in setOf("passive", "aware", "guard", "away", "sleep"))
    require(sentry.get("allow_interrupt") is Boolean && sentry.get("generation") is Int && sentry.getInt("generation") >= 0)
    sentry.getJSONArray("source_ids").texts(32); sentry.getJSONArray("trigger_keys").texts(32)
    sentry.objects("sources", 64).forEach {
        it.bounded("id", 128); listOf("perceive", "retain", "act", "simulated").forEach { key -> require(it.get(key) is Boolean) }
        require(it.get("epoch") is Int && it.getInt("epoch") >= 0)
    }
    root.optJSONArray("procedures")?.let { procedures ->
        require(procedures.length() <= 64)
        (0 until procedures.length()).forEach { index ->
            val procedure = procedures.getJSONObject(index)
            listOf("id", "source_goal_id", "event_id").forEach { procedure.bounded(it, 128) }
            procedure.bounded("goal", 512)
            require(procedure.bounded("state", 32) in setOf("candidate", "exact_replay_verified"))
        }
    }
    root.optJSONArray("planner_drafts")?.let { drafts ->
        require(drafts.length() <= 64)
        (0 until drafts.length()).forEach { index ->
            val draft = drafts.getJSONObject(index)
            draft.bounded("id", 80); draft.bounded("goal", 480); draft.bounded("state", 32)
        }
    }
    root.optJSONObject("memory")?.let(::parseMemory)
    return ManagementView(root.bounded("relationship_id", 128), mode, status, expires, epoch, caps,
        root.getJSONArray("ask_rules").texts(256).sorted(), canonicalJson(root)).also {
            if (sentry.has("alerts")) parseSentryAlerts(it, root.getLong("observed_at_ms"))
        }
}
internal fun parseConnections(root: JSONObject): ConnectionView {
    require(root.toString().toByteArray().size <= 50_000 && root.get("truncated") is Boolean)
    root.getJSONObject("identity")
    root.objects("accounts", 128).forEach {
        listOf("id", "alias", "provider", "identity_class", "status").forEach { key -> it.bounded(key, 256) }
        require(it.get("generation") is Int && it.getInt("generation") >= 0)
        it.objects("services", 64).forEach { service -> service.bounded("id", 128); service.getJSONArray("scopes").texts(128) }
    }
    root.objects("plugins", 128).forEach {
        listOf("id", "name", "account_id", "health", "transport").forEach { key -> it.bounded(key, 256) }
        require(it.get("enabled") is Boolean)
        it.objects("tools", 200).forEach { tool -> tool.bounded("name", 256) }
        val permissions = it.getJSONObject("permissions"); require(permissions.length() <= 200)
        permissions.keys().forEach { key -> permissions.getJSONArray(key).texts(6) }
    }
    root.objects("providers", 128).forEach {
        listOf("id", "provider", "service").forEach { key -> it.bounded(key, 256) }; it.getJSONArray("scopes").texts(128)
    }
    return ConnectionView(canonicalJson(root), root.getBoolean("truncated"))
}
internal fun CoreSnapshot.managementStamp(): String = Approval.displayDigest(management?.source?.let { canonicalJson(JSONObject(it).apply { remove("observed_at_ms") }) } ?: "",
    connections?.source?.let { canonicalJson(JSONObject(it).apply { remove("observed_at_ms") }) } ?: "",
    executive.orEmpty().joinToString("\n") { "${it.id}:${it.state}:${it.runs}:${it.maxRuns}" })

internal fun delegationRequest(view: ManagementView, connections: ConnectionView, mode: String, lifetime: Int): JSONObject {
    require(mode in setOf("secure", "full") && lifetime in 60..28800 && !connections.truncated)
    return JSONObject().put("mode", mode).put("lifetime_seconds", lifetime)
        .put("capabilities", JSONArray(view.capabilities.map { JSONObject().put("node_id", it.node).put("session_id", it.session).put("capability_id", it.id) }))
        .put("account_ids", JSONArray(connections.accounts().filter { it.getString("status") == "connected" }.map { it.getString("id") }))
        .put("resolve_ask_rules", JSONArray(if (mode == "full") view.askRules else emptyList<String>()))
}
internal fun routineSchedule(start: String, interval: String, runs: String): JSONObject {
    val every = if (interval.isBlank()) null else interval.toInt().also { require(it in 60..31_536_000) }
    val maximum = runs.toInt().also { require(it in 1..100 && (every != null || it == 1)) }
    val at = if (start.isBlank()) null else java.time.LocalDateTime.parse(start).atZone(java.time.ZoneId.systemDefault()).toEpochSecond().also { require(it > 0) }
    return JSONObject().put("start_at", at ?: JSONObject.NULL).put("interval_seconds", every ?: JSONObject.NULL).put("max_runs", maximum).put("priority", 0)
}
internal fun fileRoutine(name: String, goal: String, path: String, content: String, cap: ManagedCapability, schedule: JSONObject): JSONObject {
    require(name.isNotBlank() && name.length <= 80 && goal.isNotBlank() && goal.length <= 512 && path.isNotBlank() && path.length <= 1024 && content.length <= 8192 && cap.kind == "file_write")
    val value = JSONObject(schedule.toString()).put("name", name).put("goal", goal).put("conditions", JSONArray())
        .put("steps", JSONArray().put(JSONObject().put("id", "write").put("node_id", cap.node).put("capability_id", cap.id).put("depends_on", JSONArray())
            .put("intent", JSONObject().put("text", goal).put("kind", "file_write").put("path", path).put("content", content))))
    return JSONObject().put("operation", "create").put("id", "new").put("value", value).also { require(it.toString().toByteArray().size <= 16_000) }
}

internal fun planningRoutine(name: String, goal: String, mode: String, caps: List<ManagedCapability>): JSONObject {
    require(name.matches(Regex("[A-Za-z0-9 _-]{1,64}")) && goal.length in 1..480)
    require(mode in setOf("private", "auto") && caps.size in 2..16)
    require(caps.count { it.kind == "model_reasoning" } == 1 && caps.map { it.node to it.id }.distinct().size == caps.size)
    return JSONObject().put("operation", "plan_draft").put("id", "new").put("value", JSONObject()
        .put("name", name).put("goal", goal).put("mode", mode)
        .put("capabilities", JSONArray(caps.map { JSONObject().put("node_id", it.node).put("capability_id", it.id) })))
}
