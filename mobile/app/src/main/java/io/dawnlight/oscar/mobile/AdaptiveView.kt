package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.*
import kotlinx.coroutines.delay
import org.json.JSONObject

data class AdaptiveDescriptor(val taskId: String, val revision: Long, val observedAt: Long, val expiresAt: Long, val fallback: String, val texts: List<String>)
fun parseAdaptive(value: JSONObject): AdaptiveDescriptor? = try {
    require(value.keys().asSequence().toSet() == setOf("version", "view_id", "task_id", "revision", "observed_at_ms", "expires_at_ms", "fallback", "components", "actions"))
    require(value.get("version") == 1 && value.toString().length <= 8192)
    value.bounded("view_id", 80)
    val task = value.bounded("task_id", 80)
    fun integer(key: String): Long { val v = value.get(key); require(v is Number && v.toDouble().isFinite() && v.toDouble() >= 0 && v.toDouble() % 1.0 == 0.0 && v.toDouble() <= 9007199254740991.0); return v.toLong() }
    val revision = integer("revision"); val observed = integer("observed_at_ms"); val expires = integer("expires_at_ms")
    require(expires - observed in 1..30_000)
    val components = value.getJSONArray("components"); require(components.length() in 1..8)
    val texts = (0 until components.length()).map { i -> val c = components.getJSONObject(i)
        require(c.keys().asSequence().toSet() == setOf("type", "text", "source_ids"))
        require(c.getString("type") in setOf("prose", "task_progress", "result_evidence"))
        val refs = c.getJSONArray("source_ids"); require(refs.length() <= 20)
        (0 until refs.length()).forEach { require(refs.get(it) is String && refs.getString(it).length in 1..80) }
        c.bounded("text", 1024)
    }
    val actions = value.getJSONArray("actions"); require(actions.length() == 1)
    val action = actions.getJSONObject(0)
    require(action.keys().asSequence().toSet() == setOf("type", "task_id") && action.getString("type") == "inspect_task" && action.getString("task_id") == task)
    AdaptiveDescriptor(task, revision, observed, expires, value.bounded("fallback", 512), texts)
} catch (_: Exception) { null }

@Composable fun AdaptiveTask(view: AdaptiveDescriptor, inspect: () -> Unit) {
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(view) { while (true) { now = System.currentTimeMillis(); delay(1000) } }
    val fresh = view.observedAt <= now + 250 && view.expiresAt > now
    Column {
        if (fresh) view.texts.forEach { Text(it) } else Text("Details expired. Refresh for current state.")
        TextButton(onClick = inspect, enabled = fresh) { Text("Inspect task") }
    }
}
