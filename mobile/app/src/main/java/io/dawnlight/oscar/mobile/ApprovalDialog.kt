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

@Composable fun ApprovalDialog(approval: Approval, busy: Boolean, current: Boolean, close: () -> Unit, confirm: () -> Unit, replyPreview: String? = null, coreNow: Long = System.currentTimeMillis(), decline: (() -> Unit)? = null) {
    var expired by remember(approval.id) { mutableStateOf(coreNow >= approval.expiresAt) }
    var reviewed by remember(approval.id) { mutableStateOf(approval.review == "{}") }
    LaunchedEffect(approval.id) { delay((approval.expiresAt - coreNow).coerceAtLeast(0)); expired = true }
    key(approval.id) { DetailPage("Decision", close, "approvalDialog") {
        Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                EditorialHeading(when (approval.operation) {
                    "approve" -> "Go ahead?"; "deny" -> "Decline this?"; "cancel" -> "Stop this task?"; "retry" -> "Continue?"; else -> "Send this reply?"
                })
            }
            Illustration(R.drawable.illustration_decision, Modifier.width(112.dp), height = 128.dp)
        }
        SelectionContainer {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                TactileSurface(Modifier.fillMaxWidth()) {
                    Text(if (approval.operation == "reply") "EXACT REPLY" else "REQUEST", style = MaterialTheme.typography.labelSmall)
                    Text(if (approval.operation == "reply" && replyPreview != null) replyPreview else approval.exactRequest.ifEmpty { approval.description }, style = MaterialTheme.typography.titleLarge)
                }
                Text(approval.consequence, style = MaterialTheme.typography.bodyMedium)
                FeatureRow("Target", approval.target, "Devices")
                SupportingDetails("Plan & permission details", onOpen = { reviewed = true }) {
                    if (approval.review != "{}") {
                        Text("Reviewed plan", style = MaterialTheme.typography.titleMedium)
                        ResponseText(approval.review)
                        SupportingDetails("Exact source material") { Text(approval.review) }
                    }
                    Text("Permission scope: ${approval.scope}\nCapability: ${approval.capability}", style = MaterialTheme.typography.bodySmall)
                    Text("${approval.reason}\n${approval.policyReason}", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        StatusLabel(if (expired || !current) "Decision expired or unavailable. Request a fresh review." else "One decision · Android confirmation required")
        if (!reviewed) StatusLabel("Open the plan details before confirming.")
        Button(shape = MaterialTheme.shapes.medium, onClick = confirm, enabled = !busy && current && !expired && reviewed, colors = ButtonDefaults.buttonColors(containerColor = Sage), modifier = Modifier.fillMaxWidth()) { Text(if (approval.operation == "deny") "Confirm denial" else "Confirm securely") }
        decline?.let { TextButton(onClick = it, enabled = !busy && current && !expired) { Text("Review denial") } }
    } }
}
