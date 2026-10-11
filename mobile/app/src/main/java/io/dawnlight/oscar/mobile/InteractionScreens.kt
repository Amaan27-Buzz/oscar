package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp

@Composable fun PresenceScreen(state: MobileState, draft: String, write: (String) -> Unit, send: () -> Unit,
    cancel: () -> Unit, activity: () -> Unit, voice: () -> Unit) {
    Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(when {
            state.link == Link.DEGRADED -> "Connection needs attention"
            state.link != Link.CONNECTED -> "OSCAR is not connected"
            state.approval != null || state.snapshot?.tasks?.any { "approve" in it.actions } == true -> "Your decision is needed"
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
    OutlinedTextField(draft, { write(it.take(1000)) }, modifier = Modifier.fillMaxWidth().testTag("interactionInput"), label = { Text("Write to OSCAR") }, minLines = 2, maxLines = 5,
        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(imeAction = androidx.compose.ui.text.input.ImeAction.Send),
        keyboardActions = androidx.compose.foundation.text.KeyboardActions(onSend = { if (state.link == Link.CONNECTED && !state.busy && draft.isNotBlank()) send() }))
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = send, enabled = state.link == Link.CONNECTED && !state.busy && draft.isNotBlank()) { Text("Send") }
        TextButton(onClick = voice) { Text("Voice") }
        if (state.busy) TextButton(onClick = cancel) { Text("Stop waiting") }
    }
    if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth().semantics { contentDescription = "Awaiting authoritative Core response" })
    if (state.interactions.isNotEmpty()) Text("Current interaction", style = MaterialTheme.typography.titleMedium)
    state.interactions.forEach { interaction ->
        HorizontalDivider()
        Text(interaction.text, style = MaterialTheme.typography.titleMedium)
        val task = state.snapshot?.tasks?.find { it.id == interaction.taskId }
        Text(task?.let { "${it.label}${it.value?.let { value -> ": $value" } ?: ""}" } ?: interaction.response)
        task?.response?.let { Text(it); Text("Response · reported; facts require independent evidence", style = MaterialTheme.typography.bodySmall) }
        if (interaction.taskId != null) TextButton(onClick = activity) { Text("Inspect task") }
    }
}
@Composable fun ActivityScreen(state: MobileState, inspect: (String) -> Unit, review: (CoreTask, String) -> Unit) {
    Text("Ongoing work", style = MaterialTheme.typography.titleLarge)
    if (state.snapshot == null) Text("Connect to Core to inspect activity. No cached task state is presented as current.")
    else if (state.snapshot.tasks.isEmpty()) Text("Nothing is waiting here.")
    state.snapshot?.tasks?.forEach { task ->
        HorizontalDivider()
        Text(task.description, style = MaterialTheme.typography.titleMedium)
        Text(task.label, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
        Text("${task.target} · ${task.nodeStatus}", style = MaterialTheme.typography.bodySmall)
        task.blocker?.let { Text(it) }
        task.value?.let { Text("Result: $it") }
        task.response?.let { Text(it); Text("Response · reported", style = MaterialTheme.typography.bodySmall) }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            TextButton(onClick = { inspect(task.id) }, enabled = !state.busy) { Text("Inspect") }
            task.actions.filter { it != "deny" }.take(2).forEach { action ->
                TextButton(onClick = { review(task, action) }, enabled = !state.busy) { Text(action.replaceFirstChar { it.uppercase() }) }
            }
        }
        if ("deny" in task.actions) TextButton(onClick = { review(task, "deny") }, enabled = !state.busy) { Text("Deny request") }
    }
}
@Composable fun DevicesScreen(state: MobileState, connect: () -> Unit) {
    Text("Connection Grid", style = MaterialTheme.typography.titleLarge)
    Text("Capabilities belong to the nodes that currently report them. Offline nodes cannot execute new work.")
    if (state.snapshot == null) Text("No current Grid snapshot is available.")
    state.snapshot?.nodes?.forEach { node ->
        HorizontalDivider()
        Text(node.role, style = MaterialTheme.typography.titleMedium)
        Text("${node.id}\n${node.status} · ${if (node.paired) "Paired" else "Not paired"}")
        Text(if (node.capabilities.isEmpty()) "No currently available capabilities" else "Available: ${node.capabilities.distinct().joinToString(", ")}")
        val tasks = state.snapshot.tasks.filter { it.target == node.id }
        if (tasks.isNotEmpty()) Text("${tasks.size} associated task(s). Inspect in Activity.")
    }
    TextButton(onClick = connect) { Text("Connect this phone") }
    Text("Power and wake controls appear only when a real scoped capability is available.", style = MaterialTheme.typography.bodySmall)
}
