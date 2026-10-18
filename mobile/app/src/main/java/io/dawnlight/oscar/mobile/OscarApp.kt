package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
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
@Composable fun OscarTheme(preferDark: Boolean = false, content: @Composable () -> Unit) {
    val activity = androidx.activity.compose.LocalActivity.current
    val appearance = appearancePreference("theme", "system")
    // Explicit choices win; System retains the approved immersive graphite compositions.
    val dark = when (appearance) { "light" -> false; "dark" -> true; else -> preferDark || isSystemInDarkTheme() }
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
    var settingsParent by rememberSaveable { mutableStateOf("Settings") }
    var primaryDestination by rememberSaveable { mutableStateOf(Destination.OSCAR.name) }
    var voiceOpen by remember(state.epoch) { mutableStateOf(false) }
    DisposableEffect(state.epoch) { onDispose { VoicePresentation.cancel(session.getApplication()) } }
    var pairing by remember { mutableStateOf(false) }
    val draft = state.draft
    val destination = Destination.entries.firstOrNull { it.name == selected } ?: Destination.OSCAR
    var conversationPage by rememberSaveable { mutableStateOf("Conversation") }
    var automationPage by remember(state.epoch) { mutableStateOf("Overview") }
    val pageScroll = remember(destination, settingsPage, conversationPage, automationPage, voiceOpen) { androidx.compose.foundation.ScrollState(0) }
    val focus = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    fun navigate(item: Destination) {
        VoicePresentation.cancel(session.getApplication()); voiceOpen = false
        focus.clearFocus(); keyboard?.hide(); selected = item.name; settingsPage = "Settings"; settingsParent = "Settings"; conversationPage = "Conversation"; automationPage = "Overview"
        if (item in setOf(Destination.OSCAR, Destination.AUTOMATIONS, Destination.ACTIVITY)) primaryDestination = item.name
    }
    val primaryPage = !voiceOpen && when (destination) {
        Destination.OSCAR -> conversationPage == "Conversation"
        Destination.AUTOMATIONS -> automationPage == "Overview"
        Destination.ACTIVITY -> true
        else -> false
    }
    fun back() {
        focus.clearFocus(); keyboard?.hide()
        when {
            voiceOpen -> { VoicePresentation.cancel(session.getApplication()); voiceOpen = false }
            destination == Destination.SETTINGS && settingsPage != "Settings" -> { settingsPage = settingsParent; settingsParent = "Settings" }
            destination == Destination.AUTOMATIONS && automationPage != "Overview" -> automationPage = "Overview"
            destination == Destination.OSCAR && conversationPage != "Conversation" -> conversationPage = "Conversation"
            else -> navigate(Destination.entries.firstOrNull { it.name == primaryDestination } ?: Destination.OSCAR)
        }
    }
    BackHandler(!primaryPage || destination != Destination.OSCAR) { if (primaryPage) navigate(Destination.OSCAR) else back() }
    val notices = remember(state.epoch) { SnackbarHostState() }
    LaunchedEffect(state.epoch, state.message) {
        state.message?.takeIf { it.isNotBlank() }?.let { notices.showSnackbar(it, withDismissAction = true, duration = SnackbarDuration.Long) }
    }
    val send = { focus.clearFocus(); keyboard?.hide(); session.send(draft); Unit }
    OscarTheme(preferDark = destination == Destination.ACTIVITY || voiceOpen || (destination == Destination.SETTINGS && settingsPage == "Awareness")) {
        val pageArtwork = when {
            voiceOpen -> null
            destination == Destination.OSCAR && conversationPage == "Today" -> R.drawable.illustration_today
            destination == Destination.OSCAR && state.interactions.isEmpty() && draft.isBlank() -> R.drawable.illustration_home
            destination == Destination.DEVICES -> R.drawable.illustration_devices
            destination == Destination.AUTOMATIONS -> when (automationPage) {
                "Worker" -> R.drawable.illustration_worker
                "Create" -> R.drawable.oscar_orb
                else -> R.drawable.illustration_automations
            }
            destination == Destination.SETTINGS -> when (settingsPage) {
                "Settings", "Voice" -> R.drawable.illustration_preferences
                "Awareness" -> R.drawable.illustration_awareness
                "Access" -> R.drawable.oscar_orb
                "Memory" -> R.drawable.illustration_reading
                else -> null
            }
            else -> null
        }
        CompositionLocalProvider(LocalPageArtwork provides pageArtwork) {
        Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        PageArtwork(pageArtwork, pageScroll, state)
        Scaffold(modifier = Modifier.imePadding(), containerColor = Color.Transparent, contentColor = MaterialTheme.colorScheme.onBackground,
            bottomBar = {
            if (primaryPage) PrimaryNavigation(destination, ::navigate)
        }) { insets ->
            Column(Modifier.fillMaxSize().padding(insets).widthIn(max = 720.dp)) {
                Row(Modifier.fillMaxWidth().testTag("app-toolbar").padding(horizontal = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                    if (!primaryPage) IconButton(onClick = ::back, modifier = Modifier.testTag("page-back").semantics { contentDescription = "Back" }) { Glyph("Back") }
                    if (primaryPage) { Box(Modifier.width(32.dp)) { OscarOrb(state, size = 28.dp, tag = "toolbar-orb") }; Spacer(Modifier.width(8.dp)) }
                    val pageTitle = when {
                        primaryPage -> "OSCAR"
                        voiceOpen -> "Voice"
                        destination == Destination.SETTINGS -> when (settingsPage) { "Settings" -> "Preferences"; "Platform" -> "Android permissions"; "Accessibility" -> "Appearance"; else -> settingsPage }
                        destination == Destination.AUTOMATIONS -> if (automationPage == "Create") "New responsibility" else "Worker"
                        destination == Destination.OSCAR -> "Today"
                        else -> destination.label
                    }
                    Text(pageTitle, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    if (primaryPage) {
                        IconButton(onClick = { navigate(Destination.DEVICES) }, modifier = Modifier.testTag("destination-DEVICES").semantics { contentDescription = "Devices" }) { Glyph("Devices") }
                        IconButton(onClick = { navigate(Destination.SETTINGS) }, modifier = Modifier.testTag("destination-SETTINGS").semantics { contentDescription = "Preferences" }) { Glyph("Preferences") }
                    }
                }
                Column(Modifier.weight(1f).fillMaxWidth().then(pageEntrance("$selected/$settingsPage/$conversationPage/$automationPage/$voiceOpen/${state.epoch}")).verticalScroll(pageScroll)
                    .padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Spacer(Modifier.height(4.dp))
                    when (destination) {
                        Destination.OSCAR -> if (voiceOpen) VoiceExperience(state, {
                            navigate(Destination.SETTINGS); settingsPage = "Privacy"
                        }) else if (conversationPage == "Today") TodayScreen(state, { conversationPage = "Conversation" }, { navigate(Destination.ACTIVITY) })
                        else PresenceScreen(state, draft, session::writeDraft, send, session::cancelRequest,
                            { navigate(Destination.ACTIVITY) }, { focus.clearFocus(); keyboard?.hide(); voiceOpen = true }, false, { conversationPage = "Today" }, { id -> session.inspect(id); navigate(Destination.ACTIVITY) })
                        Destination.AUTOMATIONS -> AutomationsScreen(state, automationPage, { automationPage = it }) { text -> session.writeDraft(text); navigate(Destination.OSCAR) }
                        Destination.ACTIVITY -> ActivityScreen(state, session::inspect, session::review)
                        Destination.DEVICES -> DevicesScreen(state, { pairing = true }, session::disconnect, session::revoke, session::rotateConnection) { target, kind, parameters ->
                            session.submitRemote("${if (kind == "file_write") "Write" else "Read"} workspace file ${parameters.getString("path")}", kind, target, parameters)
                            navigate(Destination.ACTIVITY)
                        }
                        Destination.SETTINGS -> SettingsScreen(settingsPage, { settingsParent = settingsPage; settingsPage = it }, session, state)
                    }
                    if (state.link != Link.CONNECTED && destination in setOf(Destination.OSCAR, Destination.ACTIVITY) && !voiceOpen && conversationPage == "Conversation") {
                        if (state.link == Link.CONNECTING) StatusLabel("Connecting to Core")
                        TextButton(onClick = { pairing = true }) { Text("Connect Core") }
                    }
                    if (primaryPage && destination == Destination.OSCAR && (draft.isNotEmpty() || state.interactions.isNotEmpty() || state.privateSuppressed)) {
                        TextButton(onClick = session::discard) { Text(if (state.remote) "Clear local private cache" else if (state.privateSuppressed) "Clear Core private context" else "Discard private interaction") }
                    }
                    Spacer(Modifier.height(12.dp))
                }
                SnackbarHost(notices) { notice -> Snackbar(dismissAction = { IconButton(onClick = notice::dismiss) { Text("×", modifier = Modifier.semantics { contentDescription = "Dismiss status" }) } }) { Text(notice.visuals.message, modifier = Modifier.testTag("message")) } }
                if (destination == Destination.OSCAR && !voiceOpen && conversationPage == "Conversation") {
                    Box(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp)) {
                        ConversationComposer(state, draft, session::writeDraft, send) { focus.clearFocus(); keyboard?.hide(); voiceOpen = true }
                    }
                }
            }
        }
        }
        }
        if (pairing) PairingDialog(state, session, { pairing = false })
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
@Composable private fun PairingDialog(state: MobileState, session: CoreSession, close: () -> Unit) {
    var origin by remember { mutableStateOf("") }; var node by remember { mutableStateOf("") }
    var id by remember { mutableStateOf("") }; var token by remember { mutableStateOf("") }
    var invitation by remember { mutableStateOf("") }; var retain by remember { mutableStateOf(false) }
    var legacy by remember { mutableStateOf(false) }; var error by remember { mutableStateOf<String?>(null) }
    AlertDialog(onDismissRequest = close, title = { Text("Connect this phone") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Use an invitation issued by your trusted Core for this device’s public identity.")
            Text("Connecting a different source clears the previous private draft and readback.")
            OscarField(origin, { origin = it.take(256) }, label = "Core address (HTTPS)", singleLine = true)
            if (!legacy) {
                TextButton(onClick = session::deviceIdentity) { Text("Show this device’s public identity") }
                state.enrollmentIdentity?.let { identity ->
                    androidx.compose.foundation.text.selection.SelectionContainer { Text(identity, style = MaterialTheme.typography.bodySmall) }
                    Text("Share this public identity with your trusted Core operator. It contains no private key.", style = MaterialTheme.typography.bodySmall)
                }
                OscarField(invitation, { invitation = it.take(24000) }, label = "Core invitation", minLines = 3, maxLines = 5)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = retain, onCheckedChange = { retain = it })
                    Text("Share and retain this connection’s conversation with my authorized OSCAR clients.", style = MaterialTheme.typography.bodySmall)
                }
                Text("Enrollment grants connection scopes only. Actions still require Core policy and exact owner approval.", style = MaterialTheme.typography.bodySmall)
            } else {
            OscarField(node, { node = it.take(80) }, label = "Device ID", singleLine = true)
            OscarField(id, { id = it.take(80) }, label = "Session ID", singleLine = true)
            OscarField(token, { token = it.take(200) }, label = "Connection token", singleLine = true,
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation(),
                keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = androidx.compose.ui.text.input.KeyboardType.Password))
            }
            if (BuildConfig.DEBUG) TextButton(onClick = { legacy = !legacy }) { Text(if (legacy) "Use trusted device invitation" else "Local reference connection") }
            error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        }
    }, dismissButton = { TextButton(onClick = close) { Text("Cancel") } }, confirmButton = {
        TextButton(enabled = origin.isNotBlank() && (if (legacy) listOf(node, id, token).none { it.isBlank() } else invitation.isNotBlank()), onClick = {
            try {
                CoreClient.validateEndpoint(origin)
                if (legacy) session.connect(JSONObject().put("url", origin).put("node_id", node).put("session_id", id).put("token", token))
                else session.enroll(origin, JSONObject(invitation), retain)
                close()
            } catch (_: Exception) { error = "Check the trusted HTTPS address and invitation format." }
        }) { Text("Connect") }
    })
}
@Composable fun OscarOrb(state: MobileState, composing: Boolean = false, size: Dp = 108.dp, reduced: Boolean = LocalReducedMotion.current, tag: String = "orb") {
    val voice by VoicePresentation.state.collectAsStateWithLifecycle()
    val adapter = remember(state.epoch) { MobileExpression(state.epoch) }
    val canonical = state.snapshot?.presence?.takeIf { state.link == Link.CONNECTED && !state.busy && !composing && voice.phase == VoicePhase.IDLE }
    val event = canonical ?: remember(state, composing, reduced, voice) { adapter.event(state, System.currentTimeMillis(), composing, reduced, voice.phase) }
    val source = io.dawnlight.oscar.expression.Contract.parse(event)?.source ?: adapter.source
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
        ExpressionPresence(event, source, size, reduced, Modifier.testTag(tag))
    }
}
