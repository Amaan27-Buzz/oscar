package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.activity.compose.BackHandler

@Composable fun AutomationsScreen(state: MobileState, page: String, navigate: (String) -> Unit, converse: (String) -> Unit) {
    var responsibility by remember(state.epoch) { mutableStateOf("") }
    var timing by remember(state.epoch) { mutableStateOf("") }
    when (page) {
        "Worker" -> {
            EditorialHeading("No Worker assigned")
            Text("Continuing responsibilities aren't available yet.", style = MaterialTheme.typography.bodyMedium)
            Button(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Run Worker · unavailable") }
            SupportingDetails("Responsibility & scope") {
                FeatureRow("Responsibility", "Not assigned", "Automations")
                FeatureRow("Devices", "None assigned", "Devices")
                FeatureRow("Autonomy", "Not delegated", "Preferences")
                FeatureRow("Linked automations", "None", "Activity")
                Text("One-time work is available in Activity. This page does not create a separate assistant.", style = MaterialTheme.typography.bodySmall)
            }
        }
        "Create" -> {
            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) { EditorialHeading("What should\nOSCAR do?") }
                Box(Modifier.width(80.dp)) { OscarOrb(state, size = 80.dp) }
            }
            StatusLabel("Draft only · scheduling unavailable")
            OutlinedTextField(responsibility, { responsibility = it.take(1000) }, modifier = Modifier.fillMaxWidth().testTag("automationDraft"),
                label = { Text("Responsibility") }, minLines = 2)
            OutlinedTextField(timing, { timing = it.take(200) }, modifier = Modifier.fillMaxWidth(), label = { Text("Timing") })
            SupportingDetails("Scope & access") {
                FeatureRow("Devices", "No delegated scope", "Devices")
                FeatureRow("Autonomy", "Not delegated", "Preferences")
                FeatureRow("Access mode", "Ask · actions need confirmation", "Conversation", Clay)
            }
            Button(shape = MaterialTheme.shapes.medium, onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Create automation · unavailable") }
            TextButton(onClick = { converse(listOf(responsibility.trim(), timing.trim()).filter { it.isNotEmpty() }.joinToString("\n")) }, enabled = responsibility.isNotBlank()) { Text("Discuss with OSCAR") }
            Text("Leaving Automations clears this draft. Discussing it does not create a schedule.", style = MaterialTheme.typography.bodySmall)
        }
        else -> {
            EditorialHeading("Automations")
            Illustration(R.drawable.illustration_automations, height = 120.dp)
            StatusLabel("Scheduling unavailable")
            FeatureRow("Workers", "No responsibilities assigned", "Automations", action = { navigate("Worker") })
            HorizontalDivider()
            FeatureRow("Schedules & watches", "Not available yet", "Activity", Clay)
            SupportingDetails("What is available") { Text("One-time Core work is available in Activity. Persistent schedules are not commissioned.", style = MaterialTheme.typography.bodySmall) }
            Button(shape = MaterialTheme.shapes.medium, onClick = { navigate("Create") }, colors = ButtonDefaults.buttonColors(containerColor = Sage), modifier = Modifier.fillMaxWidth()) { Glyph("Add", color = androidx.compose.ui.graphics.Color.White); Spacer(Modifier.width(8.dp)); Text("New responsibility") }
        }
    }
}

@Composable fun TodayScreen(state: MobileState, converse: () -> Unit, activity: () -> Unit) {
    Text(java.time.LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("EEEE, d MMMM", java.util.Locale.getDefault())), style = MaterialTheme.typography.headlineLarge)
    Illustration(R.drawable.illustration_today, height = 96.dp)
    FeatureRow("Calendar", "Not connected", "Activity", Clay)
    FeatureRow("Weather", "Unavailable", "Devices")
    FeatureRow("Communications", "Not connected", "Conversation")
    state.snapshot?.tasks?.takeIf { it.isNotEmpty() }?.let { tasks ->
        HorizontalDivider()
        Text("Current work", style = MaterialTheme.typography.titleMedium)
        tasks.take(5).forEach { task -> FeatureRow(task.description, task.label, "Activity", action = activity) }
    }
    Button(shape = MaterialTheme.shapes.medium, onClick = converse, colors = ButtonDefaults.buttonColors(containerColor = Sage), modifier = Modifier.fillMaxWidth()) { Text("Plan with OSCAR") }
    SupportingDetails("Planning capabilities") { Text("Calendar changes and a persistent Chief-of-Staff runtime are not available through this Mobile contract.", style = MaterialTheme.typography.bodySmall) }
}

@Composable fun AccessScreen() {
    PreferenceGroup("Current mode") {
        FeatureRow("Ask is active", "Inspect, reason and propose. Ask before state changes.", "Access")
    }
    PreferenceGroup("Unavailable modes") {
        FeatureRow("Secure", "Ordinary autonomy; protected or consequential work still needs consent.", "Access", Lilac)
        HorizontalDivider()
        FeatureRow("Full Access", "Owner-delegated autonomy over technically available capabilities.", "Access", Clay)
        Button(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth().testTag("delegationUnavailable")) { Text("Activation unavailable") }
    }
    SupportingDetails("How Full Access works") { Text("After explicit activation, no additional OSCAR per-action prompts. Android and external platform controls still apply.", style = MaterialTheme.typography.bodySmall) }
    SupportingDetails("Why activation is unavailable") { Text("Secure and Full Access require signed owner delegation and revocation support. Ask remains active; this screen cannot change your permissions.", style = MaterialTheme.typography.bodySmall) }
}

@Composable fun AwarenessScreen(privacy: () -> Unit) {
    PreferenceGroup("Awareness mode") {
        FeatureRow("Awareness is off", "Sentry is not active", "Awareness")
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        FilterChip(selected = true, onClick = {}, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Sage, selectedLabelColor = androidx.compose.ui.graphics.Color.White), label = { Text("Manual") })
        FilterChip(selected = false, onClick = {}, enabled = false, label = { Text("Trigger-only") })
        FilterChip(selected = false, onClick = {}, enabled = false, label = { Text("Sentry") })
        }
    }
    PreferenceGroup("Capture & permissions") {
        FeatureRow("Microphone", "Manage voice permissions", "Voice", action = privacy)
        HorizontalDivider()
        PreferenceValue("Background capture", "Unavailable")
    }
    PreferenceGroup("Retention") {
        PreferenceValue("Raw audio", "Off")
        HorizontalDivider()
        PreferenceValue("Observations", "Not retained")
    }
    SupportingDetails("Awareness & privacy") { Text("Passive · Aware · Guard · Away · Sleep are planned Sentry modes. Perceiving, retaining and acting require separate grants.", style = MaterialTheme.typography.bodySmall) }
}
