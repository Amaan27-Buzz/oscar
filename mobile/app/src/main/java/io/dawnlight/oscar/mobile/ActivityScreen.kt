package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

@Composable fun ActivityScreen(state: MobileState, inspect: (String) -> Unit, review: (CoreTask, String) -> Unit) {
    var filter by remember(state.epoch) { mutableStateOf("Active") }
    EditorialHeading("Activity")
    Text("Ongoing work", style = MaterialTheme.typography.bodySmall)
    if (state.snapshot == null) { Text("Connect Core to see your activity."); return }
    val completed = setOf("verified", "partially_verified", "failed", "cancelled")
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf("Active", "Finished").forEach { name ->
            FilterChip(selected = filter == name, onClick = { filter = name }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Sage, selectedLabelColor = androidx.compose.ui.graphics.Color.White), label = { Text(name) })
        }
    }
    val tasks = state.snapshot.tasks.filter { (it.state in completed) == (filter == "Finished") }
    if (tasks.isEmpty()) Text(if (filter == "Active") "Nothing is waiting here." else "No finished tasks in this connection.")
    tasks.forEach { task ->
        TactileSurface(Modifier.fillMaxWidth()) {
        FeatureRow(task.description, "${task.label} · ${task.target}", "Activity", action = { if (!state.busy && state.link == Link.CONNECTED) inspect(task.id) },
            modifier = Modifier.testTag("task-description-${task.id}").semantics { liveRegion = LiveRegionMode.Polite })
        task.progress?.let { Text("${if (it.current) "Worker checkpoint" else "Previous checkpoint"}: ${(it.fraction * 100).toInt()}% · ${it.step} · REPORTED", style = MaterialTheme.typography.bodyMedium) }
        task.blocker?.let { Text(it) }
        FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            if ("approve" in task.actions) TextButton(onClick = { review(task, "approve") }, enabled = !state.busy && state.link == Link.CONNECTED) { Text("Review request") }
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            task.actions.filter { it != "approve" }.forEach { action ->
                TextButton(onClick = { review(task, action) }, enabled = !state.busy && state.link == Link.CONNECTED) {
                    Text(when (action) { "deny" -> "Deny request"; "cancel" -> "Review cancellation"; else -> "Review continuation" })
                }
            }
        }
        }
    }
}

@Composable fun TaskInspector(task: CoreTask, close: () -> Unit, review: ((CoreTask, String) -> Unit)? = null, controlsAvailable: Boolean = false) {
    DetailPage("Task", close, "taskInspector") {
        Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            Text(task.description, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.weight(1f))
            Illustration(R.drawable.illustration_task, Modifier.width(96.dp), height = 96.dp)
        }
        StatusLabel(task.label)
        if (controlsAvailable && review != null) FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            task.actions.forEach { action -> TextButton(onClick = { review(task, action) }) {
                Text(when (action) { "approve" -> "Review request"; "cancel" -> "Review cancellation"; "deny" -> "Deny request"; else -> "Review continuation" })
            } }
        }
        SelectionContainer {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("${task.target} · ${task.nodeStatus}", style = MaterialTheme.typography.bodySmall)
                task.progress?.let { Text("${if (it.current) "Worker checkpoint" else "Previous checkpoint"}: ${(it.fraction * 100).toInt()}% · ${it.step}\nREPORTED; progress is not verification.") }
                task.blocker?.let { Text(it) }
                task.value?.let { Text("Verified result: $it") }
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
