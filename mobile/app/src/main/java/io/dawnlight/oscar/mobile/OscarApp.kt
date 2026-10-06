package io.dawnlight.oscar.mobile

import android.graphics.Color as AndroidColor
import android.util.Base64
import android.webkit.WebView
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.json.JSONObject

private val Paper = Color(0xFFF5F1E7)
private val Ink = Color(0xFF1A1B18)
@Composable fun OscarTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = lightColorScheme(primary = Ink, onPrimary = Color(0xFFFFFDF8),
        secondary = Color(0xFF1D6FD6), tertiary = Color(0xFFFFC83D), background = Paper,
        surface = Paper, onBackground = Ink, onSurface = Ink, error = Color(0xFFD94F45)),
        shapes = Shapes(small = androidx.compose.foundation.shape.RoundedCornerShape(8.dp), medium = androidx.compose.foundation.shape.RoundedCornerShape(12.dp), large = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)), content = content)
}
@Composable fun OscarApp(session: CoreSession, confirmation: OwnerConfirmation) {
    val state by session.state.collectAsStateWithLifecycle()
    var selected by rememberSaveable { mutableStateOf(Destination.OSCAR.name) }
    var settingsPage by rememberSaveable { mutableStateOf("Settings") }
    var pairing by remember { mutableStateOf(false) }
    var draft by remember { mutableStateOf("") }
    val destination = Destination.entries.firstOrNull { it.name == selected } ?: Destination.OSCAR
    OscarTheme {
        Scaffold(containerColor = Paper, bottomBar = {
            Surface(tonalElevation = 0.dp) {
                Row(Modifier.fillMaxWidth().navigationBarsPadding(), horizontalArrangement = Arrangement.SpaceEvenly) {
                    Destination.entries.forEach { item ->
                        TextButton(onClick = { selected = item.name; settingsPage = "Settings" }, modifier = Modifier.weight(1f).heightIn(min = 56.dp)
                            .semantics { this.selected = item == destination }) { Text(item.label,
                                color = if (item == destination) MaterialTheme.colorScheme.secondary else Ink,
                                fontWeight = if (item == destination) androidx.compose.ui.text.font.FontWeight.SemiBold else androidx.compose.ui.text.font.FontWeight.Normal) }
                    }
                }
            }
        }) { insets ->
            Box(Modifier.fillMaxSize().padding(insets).imePadding(), contentAlignment = Alignment.TopCenter) {
            Column(Modifier.widthIn(max = 720.dp).fillMaxWidth().padding(horizontal = 24.dp)
                .verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Spacer(Modifier.height(8.dp))
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(if (destination == Destination.OSCAR) "OSCAR" else destination.label, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.weight(1f))
                    TextButton(onClick = session::refreshNow, enabled = !state.busy) { Text("Refresh") }
                }
                if (state.link != Link.CONNECTED) {
                    Text(when (state.link) { Link.CONNECTING -> "Connecting to Core"; Link.DEGRADED -> "Core unavailable"; else -> "Connect to your OSCAR Core" }, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
                    TextButton(onClick = { pairing = true }) { Text("Connect Core") }
                }
                when (destination) {
                    Destination.OSCAR -> PresenceScreen(state, draft, { draft = it }, { session.send(draft); draft = "" }, session::cancelRequest,
                        { selected = Destination.ACTIVITY.name }, { selected = Destination.SETTINGS.name; settingsPage = "Voice" })
                    Destination.ACTIVITY -> ActivityScreen(state, session::inspect, session::review)
                    Destination.DEVICES -> DevicesScreen(state, { pairing = true })
                    Destination.SETTINGS -> SettingsScreen(settingsPage, { settingsPage = it }, session, state)
                }
                state.message?.let { Text(it, modifier = Modifier.testTag("message").semantics { liveRegion = LiveRegionMode.Polite }) }
                Spacer(Modifier.height(16.dp))
            }
            }
        }
        if (pairing) PairingDialog({ pairing = false }) { json -> pairing = false; session.connect(json) }
        state.approval?.let { approval ->
            ApprovalDialog(approval, state.busy, session::dismissApproval) {
                val epoch = state.epoch
                confirmation.confirm(approval, { session.complete(approval, epoch) }, { session.dismissApproval(); session.message("Confirmation denied or unavailable. No action is confirmed.") })
            }
        }
    }
}
@Composable private fun PairingDialog(close: () -> Unit, connect: (JSONObject) -> Unit) {
    var origin by remember { mutableStateOf("") }; var node by remember { mutableStateOf("") }
    var id by remember { mutableStateOf("") }; var token by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = close, title = { Text("Connect this phone") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Use a scoped session issued by your trusted Core. This does not grant phone permissions or enroll owner signing authority.")
            OutlinedTextField(origin, { origin = it.take(256) }, label = { Text("Trusted HTTPS Core origin") }, singleLine = true)
            OutlinedTextField(node, { node = it.take(80) }, label = { Text("Paired node ID") }, singleLine = true)
            OutlinedTextField(id, { id = it.take(80) }, label = { Text("Session ID") }, singleLine = true)
            OutlinedTextField(token, { token = it.take(200) }, label = { Text("Scoped session token") }, singleLine = true,
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation(),
                keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = androidx.compose.ui.text.input.KeyboardType.Password))
        }
    }, dismissButton = { TextButton(onClick = close) { Text("Cancel") } }, confirmButton = {
        TextButton(enabled = listOf(origin, node, id, token).none { it.isBlank() }, onClick = {
            connect(JSONObject().put("url", origin).put("node_id", node).put("session_id", id).put("token", token))
        }) { Text("Connect") }
    })
}
@Composable private fun ApprovalDialog(approval: Approval, busy: Boolean, close: () -> Unit, confirm: () -> Unit) {
    AlertDialog(onDismissRequest = close, title = { Text("Review ${approval.operation}") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(approval.description, style = MaterialTheme.typography.titleMedium)
            Text("Why: ${approval.reason}")
            Text("Source: OSCAR Core · ${approval.capability}\nTarget: ${approval.target}")
            Text("Consequence: ${approval.consequence}")
            Text(approval.policyReason)
            Text("Confirm with biometric or phone PIN. This approves one current decision and grants no permanent authority.")
        }
    }, dismissButton = { TextButton(onClick = close) { Text("Back") } }, confirmButton = {
        TextButton(onClick = confirm, enabled = !busy) { Text("Confirm securely") }
    })
}
@Composable fun OscarOrb(presence: Presence) {
    val context = LocalContext.current
    AndroidView(modifier = Modifier.size(144.dp).testTag("orb").semantics { contentDescription = "OSCAR presence"; stateDescription = presence.name.lowercase() }, factory = {
        WebView(context).apply {
            setBackgroundColor(AndroidColor.TRANSPARENT)
            settings.javaScriptEnabled = false; settings.allowFileAccess = false; settings.allowContentAccess = false; settings.blockNetworkLoads = true
            importantForAccessibility = android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO
            val svg = context.assets.open("oscar-orb.svg").use { it.readBytes() }
            val encoded = Base64.encodeToString(svg, Base64.NO_WRAP)
            loadDataWithBaseURL(null, "<html style='height:100%'><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='height:100%;margin:0;background:transparent'><img style='width:100%;height:100%;object-fit:contain' src='data:image/svg+xml;base64,$encoded'></body></html>", "text/html", "UTF-8", null)
        }
    }, update = { it.alpha = if (presence in setOf(Presence.UNAVAILABLE, Presence.MUTED)) 0.55f else 1f }, onRelease = { it.destroy() })
}
