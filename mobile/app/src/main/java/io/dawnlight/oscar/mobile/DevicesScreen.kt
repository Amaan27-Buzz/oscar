package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.tween

@Composable fun DevicesScreen(state: MobileState, connect: () -> Unit, disconnect: () -> Unit) {
    Text("Your devices", style = MaterialTheme.typography.titleLarge)
    TactileSurface(Modifier.fillMaxWidth()) {
        FeatureRow("This phone", when (state.link) {
            Link.CONNECTED -> "Connected to Core"
            Link.CONNECTING -> "Connecting to Core…"
            Link.DEGRADED -> "Core connection lost"
            Link.DISCONNECTED -> "Not connected to Core"
        }, "Phone")
    }
    val snapshot = state.snapshot.takeIf { state.link == Link.CONNECTED }
    val nodes = snapshot?.nodes?.filterNot { it.id == state.connectedNode && it.role == "OSCAR Mobile" }
    if (nodes.isNullOrEmpty()) {
        StatusLabel(if (snapshot == null) "Connect Core to see your other devices." else "No other devices listed.")
    } else {
        Text("Other devices", style = MaterialTheme.typography.titleMedium)
        nodes.forEach { node ->
            var expanded by remember(node.id, state.epoch) { mutableStateOf(false) }
            val active = snapshot?.tasks.orEmpty().filter { (it.target == node.id || it.originNode == node.id) && it.state !in setOf("verified", "partially_verified", "failed", "cancelled") }
            HorizontalDivider()
            FeatureRow(node.role, node.status.replaceFirstChar { it.uppercase() } +
                (if (!node.paired) " · Not paired" else "") +
                (if (active.isNotEmpty()) " · ${active.size} ${if (active.size == 1) "work item" else "work items"}" else ""),
                if (node.role == "OSCAR Mobile") "Phone" else "Devices", action = { expanded = !expanded },
                modifier = Modifier.testTag("device-${node.id}").semantics { stateDescription = if (expanded) "Expanded" else "Collapsed" })
            Column(Modifier.fillMaxWidth().animateContentSize(tween(if (LocalReducedMotion.current) 0 else 200))) {
                if (expanded) {
                    Text("Capabilities", style = MaterialTheme.typography.titleMedium)
                    Text(if (node.capabilities.isEmpty()) "No currently advertised executor capabilities" else node.capabilities.distinct().joinToString("\n"), style = MaterialTheme.typography.bodySmall)
                    active.forEach { Text("${it.label} · ${it.description}", style = MaterialTheme.typography.bodyMedium) }
                    Text("Device ID: ${node.id} · ${if (node.paired) "Paired" else "Not paired"}", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
    if (state.link != Link.CONNECTED) Button(onClick = connect, enabled = state.link != Link.CONNECTING && !state.restoring,
        modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = Sage)) { Text("Connect Core") }
    SupportingDetails("Connection & privacy") {
        if (state.link == Link.CONNECTED) TextButton(onClick = connect) { Text("Change Core connection") }
        TextButton(onClick = disconnect) { Text("Disconnect and remove local credentials") }
        Text("Local disconnect removes this app’s credentials. Remote revocation is a separate Core action.", style = MaterialTheme.typography.bodySmall)
        Text("Background listening, power and wake controls are not enabled here. Cloud, Edge and Home Node appear only when commissioned.", style = MaterialTheme.typography.bodySmall)
    }
}
