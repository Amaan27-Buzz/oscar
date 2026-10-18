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
import org.json.JSONObject

@Composable fun DevicesScreen(state: MobileState, connect: () -> Unit, disconnect: () -> Unit, revoke: (() -> Unit)? = null,
    rotate: (() -> Unit)? = null, requestFile: ((String, String, JSONObject) -> Unit)? = null) {
    var request by remember(state.epoch) { mutableStateOf<Pair<CoreNode, String>?>(null) }
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
                state.connectedNode?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
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
                "Cloud", "Core" -> "Cloud" to Clay
                "Edge" -> "Edge" to Lilac
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
                            if (state.remote && node.status == "online" && requestFile != null) {
                                if ("file_read" in node.inputKinds) TextButton(onClick = { request = node to "file_read" }, enabled = !state.busy) { Text("Read a workspace file") }
                                if ("file_write" in node.inputKinds) TextButton(onClick = { request = node to "file_write" }, enabled = !state.busy) { Text("Prepare a workspace edit") }
                            }
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
        if (state.remote && state.link == Link.CONNECTED && revoke != null) TextButton(onClick = revoke, enabled = !state.busy) { Text("Revoke this device and log out") }
        if (state.remote && state.link == Link.CONNECTED && rotate != null) TextButton(onClick = rotate, enabled = !state.busy) { Text("Renew connection credentials") }
        Text("Local disconnect removes this app’s credentials. Remote revocation is a separate Core action.", style = MaterialTheme.typography.bodySmall)
        Text("Background listening, power and wake controls are not enabled here. Cloud, Edge and Home Node appear only when commissioned.", style = MaterialTheme.typography.bodySmall)
    }
    request?.let { (node, kind) ->
        var path by remember(node.id, kind) { mutableStateOf("") }
        var content by remember(node.id, kind) { mutableStateOf("") }
        val write = kind == "file_write"
        val valid = path.length in 1..240 && !path.contains('\\') && !path.contains(':') && !path.contains('\u0000') && path.split('/').all { it !in setOf("", ".", "..") }
        AlertDialog(onDismissRequest = { request = null }, title = { Text(if (write) "Prepare file edit" else "Read workspace file") }, text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${node.role} · ${node.id}")
                OscarField(path, { path = it.take(240) }, "Path inside approved workspace", singleLine = true)
                if (write) OscarField(content, { if (it.toByteArray(Charsets.UTF_8).size <= 8192) content = it }, "Reviewed file content", minLines = 3, maxLines = 5)
                Text(if (write) "Core prepares this exact edit for scoped owner review before execution." else "Core checks permission and verifies a separate readback.", style = MaterialTheme.typography.bodySmall)
            }
        }, dismissButton = { TextButton(onClick = { request = null }) { Text("Cancel") } }, confirmButton = {
            TextButton(enabled = valid, onClick = {
                val parameters = JSONObject().put("path", path)
                if (write) parameters.put("content", content)
                requestFile?.invoke(node.id, kind, parameters); request = null
            }) { Text(if (write) "Prepare for review" else "Request read") }
        })
    }
}
