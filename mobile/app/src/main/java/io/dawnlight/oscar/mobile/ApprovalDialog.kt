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
    LaunchedEffect(approval.id) { delay((approval.expiresAt - coreNow).coerceAtLeast(0)); expired = true }
    DetailPage("Decision", close, "approvalDialog") {
        Illustration(R.drawable.illustration_decision, height = 160.dp)
        EditorialHeading(when (approval.operation) {
        "approve" -> "Review request"; "deny" -> "Decline request"; "cancel" -> "Cancel task"; "retry" -> "Review continuation"; else -> "Review reply"
        })
        SelectionContainer {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(approval.description, style = MaterialTheme.typography.titleMedium)
                Text("Consequence: ${approval.consequence}")
                Text("Target: ${approval.target}\nPermission scope: ${approval.scope}\nCapability: ${approval.capability}")
                if (approval.exactRequest.isNotEmpty()) { Text("Exact request", style = MaterialTheme.typography.titleSmall); Text(approval.exactRequest) }
                if (approval.operation == "reply" && replyPreview != null) { Text("Exact reply", style = MaterialTheme.typography.titleSmall); Text(replyPreview) }
                if (approval.review != "{}") {
                    Text("Reviewed plan", style = MaterialTheme.typography.titleSmall)
                    ResponseText(approval.review)
                    SupportingDetails("Exact source material") { Text(approval.review) }
                }
                Text("Why: ${approval.reason}\n${approval.policyReason}")
                Text(if (expired || !current) "This decision is unavailable or expired. Inspect current state for a new review."
                    else "Opening this review grants no consent. Android biometric or device credential confirms one current decision; no permanent authority is granted.")
            }
        }
        Button(shape = MaterialTheme.shapes.medium, onClick = confirm, enabled = !busy && current && !expired, colors = ButtonDefaults.buttonColors(containerColor = Sage), modifier = Modifier.fillMaxWidth()) { Text(if (approval.operation == "deny") "Confirm denial" else "Confirm securely") }
        decline?.let { TextButton(onClick = it, enabled = !busy && current && !expired) { Text("Review denial") } }
        TextButton(onClick = close) { Text("Back") }
    }
}
