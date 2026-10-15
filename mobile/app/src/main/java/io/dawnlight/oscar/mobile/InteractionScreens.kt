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
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.draw.dropShadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.shadow.Shadow
import androidx.compose.ui.unit.DpOffset

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
        today?.let { TactileSurface { FeatureRow("Today", "Plan your day with OSCAR", "Calendar", Powder, action = it) } }
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
        Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.width(30.dp)) { OscarOrb(state, size = 30.dp, tag = "response-orb") }
            Text("OSCAR", style = MaterialTheme.typography.labelLarge)
        }
        SelectionContainer {
            ResponseText(task?.response ?: task?.value ?: task?.blocker ?: task?.label
                ?: if (interaction.taskId != null) "Task unavailable in current readback · outcome unknown" else interaction.response, maxLines = 12)
        }
        if (task?.response != null) StatusLabel("Reported response") else task?.let { StatusLabel(it.label) }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { reading = interaction }) { Glyph("Book"); Spacer(Modifier.width(8.dp)); Text("Read response") }
            if (interaction.taskId != null) TextButton(onClick = activity) { Glyph("Document"); Spacer(Modifier.width(8.dp)); Text("Task details") }
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
    val shape = RoundedCornerShape(22.dp)
    Surface(Modifier.fillMaxWidth().dropShadow(shape, Shadow(8.dp, Color.Black.copy(alpha = 0.08f), offset = DpOffset(2.dp, 4.dp))),
        shape = shape, color = MaterialTheme.colorScheme.surfaceContainer,
        border = androidx.compose.foundation.BorderStroke(0.7.dp, MaterialTheme.colorScheme.outlineVariant)) {
        Row(Modifier.fillMaxWidth().padding(6.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            BasicTextField(draft, { write(it.take(1000)) }, enabled = !state.restoring && state.link != Link.CONNECTING,
                modifier = Modifier.weight(1f).heightIn(min = 48.dp).testTag("interactionInput").padding(horizontal = 12.dp, vertical = 12.dp)
                    .semantics { contentDescription = "Write to OSCAR" }, minLines = 1, maxLines = 4,
                textStyle = MaterialTheme.typography.bodyLarge.copy(color = MaterialTheme.colorScheme.onSurface), cursorBrush = SolidColor(Sage),
                keyboardOptions = KeyboardOptions(imeAction = androidx.compose.ui.text.input.ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { if (canSend) send() }), decorationBox = { field ->
                    if (draft.isEmpty()) Text("Write to OSCAR", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    field()
                })
            TextButton(onClick = voice, contentPadding = PaddingValues(horizontal = 6.dp, vertical = 4.dp)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Glyph("Voice"); Text("Voice", style = MaterialTheme.typography.labelSmall)
                }
            }
            OscarButton(onClick = send, enabled = canSend) { Text("Send"); Glyph("Send", Modifier.size(18.dp)) }
        }
    }
}

@Composable internal fun ResponseDialog(interaction: Interaction, task: CoreTask?, close: () -> Unit) {
    DetailPage("Reading", close, "responseDialog") {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("OSCAR", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(interaction.text, style = MaterialTheme.typography.titleLarge, maxLines = 3, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis, modifier = Modifier.semantics { heading() })
            }
            Illustration(R.drawable.illustration_book_green, Modifier.width(72.dp), height = 86.dp)
        }
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
        OscarButton(onClick = close, modifier = Modifier.fillMaxWidth()) { Glyph("Conversation"); Text("Follow up in conversation") }
    }
}
