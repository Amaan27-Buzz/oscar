package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.clickable
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp

@Composable fun DevicesScreen(state: MobileState, connect: () -> Unit, disconnect: () -> Unit) {
    Text("Connection Grid", style = MaterialTheme.typography.titleMedium)
    if (state.snapshot == null) Text("No current Grid snapshot is available.")
    state.snapshot?.nodes?.sortedBy { if (it.id == state.connectedNode) 0 else 1 }?.forEach { node ->
        var expanded by remember(node.id, state.epoch) { mutableStateOf(false) }
        val active = state.snapshot.tasks.filter { (it.target == node.id || it.originNode == node.id) && it.state !in setOf("verified", "partially_verified", "failed", "cancelled") }
        ListItem(headlineContent = { Text(if (node.id == state.connectedNode && node.role == "OSCAR Mobile") "This phone" else node.role) },
            supportingContent = { Text("${node.status} · ${if (node.paired) "Paired" else "Not paired"}${if (active.isNotEmpty()) " · ${active.size} active tasks" else ""}") },
            leadingContent = { OscarIcon(if (node.role == "OSCAR Mobile") "phone" else "desktop") }, trailingContent = { OscarIcon("chevron") },
            colors = ListItemDefaults.colors(containerColor = androidx.compose.ui.graphics.Color.Transparent),
            modifier = Modifier.fillMaxWidth().clickable { expanded = !expanded }.heightIn(min = 80.dp).testTag("device-${node.id}"))
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
        Text("Opening OSCAR does not enable background listening.", style = MaterialTheme.typography.bodySmall)
        Text("Remote node revocation requires trusted Core administration; this Mobile API does not expose it. Local removal is not remote revocation.", style = MaterialTheme.typography.bodySmall)
        Text("Home Node · unsupported until commissioned. Cloud and Edge appear only when actually configured.", style = MaterialTheme.typography.bodySmall)
    }
}
