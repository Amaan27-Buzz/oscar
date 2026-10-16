package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

@Composable fun ActivityScreen(state: MobileState, inspect: (String) -> Unit, review: (CoreTask, String) -> Unit) {
    var filter by remember(state.epoch) { mutableStateOf("Active") }
    EditorialHeading("Activity", "Ongoing work")
    if (state.snapshot == null) { Text("Connect Core to see your activity."); return }
    val completed = setOf("verified", "partially_verified", "failed", "cancelled")
    ActivityFilters(filter) { filter = it }
    val tasks = state.snapshot.tasks.filter { (it.state in completed) == (filter == "Finished") }
    if (tasks.isEmpty()) IllustratedIntro(
        if (filter == "Active") "Nothing is waiting here." else "No finished tasks in this connection.",
        artwork = R.drawable.illustration_empty, height = 112.dp)
    tasks.forEachIndexed { index, task ->
        val tone = taskColor(task)
        Row(Modifier.fillMaxWidth().height(IntrinsicSize.Min), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            Column(Modifier.width(40.dp).fillMaxHeight(), horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(10.dp)) {
                IconBadge(when (task.state) { "verified" -> "Check"; "failed", "blocked" -> "Close"; "cancelled" -> "Pause"; "planned" -> "Access"; else -> "Activity" }, tone, 40.dp)
                if (index < tasks.lastIndex) Box(Modifier.width(1.dp).weight(1f).background(MaterialTheme.colorScheme.outlineVariant))
            }
            Column(Modifier.weight(1f).padding(bottom = 24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("task-description-${task.id}")
                    .clickable(enabled = !state.busy && state.link == Link.CONNECTED, role = Role.Button) { inspect(task.id) }
                    .semantics { liveRegion = LiveRegionMode.Polite }, verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(task.description, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                    Glyph("Next", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                StatusPill(task.label, tone)
                Text(task.target, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                task.progress?.let { Text("${if (it.current) "Worker checkpoint" else "Previous checkpoint"}: ${(it.fraction * 100).toInt()}% · ${it.step} · REPORTED", style = MaterialTheme.typography.bodyMedium) }
                task.blocker?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
                FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    task.actions.forEach { action ->
                        OscarButton(onClick = { review(task, action) }, enabled = !state.busy && state.link == Link.CONNECTED,
                            color = if (action in setOf("deny", "cancel")) Clay else Sage, outlined = action != "approve") {
                            Text(when (action) { "approve" -> "Review request"; "deny" -> "Deny request"; "cancel" -> "Review cancellation"; else -> "Review continuation" })
                        }
                    }
                }
            }
        }
    }
}

private fun taskColor(task: CoreTask): Color = when {
    task.nodeStatus != "online" && task.state in setOf("executing", "awaiting_result", "result_received", "verifying") -> Amber
    task.state == "verified" -> Sage
    task.state in setOf("failed", "blocked") -> Clay
    task.state in setOf("planned", "partially_verified", "unknown") -> Amber
    task.state == "cancelled" -> Color(0xFF77766B)
    else -> Color(0xFF1769C4)
}

@Composable fun TaskInspector(task: CoreTask, close: () -> Unit, review: ((CoreTask, String) -> Unit)? = null, controlsAvailable: Boolean = false) {
    DetailPage("Task", close, "taskInspector") {
        IllustratedIntro(task.description, artwork = R.drawable.illustration_task, height = 96.dp)
        StatusPill(task.label, taskColor(task))
        if (controlsAvailable && review != null) FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            task.actions.forEach { action -> OscarButton(onClick = { review(task, action) },
                color = if (action in setOf("deny", "cancel")) Clay else Sage, outlined = action != "approve") {
                Text(when (action) { "approve" -> "Review request"; "cancel" -> "Review cancellation"; "deny" -> "Deny request"; else -> "Review continuation" })
            } }
        }
        SelectionContainer {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    IconBadge("Devices", Powder, 32.dp)
                    Text("${task.target} · ${task.nodeStatus}", style = MaterialTheme.typography.bodyMedium)
                }
                task.progress?.let { Text("${if (it.current) "Worker checkpoint" else "Previous checkpoint"}: ${(it.fraction * 100).toInt()}% · ${it.step}\nREPORTED; progress is not verification.") }
                task.blocker?.let { Text(it) }
                task.value?.let { TactileSurface(Modifier.fillMaxWidth()) { Text("Verified result: $it", style = MaterialTheme.typography.titleLarge) } }
                task.response?.let { StatusLabel("Reported response"); ResponseText(it) }
                if (task.responseTruncated) Text("Core supplied a bounded excerpt.")
                SupportingDetails("Evidence & task details") {
                    Text("Ownership: ${task.ownership}\nGeneration: ${task.generation}")
                    Text(if (task.evidence.isEmpty()) "No independent evidence references are available." else "Evidence references: ${task.evidence.joinToString(", ")}")
                    task.artifacts.forEach { Text("Artifact ${it.id}\n${it.kind} · ${it.status}\n${it.hash ?: "Hash unavailable"}") }
                    if (task.artifacts.isEmpty()) Text("No artifact summary available to this session.")
                    Text("Reported text is not independent verification. Continuation requires fresh approval.")
                }
            }
        }
    }
}
