package io.dawnlight.oscar.mobile

import org.json.JSONArray
import org.json.JSONObject

/** A bounded presentation cache; every task/node projection is replaced by fresh Core state. */
internal data class GridEvent(val id: String, val sequence: Long, val turn: String, val task: String?, val speaker: String, val text: String)
internal class GridHistory {
    var cursor = 0L; private set
    var generation = ""; private set
    private var events = emptyList<GridEvent>()

    fun clear() { cursor = 0; generation = ""; events = emptyList() }
    fun request() = JSONObject().put("cursor", cursor).put("archive_generation", generation)
    fun merge(json: JSONObject): List<Interaction> {
        require(json.get("reset") is Boolean)
        val reset = json.getBoolean("reset")
        val nextGeneration = json.bounded("archive_generation", 128)
        require(reset || generation.isEmpty() || nextGeneration == generation)
        val nextCursor = json.get("cursor").also { require((it is Long || it is Int) && (it as Number).toLong() >= 0) } as Number
        val incoming = decode(json.getJSONArray("events"), 100)
        require(incoming.zipWithNext().all { (a, b) -> a.sequence < b.sequence })
        require(incoming.all { it.sequence <= nextCursor.toLong() })
        require(reset || nextCursor.toLong() >= cursor)
        val previous = if (reset) emptyList() else events
        incoming.forEach { event -> previous.find { it.id == event.id }?.let { require(it == event) } }
        val merged = (previous + incoming).distinctBy { it.id }.sortedBy { it.sequence }
        require(merged.map { it.sequence }.distinct().size == merged.size)
        events = merged.takeLast(100); cursor = nextCursor.toLong(); generation = nextGeneration
        while (saved().toString().toByteArray(Charsets.UTF_8).size > 196608) events = events.drop(1)
        return interactions()
    }
    fun interactions(): List<Interaction> = events.groupBy { it.turn }.values.mapNotNull { turn ->
        val owner = turn.firstOrNull { it.speaker == "owner" } ?: return@mapNotNull null
        val replies = turn.filter { it.speaker == "oscar" }.joinToString("\n") { it.text }
        Interaction(owner.text, replies.ifEmpty { "Awaiting Core response" }, owner.task)
    }
    fun saved(): JSONObject = JSONObject().put("cursor", cursor).put("archive_generation", generation)
        .put("events", JSONArray(events.map { event -> JSONObject().put("event_id", event.id).put("sequence", event.sequence)
            .put("turn_id", event.turn).put("task_id", event.task ?: JSONObject.NULL).put("speaker", event.speaker).put("text", event.text) }))
    fun restore(json: JSONObject) {
        val restored = decode(json.getJSONArray("events"), 100)
        require(restored.zipWithNext().all { (a, b) -> a.sequence < b.sequence })
        val restoredCursor = json.getLong("cursor"); require(restoredCursor >= 0 && restored.all { it.sequence <= restoredCursor })
        cursor = restoredCursor; generation = json.bounded("archive_generation", 128); events = restored
    }
    private fun decode(array: JSONArray, max: Int): List<GridEvent> {
        require(array.length() <= max)
        return (0 until array.length()).map { index ->
            val item = array.getJSONObject(index)
            val sequence = item.get("sequence"); require((sequence is Long || sequence is Int) && (sequence as Number).toLong() > 0)
            val speaker = item.bounded("speaker", 16); require(speaker in setOf("owner", "oscar"))
            GridEvent(item.bounded("event_id", 128), (sequence as Number).toLong(), item.bounded("turn_id", 128),
                if (item.isNull("task_id")) null else item.bounded("task_id", 80), speaker, item.boundedText("text", 64000))
        }.also { require(it.map { event -> event.id }.distinct().size == it.size) }
    }
}

internal fun parseGridTask(item: JSONObject, nodes: List<CoreNode>): CoreTask {
    val taskId = item.bounded("task_id", 80)
    val correlation = item.bounded("correlation_id", 80)
    val action = item.bounded("action_id", 80)
    val target = item.bounded("target", 80)
    val status = nodes.find { it.id == target }?.status ?: "offline"
    val state = item.bounded("state", 32)
    require(item.get("retained_available") is Boolean)
    val retained = item.getBoolean("retained_available")
    val evidence = item.getJSONArray("evidence"); require(evidence.length() <= 100)
    require(retained || evidence.length() == 0 && item.isNull("result") && !item.getBoolean("approval_required"))
    val ids = JSONArray()
    var verified = false
    for (index in 0 until evidence.length()) {
        val receipt = evidence.getJSONObject(index)
        require(receipt.bounded("task_id", 80) == taskId)
        require(receipt.bounded("correlation_id", 80) == correlation)
        require(receipt.isNull("matches") || receipt.get("matches") is Boolean)
        val epistemic = receipt.bounded("status", 32); require(epistemic in setOf("VERIFIED", "REPORTED", "UNKNOWN", "INFERRED", "KNOWN", "RECALLED"))
        ids.put(receipt.bounded("id", 80))
        if (epistemic == "VERIFIED" && receipt.optBoolean("matches", false)) verified = true
    }
    require(state != "verified" || !retained || verified)
    require(item.get("approval_required") is Boolean)
    val actions = JSONArray()
    if (state == "planned" && item.getBoolean("approval_required") && status == "online") actions.put("approve")
    if (state !in setOf("verified", "failed", "cancelled")) actions.put("cancel")
    val normalized = JSONObject().put("task_id", taskId).put("description", item.bounded("description", 8192).take(256))
        .put("state", if (state == "verified" && !retained) "unknown" else state).put("target", target).put("node_status", status).put("generation", item.get("generation"))
        .put("actions", actions).put("evidence_ids", ids)
        .put("blocker", if (!retained) "Retained result and verification proof unavailable" else item.opt("blocker") ?: JSONObject.NULL)
    item.optJSONObject("result")?.let { result ->
        require(result.bounded("task_id", 80) == taskId && result.bounded("status", 32) == "REPORTED" && result.get("success") is Boolean)
        require(result.bounded("action_id", 80) == action && result.bounded("correlation_id", 80) == correlation)
        require(state != "verified" || result.getBoolean("success"))
        if (!result.isNull("value")) {
            val value = result.boundedText("value", 8192)
            if (state == "verified") normalized.put("value", value)
            else normalized.put("response", value).put("response_status", "REPORTED")
        }
    }
    val digest = item.bounded("review_digest", 64).also { require(it.matches(Regex("[a-f0-9]{64}"))) }
    return parseTask(normalized).copy(reviewDigest = digest, capability = item.bounded("capability", 128))
}

internal fun parseGridSnapshot(json: JSONObject, expectedCore: String, expectedNode: String): CoreSnapshot {
    require(json.get("version") == 2 && json.bounded("core_id", 80) == expectedCore && json.bounded("node_id", 80) == expectedNode)
    json.bounded("relationship_id", 128)
    val basic = parseSnapshot(JSONObject().put("tasks", JSONArray()).put("nodes", json.getJSONArray("nodes")).put("observed_at_ms", json.get("observed_at_ms")))
    val tasks = json.getJSONArray("tasks"); require(tasks.length() <= 100)
    val parsed = (0 until tasks.length()).map { parseGridTask(tasks.getJSONObject(it), basic.nodes) }
    require(parsed.map { it.id }.distinct().size == parsed.size)
    return basic.copy(tasks = parsed)
}

internal fun reconnectDelay(failures: Int, jitter: Long): Long =
    (5_000L * (1L shl failures.coerceIn(0, 4))).coerceAtMost(60_000) + jitter.coerceIn(0, 1_000)
