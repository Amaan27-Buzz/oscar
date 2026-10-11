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
    cancel: () -> Unit, activity: () -> Unit, voice: () -> Unit) {
    var reading by remember(state.epoch) { mutableStateOf(false) }
    val canSend = state.link == Link.CONNECTED && !state.busy && !state.privateSuppressed && draft.isNotBlank()
    Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
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
            style = MaterialTheme.typography.titleLarge, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
        Text("Continue when you need me.", color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
    val relevant = state.snapshot?.tasks?.let { tasks ->
        tasks.firstOrNull { "approve" in it.actions } ?: tasks.firstOrNull { it.state in setOf("executing", "awaiting_result", "result_received", "verifying") }
    }
    relevant?.let { task ->
        TextButton(onClick = activity) { Text("${task.label} · ${task.description}") }
    }
    if (state.restoring) Text("Restoring encrypted draft…", modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
    OutlinedTextField(draft, { write(it.take(1000)) }, enabled = !state.restoring && state.link != Link.CONNECTING,
        modifier = Modifier.fillMaxWidth().testTag("interactionInput"), label = { Text("Write to OSCAR") }, minLines = 2, maxLines = 5,
        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(imeAction = androidx.compose.ui.text.input.ImeAction.Send),
        keyboardActions = androidx.compose.foundation.text.KeyboardActions(onSend = { if (canSend) send() }))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = send, enabled = canSend) { Text("Send") }
        TextButton(onClick = voice) { Text("Voice") }
        if (state.busy) TextButton(onClick = cancel) { Text("Stop waiting") }
    }
    if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth().semantics { contentDescription = "Awaiting authoritative Core response" })
    state.interactions.lastOrNull()?.let { interaction ->
        HorizontalDivider()
        Text("Current response", style = MaterialTheme.typography.titleMedium)
        val task = state.snapshot?.tasks?.find { it.id == interaction.taskId }
        Text(task?.let { "${it.label}${it.value?.let { value -> ": $value" } ?: ""}" }
            ?: if (interaction.taskId != null) "UNKNOWN · task unavailable in current readback" else interaction.response)
        task?.response?.let { Text(it.take(400)); Text("REPORTED · facts require independent evidence", style = MaterialTheme.typography.bodySmall) }
        TextButton(onClick = { reading = true }) { Text("Read response") }
        if (interaction.taskId != null) TextButton(onClick = activity) { Text("Inspect task") }
        if (reading) ResponseDialog(interaction, task) { reading = false }
    }
}
@Composable private fun ResponseDialog(interaction: Interaction, task: CoreTask?, close: () -> Unit) {
    AlertDialog(onDismissRequest = close, modifier = Modifier.testTag("responseDialog"), title = { Text("Response") }, text = {
        SelectionContainer {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(interaction.text, style = MaterialTheme.typography.titleMedium)
                Text(task?.let { if (it.response != null) "${it.label} · response REPORTED" else it.label } ?: "UNKNOWN")
                if (task?.response != null) Text("REPORTED · a response is testimony, not independent verification.")
                if (task?.responseTruncated == true) Text("Bounded excerpt. Core returned only part of this response.")
                Text(task?.response ?: task?.value ?: task?.blocker ?: if (task != null) "No response yet. Inspect Activity for the current task." else interaction.response)
                if (task?.evidence?.isNotEmpty() == true) Text("Evidence: ${task.evidence.joinToString(", ")}")
            }
        }
    }, confirmButton = { TextButton(onClick = close) { Text("Back") } })
}
