package io.dawnlight.oscar.mobile

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.tween

@Composable fun PresenceScreen(state: MobileState, draft: String, write: (String) -> Unit, send: () -> Unit,
    cancel: () -> Unit, activity: () -> Unit, voice: () -> Unit, showComposer: Boolean = true, today: (() -> Unit)? = null) {
    var reading by remember(state.epoch) { mutableStateOf<Interaction?>(null) }
    if (state.interactions.isEmpty()) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                EditorialHeading(if (draft.isBlank()) "Here with you." else "What's on your mind?", if (draft.isBlank()) "Room for a good day." else null)
            }
            Box(Modifier.width(80.dp)) { OscarOrb(state, composing = draft.isNotBlank(), size = 80.dp) }
        }
        Column(Modifier.fillMaxWidth().animateContentSize(tween(if (LocalReducedMotion.current) 0 else 220))) {
            if (draft.isBlank()) Illustration(R.drawable.illustration_home, height = 180.dp)
        }
        Text(when {
            state.link == Link.DEGRADED -> "Connection needs attention"
            state.link != Link.CONNECTED -> "OSCAR is not connected"
            state.approval != null || state.snapshot?.tasks?.any { "approve" in it.actions } == true -> "Your decision is needed"
            state.snapshot?.tasks?.any { it.nodeStatus != "online" && it.state in setOf("executing", "awaiting_result", "result_received", "verifying") } == true -> "Executor unavailable"
            state.snapshot?.tasks?.any { it.state == "verifying" } == true -> "Checking the outcome"
            state.snapshot?.tasks?.any { it.state in setOf("executing", "awaiting_result", "result_received") } == true -> "Work is underway"
            state.busy -> "Waiting for Core"
            else -> "Continue when you need me."
        }, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
        today?.let { FeatureRow("Today", "Plan your day with OSCAR", "Activity", action = it) }
    }
    state.snapshot?.tasks?.firstOrNull { "approve" in it.actions || it.state in setOf("executing", "awaiting_result", "result_received", "verifying") }?.takeIf { task -> state.interactions.none { it.taskId == task.id } }?.let { task ->
        TactileSurface { FeatureRow(task.description, task.label, "Activity", action = activity) }
    }
    state.interactions.forEach { interaction ->
        val task = state.snapshot?.tasks?.find { it.id == interaction.taskId }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            SelectionContainer {
                Text(interaction.text, Modifier.widthIn(max = 300.dp).background(
                    MaterialTheme.colorScheme.secondaryContainer, RoundedCornerShape(12.dp)).padding(12.dp),
                    color = MaterialTheme.colorScheme.onSecondaryContainer, style = MaterialTheme.typography.bodyLarge)
            }
        }
        SelectionContainer {
            ResponseText(task?.response ?: task?.value ?: task?.blocker ?: task?.label
                ?: if (interaction.taskId != null) "Task unavailable in current readback · outcome unknown" else interaction.response,
                maxLines = 12
            )
        }
        if (task?.response != null) StatusLabel("Reported response") else task?.let { StatusLabel(it.label) }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { reading = interaction }) { Text("Read response") }
            if (interaction.taskId != null) TextButton(onClick = activity) { Text("Task details") }
        }
    }
    if (state.busy) {
        LinearProgressIndicator(Modifier.fillMaxWidth().semantics { contentDescription = "Waiting for OSCAR" })
        TextButton(onClick = cancel) { Text("Stop waiting") }
    }
    if (showComposer) ConversationComposer(state, draft, write, send, voice)
    reading?.let { interaction -> ResponseDialog(interaction, state.snapshot?.tasks?.find { it.id == interaction.taskId }, { reading = null }) }
}

@Composable fun ConversationComposer(state: MobileState, draft: String, write: (String) -> Unit, send: () -> Unit, voice: () -> Unit) {
    val canSend = state.link == Link.CONNECTED && !state.busy && !state.privateSuppressed && draft.isNotBlank()
    if (state.restoring) StatusLabel("Restoring draft…")
    TactileSurface(Modifier.fillMaxWidth()) {
        OutlinedTextField(draft, { write(it.take(1000)) }, enabled = !state.restoring && state.link != Link.CONNECTING,
            modifier = Modifier.fillMaxWidth().testTag("interactionInput"), label = { Text("Write to OSCAR") }, minLines = 1, maxLines = 4,
            shape = RoundedCornerShape(12.dp),
            keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(imeAction = androidx.compose.ui.text.input.ImeAction.Send),
            keyboardActions = androidx.compose.foundation.text.KeyboardActions(onSend = { if (canSend) send() }))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            TextButton(onClick = voice) { Glyph("Voice"); Spacer(Modifier.width(8.dp)); Text("Voice") }
            Button(shape = MaterialTheme.shapes.medium, onClick = send, enabled = canSend, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary)) { Text("Send") }
        }
    }
}

@Composable internal fun ResponseDialog(interaction: Interaction, task: CoreTask?, close: () -> Unit) {
    DetailPage("Reading", close, "responseDialog") {
        Text(interaction.text, style = MaterialTheme.typography.titleLarge, maxLines = 3, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis, modifier = Modifier.semantics { heading() })
        if (interaction.text.length > 140) SupportingDetails("Original request") { Text(interaction.text) }
        StatusLabel(if (task?.response != null) "Reported response" else task?.label ?: if (interaction.taskId == null) "Core response" else "Outcome unknown")
        if (task?.responseTruncated == true) StatusLabel("Bounded excerpt. Core returned only part of this response.")
        SelectionContainer {
            ResponseText(task?.response ?: task?.value ?: task?.blocker ?: if (task != null) "No response yet. Inspect Activity for the current task." else interaction.response)
        }
        task?.let {
            SupportingDetails("Source & verification") {
                Text(it.label, style = MaterialTheme.typography.bodySmall)
                Text("Reported text is not independent verification.", style = MaterialTheme.typography.bodySmall)
                if (it.evidence.isNotEmpty()) Text(it.evidence.joinToString("\n"), style = MaterialTheme.typography.bodySmall)
            }
        }
        Button(shape = MaterialTheme.shapes.medium, onClick = close, modifier = Modifier.fillMaxWidth()) { Text("Follow up in conversation") }
    }
}
