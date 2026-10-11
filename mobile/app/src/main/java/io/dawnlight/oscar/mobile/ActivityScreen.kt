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
    Text("Ongoing work", style = MaterialTheme.typography.titleLarge)
    if (state.snapshot == null) { Text("Connect to Core to inspect activity. No cached task state is presented as current."); return }
    val completed = setOf("verified", "partially_verified", "failed", "cancelled")
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf("Active", "Finished").forEach { name ->
            FilterChip(selected = filter == name, onClick = { filter = name }, label = { Text(name) })
        }
    }
    val tasks = state.snapshot.tasks.filter { (it.state in completed) == (filter == "Finished") }
    if (tasks.isEmpty()) Text(if (filter == "Active") "Nothing is waiting here." else "No finished tasks in current readback.")
    tasks.forEach { task ->
        HorizontalDivider()
        Text(task.description, style = MaterialTheme.typography.titleMedium, modifier = Modifier.testTag("task-description-${task.id}"))
        Text(task.label, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
        Text("From ${task.origin}", style = MaterialTheme.typography.bodySmall)
        Text("${when(task.ownership) { "leased" -> "Executor"; "none" -> "Last target"; "expired" -> "Lease unavailable"; else -> "Planned target" }}: ${task.target} · ${task.nodeStatus}", style = MaterialTheme.typography.bodySmall)
        task.progress?.let { Text("${if (it.current) "Worker checkpoint" else "Previous checkpoint"}: ${(it.fraction * 100).toInt()}% · ${it.step} · REPORTED", style = MaterialTheme.typography.bodyMedium) }
        task.blocker?.let { Text(it) }
        FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            TextButton(onClick = { inspect(task.id) }, enabled = !state.busy && state.link == Link.CONNECTED) { Text("Inspect") }
            if ("approve" in task.actions) TextButton(onClick = { review(task, "approve") }, enabled = !state.busy) { Text("Review request") }
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

@Composable fun TaskInspector(task: CoreTask, close: () -> Unit) {
    AlertDialog(onDismissRequest = close, modifier = Modifier.testTag("taskInspector"), title = { Text("Task & evidence") }, text = {
        SelectionContainer {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(task.description, style = MaterialTheme.typography.titleMedium)
                Text(task.label)
                Text("Target: ${task.target}\nConnection: ${task.nodeStatus}\nOwnership: ${task.ownership}\nGeneration: ${task.generation}")
                task.progress?.let { Text("${if (it.current) "Worker checkpoint" else "Previous checkpoint"}: ${(it.fraction * 100).toInt()}% · ${it.step}\nREPORTED; progress is not verification.") }
                task.blocker?.let { Text(it) }
                task.value?.let { Text("Verified result: $it") }
                task.response?.let { Text("Response REPORTED; task verification does not establish every response claim."); Text(it) }
                if (task.responseTruncated) Text("Core supplied a bounded excerpt.")
                Text(if (task.evidence.isEmpty()) "No independent evidence references are available." else "Evidence references: ${task.evidence.joinToString(", ")}")
                task.artifacts.forEach { Text("Artifact ${it.id}\n${it.kind} · ${it.status}\n${it.hash ?: "Hash unavailable"}") }
                if (task.artifacts.isEmpty()) Text("No artifact summary available to this session.")
                Text("Only currently advertised actions are offered. Continuation restores a plan; fresh approval is still required to execute.")
            }
        }
    }, confirmButton = { TextButton(onClick = close) { Text("Back") } })
}
