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
    BackHandler(page != "Overview") { navigate("Overview") }
    if (page != "Overview") TextButton(onClick = { navigate("Overview") }, modifier = Modifier.testTag("automation-back")) { Glyph("Back"); Text("Automations") }
    when (page) {
        "Worker" -> {
            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.Bottom) {
                Column(Modifier.weight(1f)) { EditorialHeading("Worker", "A responsibility within OSCAR.") }
                Illustration(R.drawable.illustration_worker, Modifier.width(140.dp), height = 180.dp)
            }
            StatusLabel("Not configured")
            FeatureRow("Responsibility", "No persistent Worker has been assigned.", "Automations")
            FeatureRow("Scope & devices", "No delegated scope or assigned devices.", "Devices")
            FeatureRow("Autonomy", "Unavailable · cannot expand Core authority.", "Preferences")
            FeatureRow("Linked automations", "None · scheduling runtime unavailable.", "Activity")
            Button(shape = MaterialTheme.shapes.medium, onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Run Worker · unavailable") }
            SupportingDetails("About Workers") { Text("Current one-time tasks remain in Activity. A task executor is not a persistent Worker.", style = MaterialTheme.typography.bodySmall) }
        }
        "Create" -> {
            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) { EditorialHeading("What should\nOSCAR do?") }
                Box(Modifier.width(80.dp)) { OscarOrb(state, size = 80.dp) }
            }
            StatusLabel("Draft only · no Worker or schedule is deployed")
            OutlinedTextField(responsibility, { responsibility = it.take(1000) }, modifier = Modifier.fillMaxWidth().testTag("automationDraft"),
                label = { Text("Responsibility") }, minLines = 2)
            OutlinedTextField(timing, { timing = it.take(200) }, modifier = Modifier.fillMaxWidth(), label = { Text("Timing") })
            FeatureRow("Scope", "Available capabilities require a Core review.", "Devices", Clay)
            FeatureRow("Autonomy", "Not delegated", "Preferences")
            FeatureRow("Access mode", "Ask · current exact-action confirmation remains required.", "Conversation", Clay)
            Button(shape = MaterialTheme.shapes.medium, onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Create automation · unavailable") }
            TextButton(onClick = { converse(listOf(responsibility.trim(), timing.trim()).filter { it.isNotEmpty() }.joinToString("\n")) }, enabled = responsibility.isNotBlank()) { Text("Discuss with OSCAR") }
            Text("This draft is temporary and clears when you leave Automations. Discussing it does not create a schedule.", style = MaterialTheme.typography.bodySmall)
        }
        else -> {
            EditorialHeading("Automations", "Taken care of.")
            Illustration(R.drawable.illustration_automations)
            StatusLabel("Persistent scheduling is unavailable")
            FeatureRow("Workers", "No continuing responsibilities configured", "Automations", action = { navigate("Worker") })
            HorizontalDivider()
            FeatureRow("Schedules & watches", "Planned · Core runtime required", "Activity", Clay)
            SupportingDetails("What is available") { Text("One-time Core work is available in Activity. Persistent schedules are not commissioned.", style = MaterialTheme.typography.bodySmall) }
            Button(shape = MaterialTheme.shapes.medium, onClick = { navigate("Create") }, colors = ButtonDefaults.buttonColors(containerColor = Sage), modifier = Modifier.fillMaxWidth()) { Glyph("Add", color = androidx.compose.ui.graphics.Color.White); Spacer(Modifier.width(8.dp)); Text("New responsibility") }
        }
    }
}

@Composable fun TodayScreen(state: MobileState, converse: () -> Unit, activity: () -> Unit) {
    Illustration(R.drawable.illustration_today, height = 180.dp)
    EditorialHeading("Today", "A little room to focus.")
    Text(java.time.LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("EEEE · d MMMM", java.util.Locale.getDefault())), style = MaterialTheme.typography.bodySmall)
    FeatureRow("Calendar", "Not connected · no commitments retrieved", "Activity", Clay)
    FeatureRow("Weather", "Unavailable · no current forecast retrieved", "Devices")
    FeatureRow("Communications", "No provider brief available", "Conversation")
    state.snapshot?.tasks?.takeIf { it.isNotEmpty() }?.let { tasks ->
        HorizontalDivider()
        Text("Current Core work", style = MaterialTheme.typography.titleMedium)
        tasks.take(5).forEach { task -> FeatureRow(task.description, task.label, "Activity", action = activity) }
    }
    Button(shape = MaterialTheme.shapes.medium, onClick = converse, colors = ButtonDefaults.buttonColors(containerColor = Sage), modifier = Modifier.fillMaxWidth()) { Text("Plan with OSCAR") }
    SupportingDetails("Planning capabilities") { Text("Calendar changes and a persistent Chief-of-Staff runtime are not available through this Mobile contract.", style = MaterialTheme.typography.bodySmall) }
}

@Composable fun AccessScreen(state: MobileState) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { EditorialHeading("Access", "Current: Ask") }
        Box(Modifier.width(88.dp)) { OscarOrb(state, size = 88.dp) }
    }
    FeatureRow("Ask", "Inspect, reason and propose. Ask before state changes.", "Conversation")
    HorizontalDivider()
    FeatureRow("Secure", "Ordinary autonomous work; protected and consequential operations retain consent.", "Preferences", Lilac)
    StatusLabel("Activation unavailable")
    HorizontalDivider()
    FeatureRow("Full Access", "Genuine unrestricted owner-delegated autonomy over technically available capabilities.", "Automations", Clay)
    SupportingDetails("How Full Access works") { Text("After explicit activation, no additional OSCAR per-action prompts. Android and external platform controls still apply.", style = MaterialTheme.typography.bodySmall) }
    Button(shape = MaterialTheme.shapes.medium, onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth().testTag("delegationUnavailable")) { Text("Activation unavailable") }
    Text("Signed owner delegation and revocation are not integrated. This page grants no authority and cannot bypass exact-action confirmation.", style = MaterialTheme.typography.bodyMedium)
}

@Composable fun AwarenessScreen(privacy: () -> Unit) {
    EditorialHeading("Awareness", "Awareness is off.")
    Illustration(R.drawable.illustration_awareness, height = 200.dp)
    StatusLabel("No Sentry observation or recording is active")
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        FilterChip(selected = true, onClick = {}, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Sage, selectedLabelColor = androidx.compose.ui.graphics.Color.White), label = { Text("Manual") })
        FilterChip(selected = false, onClick = {}, enabled = false, label = { Text("Trigger-only") })
        FilterChip(selected = false, onClick = {}, enabled = false, label = { Text("Sentry") })
    }
    FeatureRow("Microphone", "Voice capture requires separate Android and OSCAR grants.", "Voice", action = privacy)
    FeatureRow("Capture", "Unavailable · Sentry runtime not commissioned", "Devices", Clay)
    FeatureRow("Retention", "Raw audio and observation retention off", "Preferences", Lilac)
    SupportingDetails("Awareness & privacy") { Text("Passive · Aware · Guard · Away · Sleep are planned Sentry modes. Perceiving, retaining and acting require separate grants.", style = MaterialTheme.typography.bodySmall) }
    TextButton(onClick = privacy) { Text("Privacy controls") }
}
