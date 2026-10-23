package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import org.json.JSONObject

internal data class SavedMemory(val id: String, val content: String, val digest: String, val status: String,
    val sources: Int, val excerpt: Boolean, val canManage: Boolean, val canCorrect: Boolean)
internal data class MemoryReadback(val available: Boolean, val records: List<SavedMemory>, val truncated: Boolean)
internal fun parseMemory(root: JSONObject): MemoryReadback {
    require(root.toString().toByteArray().size <= 12_000)
    require(root.get("available") is Boolean && root.get("truncated") is Boolean)
    if (root.getBoolean("available")) require(root.get("generation") is Int && root.getInt("generation") >= 0)
    val records = root.objects("records", 20).map {
        listOf("excerpt", "can_manage", "can_correct").forEach { key -> require(it.get(key) is Boolean) }
        val digest = it.bounded("digest", 64); require(digest.matches(Regex("[a-f0-9]{64}")))
        it.bounded("kind", 128)
        SavedMemory(it.bounded("id", 128), it.boundedText("content", 2000), digest, it.bounded("status", 32),
            it.getJSONArray("source_event_ids").texts(32, 128).size, it.getBoolean("excerpt"),
            it.getBoolean("can_manage"), it.getBoolean("can_correct"))
    }
    require(root.getBoolean("available") || records.isEmpty())
    require(records.map { it.id }.distinct().size == records.size)
    return MemoryReadback(root.getBoolean("available"), records, root.getBoolean("truncated"))
}

@Composable fun MemoryScreen(session: CoreSession, state: MobileState) {
    val view = state.snapshot?.management?.source?.let { JSONObject(it).optJSONObject("memory") }?.let(::parseMemory)
    IllustratedIntro("Memory", artwork = R.drawable.illustration_reading)
    Text("Saved statements come from your Core. Corrections preserve the earlier statement as history. Forgetting removes a memory from recall.", style = MaterialTheme.typography.bodyMedium)
    if (view?.available == true) {
        view.records.forEach { memory -> key(memory.id, memory.digest) {
            var correction by remember { mutableStateOf("") }
            var retain by remember { mutableStateOf(false) }
            var sources by remember { mutableStateOf(false) }
            SupportingDetails(memory.content.take(80) + if (memory.content.length > 80) "…" else "") {
                Text(memory.content + if (memory.excerpt) "…" else "")
                Text("${memory.status} · ${memory.sources} retained source statements", style = MaterialTheme.typography.bodySmall)
                if (memory.canManage) {
                    Row { Checkbox(checked = sources, onCheckedChange = { sources = it }); Text("Also forget retained sources and dependent memories") }
                    Text("Keeping sources leaves the original conversation available. Backups and physical storage are not securely erased.", style = MaterialTheme.typography.bodySmall)
                    OscarButton(onClick = { reviewChange(session, "assistance", change("memory_forget", memory.id,
                        JSONObject().put("digest", memory.digest).put("forget_sources", sources))) }, enabled = state.canManage(), modifier = Modifier.fillMaxWidth()) { Text("Review forgetting this memory") }
                    if (memory.canCorrect) {
                        OscarField(correction, { correction = it.take(2000) }, label = "Corrected statement", modifier = Modifier.fillMaxWidth())
                        Row { Checkbox(checked = retain, onCheckedChange = { retain = it }); Text("Retain this exact correction") }
                        OscarButton(onClick = { reviewChange(session, "assistance", change("memory_correct", memory.id,
                            JSONObject().put("digest", memory.digest).put("content", correction).put("retain", true))) },
                            enabled = state.canManage() && retain && correction.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text("Review memory correction") }
                    } else Text("Corrections need a separate retention grant.", style = MaterialTheme.typography.bodySmall)
                } else Text("Memory changes need a separate owner management grant.")
            }
        } }
        if (view.records.isEmpty()) Text("No current saved memories were found in this bounded view.")
        if (view.truncated) Text("Showing the most recent memories within this display limit.")
    } else Text("Saved memory needs a connected Core with a separate memory read grant.")
    TextButton(onClick = session::refreshNow, enabled = !state.busy) { Text("Refresh saved memory") }
    SupportingDetails("On this phone") { Text("Unsent drafts use encrypted recovery. Clearing local drafts does not forget Core memory.", style = MaterialTheme.typography.bodySmall) }
}
