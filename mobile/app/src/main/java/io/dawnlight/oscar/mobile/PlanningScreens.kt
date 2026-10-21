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

@Composable fun TodayScreen(session: CoreSession, state: MobileState, converse: () -> Unit, activity: () -> Unit) {
    IllustratedIntro(java.time.LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("EEEE, d MMMM", java.util.Locale.getDefault())),
        artwork = R.drawable.illustration_today, height = 136.dp)
    TactileSurface(Modifier.fillMaxWidth()) {
        FeatureRow("Calendar", if (state.dayBrief?.sources?.any { it.adapter == "calendar" } == true) "Observed context · refresh below" else "Not connected", "Calendar", Clay)
        HorizontalDivider()
        FeatureRow("Weather", "Unavailable", "Sun", Color(0xFFE7AD3B))
        HorizontalDivider()
        FeatureRow("Communications", "Not connected", "Conversation")
    }
    if (state.snapshot?.management != null) CurrentBrief(session, state)
    state.snapshot?.tasks?.takeIf { it.isNotEmpty() }?.let { tasks ->
        HorizontalDivider()
        Text("Current work", style = MaterialTheme.typography.titleMedium)
        tasks.take(5).forEach { task -> FeatureRow(task.description, task.label, "Activity", action = activity) }
    }
    OscarButton(onClick = converse, modifier = Modifier.fillMaxWidth()) { Text("Plan with OSCAR"); Spacer(Modifier.width(12.dp)); Glyph("Send", color = Color.White) }
    SupportingDetails("Planning capabilities") { Text("Connect time and calendar sources in Preferences → Awareness, then refresh their qualified context here. Calendar changes require a separately available capability and reviewed authority. Weather and communication awareness are unavailable.", style = MaterialTheme.typography.bodySmall) }
}
