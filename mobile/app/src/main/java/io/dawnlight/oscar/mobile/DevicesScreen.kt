package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.tween

@Composable fun DevicesScreen(state: MobileState, connect: () -> Unit, disconnect: () -> Unit) {
    IllustratedIntro("Your devices", artwork = R.drawable.illustration_devices, height = 132.dp)
    TactileSurface(Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            IconBadge("Phone")
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("This phone", style = MaterialTheme.typography.titleLarge)
                StatusPill(when (state.link) {
                    Link.CONNECTED -> "Connected to Core"
                    Link.CONNECTING -> "Connecting to Core…"
                    Link.DEGRADED -> "Core connection lost"
                    Link.DISCONNECTED -> "Not connected to Core"
                }, when (state.link) { Link.CONNECTED -> Sage; Link.CONNECTING -> Amber; else -> Clay })
            }
        }
    }
    val snapshot = state.snapshot.takeIf { state.link == Link.CONNECTED }
    val nodes = snapshot?.nodes?.filterNot { it.id == state.connectedNode && it.role == "OSCAR Mobile" }
    if (nodes.isNullOrEmpty()) {
        StatusLabel(if (snapshot == null) "Connect Core to see your other devices." else "No other devices listed.")
    } else {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Other devices", style = MaterialTheme.typography.labelLarge, modifier = Modifier.semantics { heading() })
            HorizontalDivider(Modifier.weight(1f))
        }
        nodes.forEach { node ->
            var expanded by remember(node.id, state.epoch) { mutableStateOf(false) }
            val active = snapshot?.tasks.orEmpty().filter { (it.target == node.id || it.originNode == node.id) && it.state !in setOf("verified", "partially_verified", "failed", "cancelled") }
            val (icon, color) = when (node.role) {
                "OSCAR Mobile" -> "Phone" to Sage
                "Desktop" -> "Devices" to Powder
                "Cloud", "Core" -> "Goal" to Clay
                "Edge" -> "Retain" to Lilac
                else -> "Devices" to Sage
            }
            TactileSurface(Modifier.fillMaxWidth()) {
                FeatureRow(node.role, node.status.replaceFirstChar { it.uppercase() } +
                    (if (!node.paired) " · Not paired" else "") +
                    (if (active.isNotEmpty()) " · ${active.size} ${if (active.size == 1) "work item" else "work items"}" else ""),
                    icon, color, action = { expanded = !expanded },
                    modifier = Modifier.testTag("device-${node.id}").semantics { stateDescription = if (expanded) "Expanded" else "Collapsed" })
                Column(Modifier.fillMaxWidth().animateContentSize(tween(if (LocalReducedMotion.current) 0 else 200))) {
                    if (expanded) {
                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            HorizontalDivider()
                            Text("Capabilities", style = MaterialTheme.typography.titleMedium)
                            Text(if (node.capabilities.isEmpty()) "No currently advertised executor capabilities" else node.capabilities.distinct().joinToString("\n"), style = MaterialTheme.typography.bodySmall)
                            active.forEach { Text("${it.label} · ${it.description}", style = MaterialTheme.typography.bodyMedium) }
                            Text("Device ID: ${node.id} · ${if (node.paired) "Paired" else "Not paired"}", style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }
    }
    if (state.link != Link.CONNECTED) OscarButton(onClick = connect, enabled = state.link != Link.CONNECTING && !state.restoring,
        modifier = Modifier.fillMaxWidth()) { Text("Connect Core") }
    SupportingDetails("Connection & privacy") {
        if (state.link == Link.CONNECTED) TextButton(onClick = connect) { Text("Change Core connection") }
        TextButton(onClick = disconnect) { Text("Disconnect and remove local credentials") }
        Text("Local disconnect removes this app’s credentials. Remote revocation is a separate Core action.", style = MaterialTheme.typography.bodySmall)
        Text("Background listening, power and wake controls are not enabled here. Cloud, Edge and Home Node appear only when commissioned.", style = MaterialTheme.typography.bodySmall)
    }
}
