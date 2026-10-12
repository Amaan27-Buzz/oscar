package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay

@Composable fun ApprovalDialog(approval: Approval, busy: Boolean, current: Boolean, close: () -> Unit, confirm: () -> Unit, replyPreview: String? = null, coreNow: Long = System.currentTimeMillis()) {
    var expired by remember(approval.id) { mutableStateOf(coreNow >= approval.expiresAt) }
    LaunchedEffect(approval.id) { delay((approval.expiresAt - coreNow).coerceAtLeast(0)); expired = true }
    androidx.compose.ui.window.Dialog(onDismissRequest = close, properties = androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth = false)) {
    Surface(Modifier.fillMaxSize().testTag("approvalDialog"), color = MaterialTheme.colorScheme.background) {
    Column(Modifier.safeDrawingPadding().padding(24.dp)) {
        Text(when (approval.operation) {
        "approve" -> "Review request"; "deny" -> "Decline request"; "cancel" -> "Cancel task"; "retry" -> "Review continuation"; else -> "Review reply"
        }, style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(24.dp))
        SelectionContainer(Modifier.weight(1f)) {
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(approval.description, style = MaterialTheme.typography.titleMedium)
                Surface(color = MaterialTheme.colorScheme.tertiaryContainer, shape = MaterialTheme.shapes.small) {
                    Text("Consequence: ${approval.consequence}", modifier = Modifier.padding(16.dp), style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onTertiaryContainer)
                }
                if (approval.exactRequest.isNotEmpty()) { Text("Exact request", style = MaterialTheme.typography.titleSmall); Text(approval.exactRequest) }
                if (approval.operation == "reply" && replyPreview != null) { Text("Exact reply", style = MaterialTheme.typography.titleSmall); Text(replyPreview) }
                if (approval.review != "{}") { Text("Exact plan material", style = MaterialTheme.typography.titleSmall); Text(approval.review) }
                HorizontalDivider()
                Disclosure("Scope & policy") {
                    Text("Target: ${approval.target}\nPermission scope: ${approval.scope}\nCapability: ${approval.capability}")
                    Text("Why: ${approval.reason}\n${approval.policyReason}")
                }
                Text(if (expired || !current) "This decision is unavailable or expired. Inspect current state for a new review."
                    else "Opening this review grants no consent. Android biometric or device credential confirms one current decision; no permanent authority is granted.")
            }
        }
        HorizontalDivider(Modifier.padding(vertical = 16.dp))
        FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TextButton(onClick = close, modifier = Modifier.heightIn(min = 48.dp)) { Text("Back") }
            Button(onClick = confirm, enabled = !busy && current && !expired, shape = MaterialTheme.shapes.small, modifier = Modifier.heightIn(min = 48.dp)) {
                Text(if (approval.operation == "deny") "Confirm denial" else "Confirm securely")
            }
        }
    }
    }
    }
}
