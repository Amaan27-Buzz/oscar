package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.border
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.activity.compose.BackHandler

@Composable fun AutomationsScreen(state: MobileState, page: String, navigate: (String) -> Unit, converse: (String) -> Unit) {
    var responsibility by remember(state.epoch) { mutableStateOf("") }
    var timing by remember(state.epoch) { mutableStateOf("") }
    when (page) {
        "Worker" -> {
            IllustratedIntro(if (state.snapshot?.executive.isNullOrEmpty()) "No Worker in readback" else "Core responsibilities", artwork = R.drawable.illustration_worker, height = 136.dp)
            Text("Worker scope and activation are managed by your trusted Core. Changes aren't available on this phone yet.", style = MaterialTheme.typography.bodyMedium)
            OscarButton(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Run Worker · unavailable") }
            SupportingDetails("Responsibility & scope") {
                FeatureRow("Responsibility", "Not assigned", "Automations")
                FeatureRow("Devices", "None assigned", "Devices")
                FeatureRow("Autonomy", "Not delegated", "Person")
                FeatureRow("Linked automations", "None", "Activity")
                Text("One-time work is available in Activity. This page does not create a separate assistant.", style = MaterialTheme.typography.bodySmall)
            }
        }
        "Create" -> {
            if (LocalPageArtwork.current == R.drawable.oscar_orb) IllustratedIntro("What should\nOSCAR do?", artwork = R.drawable.oscar_orb)
            else {
            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) { EditorialHeading("What should\nOSCAR do?") }
                Box(Modifier.width(80.dp)) { OscarOrb(state, size = 80.dp) }
            }
            }
            StatusLabel("Draft only · scheduling unavailable")
            OscarField(responsibility, { responsibility = it.take(1000) }, modifier = Modifier.fillMaxWidth().testTag("automationDraft"),
                label = "Responsibility", minLines = 2)
            OscarField(timing, { timing = it.take(200) }, modifier = Modifier.fillMaxWidth(), label = "Timing")
            SupportingDetails("Scope & access") {
                FeatureRow("Devices", "No delegated scope", "Devices")
                FeatureRow("Autonomy", "Not delegated", "Person")
                FeatureRow("Access mode", "Ask · actions need confirmation", "Conversation", Clay)
            }
            OscarButton(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth()) { Text("Create automation · unavailable") }
            TextButton(onClick = { converse(listOf(responsibility.trim(), timing.trim()).filter { it.isNotEmpty() }.joinToString("\n")) }, enabled = responsibility.isNotBlank()) { Text("Discuss with OSCAR") }
            Text("Leaving Automations clears this draft. Discussing it does not create a schedule.", style = MaterialTheme.typography.bodySmall)
        }
        else -> {
            IllustratedIntro("Automations", artwork = R.drawable.illustration_automations, height = 152.dp)
            StatusLabel(if (state.snapshot?.executive != null) "Core responsibilities" else "Automation readback unavailable")
            state.snapshot?.executive?.forEach { goal -> TactileSurface(Modifier.fillMaxWidth()) { FeatureRow(goal.goal, "${goal.state} · ${goal.runs} of ${goal.maxRuns} runs verified", "Activity") } }
            TactileSurface(Modifier.fillMaxWidth()) {
                FeatureRow("Workers", if (state.snapshot?.executive.isNullOrEmpty()) "No responsibilities in this readback" else "Managed by your Core", "Automations", action = { navigate("Worker") }, artwork = R.drawable.illustration_worker_brief)
            }
            TactileSurface(Modifier.fillMaxWidth()) {
                FeatureRow("Schedules & watches", if (state.snapshot?.executive != null) "Review and activate with Core" else "Not available on this connection", "Clock", Clay, artwork = R.drawable.illustration_worker_watch)
            }
            SupportingDetails("What is available") { Text("Authorized task progress is available in Activity. Review and activate persistent schedules with Core; discussing a draft here does not activate it.", style = MaterialTheme.typography.bodySmall) }
            OscarButton(onClick = { navigate("Create") }, modifier = Modifier.fillMaxWidth()) { Glyph("Add", color = Color.White); Spacer(Modifier.width(8.dp)); Text("New responsibility") }
        }
    }
}

@Composable fun TodayScreen(state: MobileState, converse: () -> Unit, activity: () -> Unit) {
    IllustratedIntro(java.time.LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("EEEE, d MMMM", java.util.Locale.getDefault())),
        artwork = R.drawable.illustration_today, height = 136.dp)
    TactileSurface(Modifier.fillMaxWidth()) {
        FeatureRow("Calendar", "Not connected", "Calendar", Clay)
        HorizontalDivider()
        FeatureRow("Weather", "Unavailable", "Sun", Color(0xFFE7AD3B))
        HorizontalDivider()
        FeatureRow("Communications", "Not connected", "Conversation")
    }
    state.snapshot?.tasks?.takeIf { it.isNotEmpty() }?.let { tasks ->
        HorizontalDivider()
        Text("Current work", style = MaterialTheme.typography.titleMedium)
        tasks.take(5).forEach { task -> FeatureRow(task.description, task.label, "Activity", action = activity) }
    }
    OscarButton(onClick = converse, modifier = Modifier.fillMaxWidth()) { Text("Plan with OSCAR"); Spacer(Modifier.width(12.dp)); Glyph("Send", color = Color.White) }
    SupportingDetails("Planning capabilities") { Text("Calendar changes and a persistent Chief-of-Staff runtime are not available through this Mobile contract.", style = MaterialTheme.typography.bodySmall) }
}

@Composable fun AccessScreen() {
    IllustratedIntro("Access", "On your terms.", R.drawable.oscar_orb)
    PreferenceGroup("Current mode", flat = true) {
        TactileSurface(Modifier.fillMaxWidth().border(1.dp, Sage, RoundedCornerShape(18.dp))) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                IconBadge("Conversation")
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Ask is active", style = MaterialTheme.typography.titleLarge)
                    Text("Inspect, reason and propose. Ask before state changes.", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Glyph("Check", color = Sage)
            }
        }
    }
    PreferenceGroup("Unavailable modes", flat = true) {
        TactileSurface(Modifier.fillMaxWidth()) {
            FeatureRow("Secure", "Ordinary autonomy; protected or consequential work still needs consent.", "Shield", Lilac)
            StatusLabel("Unavailable")
        }
        Spacer(Modifier.height(12.dp))
        TactileSurface(Modifier.fillMaxWidth()) {
            FeatureRow("Full Access", "Owner-delegated autonomy over technically available capabilities.", "Door", Color(0xFFE7AD3B))
            OscarButton(onClick = {}, enabled = false, modifier = Modifier.fillMaxWidth().testTag("delegationUnavailable")) { Text("Activation unavailable") }
        }
    }
    SupportingDetails("How Full Access works") { Text("After explicit activation, no additional OSCAR per-action prompts. Android and external platform controls still apply.", style = MaterialTheme.typography.bodySmall) }
    SupportingDetails("Why activation is unavailable") { Text("Secure and Full Access require signed owner delegation and revocation support. Ask remains active; this screen cannot change your permissions.", style = MaterialTheme.typography.bodySmall) }
}

@Composable fun AwarenessScreen(privacy: () -> Unit) {
    IllustratedIntro("Awareness is off", artwork = R.drawable.illustration_awareness, height = 144.dp)
    StatusLabel("Sentry is not active")
    PreferenceGroup("Awareness mode") {
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        FilterChip(selected = true, onClick = {}, shape = RoundedCornerShape(14.dp), colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Sage, selectedLabelColor = Color.White), label = { Text("Manual") })
        FilterChip(selected = false, onClick = {}, enabled = false, shape = RoundedCornerShape(14.dp), label = { Text("Trigger-only") })
        FilterChip(selected = false, onClick = {}, enabled = false, shape = RoundedCornerShape(14.dp), label = { Text("Sentry") })
        }
    }
    PreferenceGroup("Capture & permissions") {
        FeatureRow("Microphone", "Manage voice permissions", "Voice", action = privacy)
        HorizontalDivider()
        FeatureRow("Background capture", "Unavailable", "Capture", Clay)
    }
    PreferenceGroup("Retention") {
        PreferenceValue("Raw audio", "Off")
        HorizontalDivider()
        PreferenceValue("Observations", "Not retained")
    }
    SupportingDetails("Awareness & privacy") { Text("Passive · Aware · Guard · Away · Sleep are planned Sentry modes. Perceiving, retaining and acting require separate grants.", style = MaterialTheme.typography.bodySmall) }
}
