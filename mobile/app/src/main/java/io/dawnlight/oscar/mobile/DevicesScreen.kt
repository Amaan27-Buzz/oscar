package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp

@Composable fun DevicesScreen(state: MobileState, connect: () -> Unit, disconnect: () -> Unit) {
    Text("Connection Grid", style = MaterialTheme.typography.headlineLarge)
    Text("This Android surface", style = MaterialTheme.typography.titleMedium)
    Text(if (state.link == Link.CONNECTED) "Here · scoped Core session connected" else "App open · Core connection unavailable")
    Text("Opening OSCAR does not imply background listening or continuous availability.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    if (state.snapshot == null) Text("No current Grid snapshot is available.")
    state.snapshot?.nodes?.sortedBy { if (it.id == state.connectedNode) 0 else 1 }?.forEach { node ->
        var expanded by remember(node.id, state.epoch) { mutableStateOf(false) }
        val active = state.snapshot.tasks.filter { (it.target == node.id || it.originNode == node.id) && it.state !in setOf("verified", "partially_verified", "failed", "cancelled") }
        HorizontalDivider()
        TextButton(onClick = { expanded = !expanded }, contentPadding = PaddingValues(vertical = 16.dp), modifier = Modifier.fillMaxWidth().heightIn(min = 64.dp).testTag("device-${node.id}")) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp), horizontalAlignment = androidx.compose.ui.Alignment.Start) {
                Text(if (node.id == state.connectedNode && node.role == "OSCAR Mobile") "This phone" else node.role, style = MaterialTheme.typography.titleMedium)
                Text("${node.status} · ${if (node.paired) "Paired" else "Not paired"}${if (active.isNotEmpty()) " · ${active.size} associated active tasks" else ""}")
            }
            OscarIcon("chevron")
        }
        if (expanded) {
            Text(node.id, style = MaterialTheme.typography.bodySmall)
            Text(if (node.capabilities.isEmpty()) "No currently advertised executor capabilities" else node.capabilities.distinct().joinToString("\n"))
            active.forEach { Text("${it.label} · ${it.description}") }
            Text("Supervise authorized tasks in Activity. No power or wake command is exposed by this Mobile contract.", style = MaterialTheme.typography.bodySmall)
        }
    }
    HorizontalDivider()
    TextButton(onClick = connect) { Text("Connect this phone") }
    TextButton(onClick = disconnect) { Text("Disconnect and remove local credentials") }
    Disclosure("Connection boundaries") {
        Text("Remote node revocation requires trusted Core administration; this Mobile API does not expose it. Local removal is not remote revocation.", style = MaterialTheme.typography.bodySmall)
        Text("Home Node · unsupported until commissioned. Cloud and Edge appear only when actually configured.", style = MaterialTheme.typography.bodySmall)
    }
}
