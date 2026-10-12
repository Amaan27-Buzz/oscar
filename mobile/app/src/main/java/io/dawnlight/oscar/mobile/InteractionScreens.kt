package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.*
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

@Composable fun PresenceScreen(state: MobileState, draft: String, write: (String) -> Unit, send: () -> Unit,
    cancel: () -> Unit, activity: () -> Unit, voice: () -> Unit, showComposer: Boolean = true, inspect: (String) -> Unit = { activity() }) {
    var reading by remember(state.epoch) { mutableStateOf(false) }
    if (showComposer || state.link == Link.CONNECTED) Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(when {
            state.link == Link.DEGRADED -> "Connection needs attention"
            state.link != Link.CONNECTED -> "OSCAR is not connected"
            state.approval != null || state.snapshot?.tasks?.any { "approve" in it.actions } == true -> "Your decision is needed"
            state.snapshot?.tasks?.any { it.nodeStatus != "online" && it.state in setOf("executing", "awaiting_result", "result_received", "verifying") } == true -> "Executor unavailable"
            state.snapshot?.tasks?.any { it.state == "verifying" } == true -> "Checking the outcome"
            state.snapshot?.tasks?.any { it.state in setOf("executing", "awaiting_result", "result_received") } == true -> "Work is underway"
            state.busy -> "Waiting for Core"
            else -> "Here with you"
        },
            style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite; heading() })
    }
    val relevant = state.snapshot?.tasks?.let { tasks ->
        tasks.firstOrNull { "approve" in it.actions } ?: tasks.firstOrNull { it.state in setOf("executing", "awaiting_result", "result_received", "verifying") }
    }
    relevant?.let { task ->
            Column(Modifier.fillMaxWidth().padding(vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                HorizontalDivider()
                Text(task.description, style = MaterialTheme.typography.titleMedium)
                Text(task.label, color = MaterialTheme.colorScheme.onSurfaceVariant)
                FilledTonalButton(onClick = activity, shape = MaterialTheme.shapes.small) { Text(if ("approve" in task.actions) "Review in Activity" else "Inspect work"); Spacer(Modifier.width(8.dp)); OscarIcon("arrow") }
            }
    }
    if (relevant == null && state.interactions.isEmpty() && state.link == Link.CONNECTED) {
        state.snapshot?.tasks?.firstOrNull { it.state == "verified" && it.value != null }?.let { task ->
            HorizontalDivider(Modifier.padding(top = 16.dp))
            Text(task.description, style = MaterialTheme.typography.titleMedium)
            Text("${task.label} · ${task.value}", color = MaterialTheme.colorScheme.onSurfaceVariant)
            TextButton(onClick = { inspect(task.id) }, enabled = !state.busy, contentPadding = PaddingValues(0.dp)) { Text("Inspect verified work"); Spacer(Modifier.width(8.dp)); OscarIcon("arrow") }
        }
    }
    state.interactions.lastOrNull()?.let { interaction ->
        HorizontalDivider()
        Text("Current response", style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
        val task = state.snapshot?.tasks?.find { it.id == interaction.taskId }
        Text(task?.let { "${it.label}${it.value?.let { value -> ": $value" } ?: ""}" }
            ?: if (interaction.taskId != null) "UNKNOWN · task unavailable in current readback" else interaction.response)
        task?.response?.let { Text(it.take(400), style = MaterialTheme.typography.bodyMedium, maxLines = 4, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis); Text("REPORTED", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilledTonalButton(onClick = { reading = true }, shape = MaterialTheme.shapes.small) { Text("Read response") }
            if (interaction.taskId != null) TextButton(onClick = activity) { Text("Inspect task") }
        }
        if (reading) ResponseDialog(interaction, task) { reading = false }
    }
    if (showComposer) InteractionComposer(state, draft, write, send, cancel, voice)
}
@Composable fun InteractionComposer(state: MobileState, draft: String, write: (String) -> Unit, send: () -> Unit, cancel: () -> Unit, voice: () -> Unit) {
    val canSend = state.link == Link.CONNECTED && !state.busy && !state.privateSuppressed && draft.isNotBlank()
    if (state.restoring) Text("Restoring encrypted draft…", modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
    OutlinedTextField(draft, { write(it.take(1000)) }, enabled = !state.restoring && state.link != Link.CONNECTING,
        modifier = Modifier.weight(1f).testTag("interactionInput").semantics { contentDescription = "Write to OSCAR" }, placeholder = { Text("Write to OSCAR") }, minLines = 1, maxLines = 4,
        shape = MaterialTheme.shapes.small, textStyle = MaterialTheme.typography.bodyLarge,
        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(imeAction = androidx.compose.ui.text.input.ImeAction.Send),
        keyboardActions = androidx.compose.foundation.text.KeyboardActions(onSend = { if (canSend) send() }),
        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant))
        FilledIconButton(onClick = send, enabled = canSend, shape = MaterialTheme.shapes.small, modifier = Modifier.size(48.dp).semantics { contentDescription = "Send" }) { OscarIcon("arrow") }
    }
    if (state.busy) TextButton(onClick = cancel) { OscarIcon("stop"); Spacer(Modifier.width(8.dp)); Text("Stop waiting") }
}
@Composable private fun ResponseDialog(interaction: Interaction, task: CoreTask?, close: () -> Unit) {
    androidx.compose.ui.window.Dialog(onDismissRequest = close, properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(Modifier.fillMaxSize().testTag("responseDialog"), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.safeDrawingPadding().padding(24.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text("Response", style = MaterialTheme.typography.headlineSmall, modifier = Modifier.weight(1f).semantics { heading() })
            TextButton(onClick = close) { Text("Back") }
        }
        Spacer(Modifier.height(24.dp))
        SelectionContainer(Modifier.weight(1f)) {
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(interaction.text, style = MaterialTheme.typography.titleMedium)
                Text(task?.let { if (it.response != null) "${it.label} · response REPORTED" else it.label } ?: "UNKNOWN")
                if (task?.response != null) Text("REPORTED · a response is testimony, not independent verification.")
                if (task?.responseTruncated == true) Text("Bounded excerpt. Core returned only part of this response.")
                Text(task?.response ?: task?.value ?: task?.blocker ?: if (task != null) "No response yet. Inspect Activity for the current task." else interaction.response, style = MaterialTheme.typography.bodyLarge)
                if (task?.evidence?.isNotEmpty() == true) Text("Evidence: ${task.evidence.joinToString(", ")}")
            }
        }
        }
        }
    }
}
