package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.background
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
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
@Composable fun OscarTheme(forceDark: Boolean = false, content: @Composable () -> Unit) {
    val activity = androidx.activity.compose.LocalActivity.current
    val appearance = appearancePreference("theme", "system")
    val dark = forceDark || appearance == "dark" || (appearance == "system" && isSystemInDarkTheme())
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
        secondary = Color(0xFF86B8F7), secondaryContainer = Color(0xFF384B3C), onSecondaryContainer = Color(0xFFF0EEE6), tertiary = Color(0xFFFFCF5A), background = Color(0xFF191B19),
        surface = Color(0xFF191B19), surfaceContainer = Color(0xFF242723), surfaceContainerHigh = Color(0xFF292C27),
        surfaceContainerHighest = Color(0xFF30342D), surfaceContainerLow = Color(0xFF20231E), surfaceContainerLowest = Color(0xFF151713),
        surfaceTint = Color.Transparent, onBackground = Color(0xFFF0EEE6), onSurface = Color(0xFFF0EEE6), onSurfaceVariant = Color(0xFFC2C4B9),
        outline = Color(0xFF999D8D), outlineVariant = Color(0xFF44493C), error = Color(0xFFFFB4A9)) else lightColorScheme(primary = Ink, onPrimary = Color(0xFFFFFDF8),
        secondary = Color(0xFF1769C4), secondaryContainer = Powder, onSecondaryContainer = Ink, tertiary = Color(0xFFFFC83D), background = Paper,
        surface = Paper, surfaceContainer = Color(0xFFFAF7EF), surfaceContainerHigh = Color(0xFFFAF7EF),
        surfaceContainerHighest = Color(0xFFFFFDF8), surfaceContainerLow = Paper, surfaceContainerLowest = Color(0xFFFFFDF8),
        surfaceTint = Color.Transparent, onBackground = Ink, onSurface = Ink, onSurfaceVariant = Color(0xFF625F57),
        outline = Color(0xFF8B877E), outlineVariant = Color(0xFFDDD7CA), error = Color(0xFFB6322B)),
        typography = OscarTypography, shapes = Shapes(small = androidx.compose.foundation.shape.RoundedCornerShape(8.dp), medium = androidx.compose.foundation.shape.RoundedCornerShape(12.dp), large = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)), content = content)
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
    var conversationPage by rememberSaveable { mutableStateOf("Conversation") }
    var automationPage by remember(state.epoch) { mutableStateOf("Overview") }
    val pageScroll = remember(destination, settingsPage, conversationPage, automationPage) { androidx.compose.foundation.ScrollState(0) }
    val focus = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    fun navigate(item: Destination) {
        VoicePresentation.cancel(session.getApplication()); voiceOpen = false
        focus.clearFocus(); keyboard?.hide(); selected = item.name; settingsPage = "Settings"; conversationPage = "Conversation"; automationPage = "Overview"
    }
    BackHandler(voiceOpen || destination != Destination.OSCAR || settingsPage != "Settings" || conversationPage != "Conversation") {
        if (voiceOpen) { VoicePresentation.cancel(session.getApplication()); voiceOpen = false }
        else if (settingsPage != "Settings") settingsPage = "Settings"
        else if (conversationPage != "Conversation") conversationPage = "Conversation"
        else navigate(Destination.OSCAR)
    }
    val send = { focus.clearFocus(); keyboard?.hide(); session.send(draft); Unit }
    OscarTheme(forceDark = destination == Destination.ACTIVITY || voiceOpen || (destination == Destination.SETTINGS && settingsPage == "Awareness")) {
        Scaffold(modifier = Modifier.imePadding(), containerColor = MaterialTheme.colorScheme.background, bottomBar = {
            if (!voiceOpen) Surface(color = MaterialTheme.colorScheme.background) {
                Row(Modifier.fillMaxWidth().navigationBarsPadding().padding(horizontal = 16.dp)) {
                    listOf(Destination.OSCAR, Destination.AUTOMATIONS, Destination.ACTIVITY).forEach { item ->
                        val navColor by animateColorAsState(if (item == destination) MaterialTheme.colorScheme.secondaryContainer else Color.Transparent,
                            tween(if (LocalReducedMotion.current) 0 else 180), label = "navigationSelection")
                        TextButton(onClick = { navigate(item) }, modifier = Modifier.weight(1f).heightIn(min = 64.dp)
                            .testTag("destination-${item.name}").semantics { this.selected = item == destination }) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Box(Modifier.size(width = 56.dp, height = 30.dp).background(navColor, CircleShape), contentAlignment = Alignment.Center) {
                                    Glyph(item.label, color = if (item == destination) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                                Text(item.label, style = MaterialTheme.typography.labelSmall,
                                    color = if (item == destination) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
            }
        }) { insets ->
            Column(Modifier.fillMaxSize().padding(insets).widthIn(max = 720.dp)) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                    if (destination in setOf(Destination.DEVICES, Destination.SETTINGS) || conversationPage != "Conversation") {
                        IconButton(onClick = { navigate(Destination.OSCAR) }, modifier = Modifier.semantics { contentDescription = "Back to conversation" }) { Glyph("Back") }
                    }
                    Text(if (voiceOpen) "Voice" else if (destination == Destination.OSCAR) "OSCAR" else destination.label, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    IconButton(onClick = { navigate(Destination.DEVICES) }, modifier = Modifier.testTag("destination-DEVICES").semantics { contentDescription = "Devices" }) { Glyph("Devices") }
                    IconButton(onClick = { navigate(Destination.SETTINGS) }, modifier = Modifier.testTag("destination-SETTINGS").semantics { contentDescription = "Preferences" }) { Glyph("Preferences") }
                }
                Column(Modifier.weight(1f).fillMaxWidth().then(pageEntrance("$selected/$settingsPage/$conversationPage/$automationPage/$voiceOpen/${state.epoch}")).verticalScroll(pageScroll)
                    .padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Spacer(Modifier.height(4.dp))
                    if (destination == Destination.OSCAR && conversationPage == "Conversation" && !voiceOpen && state.interactions.isNotEmpty()) {
                        OscarOrb(state, composing = draft.isNotBlank(), size = 36.dp)
                    }
                    when (destination) {
                        Destination.OSCAR -> if (voiceOpen) VoiceExperience(state, { voiceOpen = false }, {
                            navigate(Destination.SETTINGS); settingsPage = "Privacy"
                        }) else if (conversationPage == "Today") TodayScreen(state, { conversationPage = "Conversation" }, { navigate(Destination.ACTIVITY) })
                        else PresenceScreen(state, draft, session::writeDraft, send, session::cancelRequest,
                            { navigate(Destination.ACTIVITY) }, { focus.clearFocus(); keyboard?.hide(); voiceOpen = true }, false, { conversationPage = "Today" })
                        Destination.AUTOMATIONS -> AutomationsScreen(state, automationPage, { automationPage = it }) { text -> session.writeDraft(text); navigate(Destination.OSCAR) }
                        Destination.ACTIVITY -> ActivityScreen(state, session::inspect, session::review)
                        Destination.DEVICES -> DevicesScreen(state, { pairing = true }, session::disconnect)
                        Destination.SETTINGS -> SettingsScreen(settingsPage, { settingsPage = it }, session, state)
                    }
                    if (state.link != Link.CONNECTED && destination in setOf(Destination.OSCAR, Destination.ACTIVITY) && !voiceOpen && conversationPage == "Conversation") {
                        if (state.link == Link.CONNECTING) StatusLabel("Connecting to Core")
                        TextButton(onClick = { pairing = true }) { Text("Connect Core") }
                    }
                    state.message?.let { Text(it, style = MaterialTheme.typography.bodySmall, modifier = Modifier.testTag("message").semantics { liveRegion = LiveRegionMode.Polite }) }
                    if (draft.isNotEmpty() || state.interactions.isNotEmpty() || state.privateSuppressed) {
                        TextButton(onClick = session::discard) { Text(if (state.privateSuppressed) "Clear Core private context" else "Discard private interaction") }
                    }
                    Spacer(Modifier.height(12.dp))
                }
                if (destination == Destination.OSCAR && !voiceOpen && conversationPage == "Conversation") {
                    Box(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp)) {
                        ConversationComposer(state, draft, session::writeDraft, send) { focus.clearFocus(); keyboard?.hide(); voiceOpen = true }
                    }
                }
            }
        }
        if (pairing) PairingDialog({ pairing = false }) { json -> pairing = false; session.connect(json) }
        state.inspected?.let { TaskInspector(it, session::closeInspector, { task, action -> session.closeInspector(); session.review(task, action) }, state.link == Link.CONNECTED && !state.busy) }
        state.approval?.let { approval ->
            DisposableEffect(state.epoch, approval.id) { onDispose { confirmation.cancel() } }
            ApprovalDialog(approval, state.busy, approval.current(state, System.currentTimeMillis()), session::dismissApproval, confirm = {
                val epoch = state.epoch
                confirmation.confirm(approval, { session.complete(approval, epoch) }, {
                    if (session.state.value.epoch == epoch && session.state.value.approval == approval) {
                        session.dismissApproval(); session.message("Android confirmation was denied or unavailable. This phone granted no consent.")
                    }
                })
            }, replyPreview = state.replyPreview, coreNow = state.coreNow(System.currentTimeMillis()), decline =
                state.snapshot?.tasks?.firstOrNull { task -> approval.operation == "approve" && task.id == approval.material().getString("task_id") && "deny" in task.actions }
                    ?.let { task -> { session.dismissApproval(); session.review(task, "deny") } })
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
