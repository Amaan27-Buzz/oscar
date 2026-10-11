package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.json.JSONObject
import io.dawnlight.oscar.expression.ExpressionPresence
import androidx.compose.ui.unit.Dp
import androidx.activity.compose.BackHandler

private val Paper = Color(0xFFF5F1E7)
private val Ink = Color(0xFF1A1B18)
@Composable fun OscarTheme(content: @Composable () -> Unit) {
    val activity = androidx.activity.compose.LocalActivity.current
    val appearance = appearancePreference("theme", "system")
    val dark = appearance == "dark" || (appearance == "system" && isSystemInDarkTheme())
    SideEffect {
        val mask = android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
        activity?.window?.insetsController?.setSystemBarsAppearance(if (dark) 0 else mask, mask)
    }
    val owner = androidx.lifecycle.compose.LocalLifecycleOwner.current
    var systemMotionOff by remember { mutableStateOf(!android.animation.ValueAnimator.areAnimatorsEnabled()) }
    DisposableEffect(owner) {
        val observer = androidx.lifecycle.LifecycleEventObserver { _, event ->
            if (event == androidx.lifecycle.Lifecycle.Event.ON_RESUME) systemMotionOff = !android.animation.ValueAnimator.areAnimatorsEnabled()
        }
        owner.lifecycle.addObserver(observer)
        onDispose { owner.lifecycle.removeObserver(observer) }
    }
    val reduced = appearancePreference("motion", "system") == "reduced" || systemMotionOff
    CompositionLocalProvider(LocalReducedMotion provides reduced) {
    MaterialTheme(colorScheme = if (dark) darkColorScheme(primary = Color(0xFFF0EEE6), onPrimary = Ink,
        secondary = Color(0xFF86B8F7), tertiary = Color(0xFFFFCF5A), background = Color(0xFF191B19),
        surface = Color(0xFF191B19), surfaceContainer = Color(0xFF242723), surfaceContainerHigh = Color(0xFF292C27),
        surfaceContainerHighest = Color(0xFF30342D), surfaceContainerLow = Color(0xFF20231E), surfaceContainerLowest = Color(0xFF151713),
        surfaceTint = Color.Transparent, onBackground = Color(0xFFF0EEE6), onSurface = Color(0xFFF0EEE6), onSurfaceVariant = Color(0xFFC2C4B9),
        outline = Color(0xFF999D8D), outlineVariant = Color(0xFF44493C), error = Color(0xFFFFB4A9)) else lightColorScheme(primary = Ink, onPrimary = Color(0xFFFFFDF8),
        secondary = Color(0xFF1B68C8), tertiary = Color(0xFFFFC83D), background = Paper,
        surface = Paper, surfaceContainer = Color(0xFFFAF7EF), surfaceContainerHigh = Color(0xFFFAF7EF),
        surfaceContainerHighest = Color(0xFFFFFDF8), surfaceContainerLow = Paper, surfaceContainerLowest = Color(0xFFFFFDF8),
        surfaceTint = Color.Transparent, onBackground = Ink, onSurface = Ink, onSurfaceVariant = Color(0xFF625F57),
        outline = Color(0xFF8B877E), outlineVariant = Color(0xFFDDD7CA), error = Color(0xFFB6322B)),
        shapes = Shapes(small = androidx.compose.foundation.shape.RoundedCornerShape(8.dp), medium = androidx.compose.foundation.shape.RoundedCornerShape(12.dp), large = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)), content = content)
    }
}
@Composable fun OscarApp(session: CoreSession, confirmation: OwnerConfirmation) {
    val state by session.state.collectAsStateWithLifecycle()
    var selected by rememberSaveable { mutableStateOf(Destination.OSCAR.name) }
    var settingsPage by rememberSaveable { mutableStateOf("Settings") }
    var voiceOpen by remember(state.epoch) { mutableStateOf(false) }
    DisposableEffect(state.epoch) { onDispose { VoicePresentation.cancel(session.getApplication()) } }
    var pairing by remember { mutableStateOf(false) }
    val draft = state.draft
    val destination = Destination.entries.firstOrNull { it.name == selected } ?: Destination.OSCAR
    val window = LocalWindowInfo.current.containerSize
    val widthDp = with(LocalDensity.current) { window.width.toDp() }
    val heightDp = with(LocalDensity.current) { window.height.toDp() }
    val focus = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    BackHandler(voiceOpen || destination != Destination.OSCAR || settingsPage != "Settings") {
        if (voiceOpen) { VoicePresentation.cancel(session.getApplication()); voiceOpen = false } else if (settingsPage != "Settings") settingsPage = "Settings" else selected = Destination.OSCAR.name
    }
    OscarTheme {
        Scaffold(modifier = Modifier.imePadding(), containerColor = MaterialTheme.colorScheme.background, bottomBar = {
            Surface(tonalElevation = 0.dp) {
                BoxWithConstraints(Modifier.fillMaxWidth().navigationBarsPadding()) {
                val columns = if (LocalDensity.current.fontScale > 1.3f && maxWidth < 600.dp) 2 else 4
                FlowRow(Modifier.fillMaxWidth(), maxItemsInEachRow = columns, horizontalArrangement = Arrangement.SpaceEvenly) {
                    Destination.entries.forEach { item ->
                        TextButton(onClick = { VoicePresentation.cancel(session.getApplication()); voiceOpen = false; focus.clearFocus(); keyboard?.hide(); selected = item.name; settingsPage = "Settings" }, modifier = Modifier.fillMaxWidth(1f / columns).heightIn(min = 56.dp).testTag("destination-${item.name}")
                            .semantics { this.selected = item == destination }) { Text(item.label,
                                color = if (item == destination) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.onSurface,
                                fontWeight = if (item == destination) androidx.compose.ui.text.font.FontWeight.SemiBold else androidx.compose.ui.text.font.FontWeight.Normal) }
                    }
                }
                }
            }
        }) { insets ->
            Box(Modifier.fillMaxSize().padding(insets), contentAlignment = Alignment.TopCenter) {
            Column(Modifier.widthIn(max = 720.dp).fillMaxWidth().padding(horizontal = if (widthDp < 360.dp) 16.dp else 24.dp)
                .verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Spacer(Modifier.height(8.dp))
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text(if (destination == Destination.OSCAR) "OSCAR" else destination.label, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.weight(1f).semantics { heading() })
                    TextButton(onClick = session::refreshNow, enabled = !state.busy) { Text("Refresh") }
                }
                OscarOrb(state, composing = draft.isNotBlank(), size = if (destination == Destination.OSCAR) { if (heightDp < 420.dp) 72.dp else 108.dp } else 40.dp)
                if (state.link != Link.CONNECTED) {
                    Text(when (state.link) { Link.CONNECTING -> "Connecting to Core"; Link.DEGRADED -> "Core unavailable"; else -> "Connect to your OSCAR Core" }, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
                    TextButton(onClick = { pairing = true }) { Text("Connect Core") }
                }
                when (destination) {
                    Destination.OSCAR -> if (voiceOpen) VoiceExperience({ voiceOpen = false }, { VoicePresentation.cancel(session.getApplication()); voiceOpen = false; selected = Destination.SETTINGS.name; settingsPage = "Privacy" }) else PresenceScreen(state, draft, session::writeDraft, { focus.clearFocus(); keyboard?.hide(); session.send(draft) }, session::cancelRequest,
                        { focus.clearFocus(); keyboard?.hide(); selected = Destination.ACTIVITY.name }, { focus.clearFocus(); keyboard?.hide(); voiceOpen = true })
                    Destination.ACTIVITY -> ActivityScreen(state, session::inspect, session::review)
                    Destination.DEVICES -> DevicesScreen(state, { pairing = true }, session::disconnect)
                    Destination.SETTINGS -> SettingsScreen(settingsPage, { settingsPage = it }, session, state)
                }
                state.message?.let { Text(it, modifier = Modifier.testTag("message").semantics { liveRegion = LiveRegionMode.Polite }) }
                if (draft.isNotEmpty() || state.interactions.isNotEmpty() || state.privateSuppressed) {
                    TextButton(onClick = session::discard) { Text(if (state.privateSuppressed) "Clear Core private context" else "Discard private interaction") }
                }
                Spacer(Modifier.height(16.dp))
            }
            }
        }
        if (pairing) PairingDialog({ pairing = false }) { json -> pairing = false; session.connect(json) }
        state.inspected?.let { TaskInspector(it, session::closeInspector) }
        state.approval?.let { approval ->
            DisposableEffect(state.epoch, approval.id) { onDispose { confirmation.cancel() } }
            ApprovalDialog(approval, state.busy, approval.current(state, System.currentTimeMillis()), session::dismissApproval, confirm = {
                val epoch = state.epoch
                confirmation.confirm(approval, { session.complete(approval, epoch) }, {
                    if (session.state.value.epoch == epoch && session.state.value.approval == approval) {
                        session.dismissApproval(); session.message("Android confirmation was denied or unavailable. This phone granted no consent.")
                    }
                })
            }, replyPreview = state.replyPreview, coreNow = state.coreNow(System.currentTimeMillis()))
        }
    }
}
@Composable private fun PairingDialog(close: () -> Unit, connect: (JSONObject) -> Unit) {
    var origin by remember { mutableStateOf("") }; var node by remember { mutableStateOf("") }
    var id by remember { mutableStateOf("") }; var token by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = close, title = { Text("Connect this phone") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Use a scoped session issued by your trusted Core. This does not grant phone permissions or enroll owner signing authority.")
            Text("Connecting a different source clears the previous private draft and readback.")
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
@Composable fun OscarOrb(state: MobileState, composing: Boolean = false, size: Dp = 108.dp, reduced: Boolean = LocalReducedMotion.current) {
    val voice by VoicePresentation.state.collectAsStateWithLifecycle()
    val adapter = remember(state.epoch) { MobileExpression(state.epoch) }
    val event = remember(state, composing, reduced, voice) { adapter.event(state, System.currentTimeMillis(), composing, reduced, voice.phase) }
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
        ExpressionPresence(event, adapter.source, size, reduced, Modifier.testTag("orb"))
    }
}
