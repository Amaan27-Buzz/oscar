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
        IllustratedIntro(when (approval.operation) {
            "approve" -> "Go ahead?"; "deny" -> "Decline this?"; "cancel" -> "Stop this task?"; "retry" -> "Continue?"; else -> "Send this reply?"
        }, artwork = R.drawable.illustration_decision, height = 144.dp)
        SelectionContainer {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                TactileSurface(Modifier.fillMaxWidth()) {
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                        IconBadge(if (approval.operation == "reply") "Conversation" else "Document", Powder, 40.dp)
                        Text(if (approval.operation == "reply") "EXACT REPLY" else "REQUEST", style = MaterialTheme.typography.labelLarge)
                    }
                    Text(if (approval.operation == "reply" && replyPreview != null) replyPreview else approval.exactRequest.ifEmpty { approval.description }, style = MaterialTheme.typography.titleLarge)
                }
                Text(approval.consequence, style = MaterialTheme.typography.bodyMedium)
                FeatureRow("Target", approval.target, "Devices", Lilac)
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
        OscarButton(onClick = confirm, enabled = !busy && current && !expired && reviewed, modifier = Modifier.fillMaxWidth()) {
            Glyph("Check"); Text(if (approval.operation == "deny") "Confirm denial" else "Confirm securely")
        }
        decline?.let { OscarButton(onClick = it, enabled = !busy && current && !expired, outlined = true, modifier = Modifier.fillMaxWidth()) {
            Glyph("Close"); Text("Review denial")
        } }
    } }
}
