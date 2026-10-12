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
import androidx.compose.foundation.clickable
import androidx.compose.foundation.background
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

private val Paper = Color(0xFFF5F1E7)
private val Ink = Color(0xFF1A1B18)
@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
private val OscarSans = FontFamily(
    Font(R.font.source_sans_3, FontWeight.Normal, variationSettings = androidx.compose.ui.text.font.FontVariation.Settings(androidx.compose.ui.text.font.FontVariation.weight(400))),
    Font(R.font.source_sans_3, FontWeight.Medium, variationSettings = androidx.compose.ui.text.font.FontVariation.Settings(androidx.compose.ui.text.font.FontVariation.weight(500))),
    Font(R.font.source_sans_3, FontWeight.SemiBold, variationSettings = androidx.compose.ui.text.font.FontVariation.Settings(androidx.compose.ui.text.font.FontVariation.weight(600))),
)
@OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
private val OscarSerif = FontFamily(Font(R.font.source_serif_4, variationSettings = androidx.compose.ui.text.font.FontVariation.Settings(androidx.compose.ui.text.font.FontVariation.weight(400))))
private val OscarType = Typography(
    headlineLarge = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 26.sp, lineHeight = 32.sp),
    headlineMedium = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 24.sp, lineHeight = 30.sp),
    headlineSmall = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleLarge = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, lineHeight = 28.sp),
    titleMedium = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 18.sp, lineHeight = 24.sp),
    titleSmall = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 15.sp, lineHeight = 20.sp),
    bodyLarge = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontSize = 18.sp, lineHeight = 28.sp),
    bodyMedium = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontSize = 16.sp, lineHeight = 24.sp),
    bodySmall = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontSize = 14.sp, lineHeight = 20.sp),
    labelLarge = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 22.sp),
    labelMedium = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    labelSmall = androidx.compose.ui.text.TextStyle(fontFamily = OscarSans, fontSize = 12.sp, lineHeight = 16.sp),
)
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
    MaterialTheme(typography = OscarType, colorScheme = if (dark) darkColorScheme(primary = Color(0xFFF2F5EE), onPrimary = Ink,
        secondary = Color(0xFF91C4FF), secondaryContainer = Color(0xFF303E35), onSecondaryContainer = Color(0xFFF2F5EE),
        tertiary = Color(0xFFFFCF5A), tertiaryContainer = Color(0xFF453C22), onTertiaryContainer = Color(0xFFFFEAB0), background = Color(0xFF1D2622),
        surface = Color(0xFF1D2622), surfaceContainer = Color(0xFF27312B), surfaceContainerHigh = Color(0xFF303E35),
        surfaceContainerHighest = Color(0xFF30342D), surfaceContainerLow = Color(0xFF20231E), surfaceContainerLowest = Color(0xFF151713),
        surfaceTint = Color.Transparent, onBackground = Color(0xFFF2F5EE), onSurface = Color(0xFFF2F5EE), onSurfaceVariant = Color(0xFFB6C3B9),
        outline = Color(0xFF999D8D), outlineVariant = Color(0xFF3E4C42), error = Color(0xFFFFB4A9)) else lightColorScheme(primary = Ink, onPrimary = Color.White,
        secondary = Color(0xFF1969BC), secondaryContainer = Color(0xFFE8EDE6), onSecondaryContainer = Ink,
        tertiary = Color(0xFFFFC83D), tertiaryContainer = Color(0xFFFFF0B7), onTertiaryContainer = Ink, background = Paper,
        surface = Paper, surfaceContainer = Color(0xFFFFFDF8), surfaceContainerHigh = Color(0xFFEAE5DA),
        surfaceContainerHighest = Color(0xFFE0E7DE), surfaceContainerLow = Paper, surfaceContainerLowest = Color.White,
        surfaceTint = Color.Transparent, onBackground = Ink, onSurface = Ink, onSurfaceVariant = Color(0xFF58635B),
        outline = Color(0xFF78857A), outlineVariant = Color(0xFFD7DDD6), error = Color(0xFFB6322B)),
        shapes = Shapes(small = androidx.compose.foundation.shape.RoundedCornerShape(6.dp), medium = androidx.compose.foundation.shape.RoundedCornerShape(12.dp), large = androidx.compose.foundation.shape.RoundedCornerShape(16.dp)), content = content)
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
    val focus = LocalFocusManager.current
    val keyboard = LocalSoftwareKeyboardController.current
    val drawer = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    fun navigate(item: Destination) {
        VoicePresentation.cancel(session.getApplication()); voiceOpen = false
        focus.clearFocus(); keyboard?.hide(); selected = item.name; settingsPage = "Settings"
        scope.launch { drawer.close() }
    }
    BackHandler(drawer.isOpen || drawer.targetValue == DrawerValue.Open || voiceOpen || destination != Destination.OSCAR || settingsPage != "Settings") {
        if (drawer.isOpen || drawer.targetValue == DrawerValue.Open) scope.launch { drawer.close() }
        else if (voiceOpen) { VoicePresentation.cancel(session.getApplication()); voiceOpen = false } else if (settingsPage != "Settings") settingsPage = "Settings" else selected = Destination.OSCAR.name
    }
    OscarTheme {
        ModalNavigationDrawer(drawerState = drawer, gesturesEnabled = drawer.isOpen, drawerContent = {
            ModalDrawerSheet(Modifier.widthIn(max = 320.dp)) {
                Text("Your OSCAR", style = MaterialTheme.typography.headlineSmall, modifier = Modifier.padding(24.dp))
                Destination.entries.forEach { item ->
                    NavigationDrawerItem(label = { Text(item.label) }, selected = item == destination,
                        onClick = { navigate(item) }, modifier = Modifier.padding(horizontal = 12.dp).testTag("destination-${item.name}"))
                }
                Spacer(Modifier.weight(1f))
            }
        }) {
        Scaffold(modifier = Modifier.imePadding(), containerColor = MaterialTheme.colorScheme.background,
            topBar = {
                Row(Modifier.fillMaxWidth().statusBarsPadding().padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                    if (destination != Destination.OSCAR) IconButton(onClick = { if (settingsPage != "Settings") settingsPage = "Settings" else navigate(Destination.OSCAR) }, modifier = Modifier.semantics { contentDescription = if (settingsPage != "Settings") "Back to Settings" else "Back to OSCAR" }) { OscarIcon("back") }
                    Column(Modifier.weight(1f).padding(start = 8.dp)) {
                        Text(if (destination == Destination.OSCAR) "OSCAR" else if (destination == Destination.SETTINGS && settingsPage != "Settings") settingsPage else destination.label,
                            style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                        if (destination == Destination.OSCAR) Text(when(state.link) { Link.CONNECTED -> "Connected"; Link.CONNECTING -> "Connecting"; else -> "Not connected" }, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    if (destination == Destination.OSCAR) IconButton(onClick = { navigate(Destination.ACTIVITY) }, modifier = Modifier.testTag("activityShortcut").semantics { contentDescription = "Activity" }) { OscarIcon("activity") }
                    IconButton(onClick = { focus.clearFocus(); keyboard?.hide(); scope.launch { drawer.open() } }, modifier = Modifier.testTag("navigation").semantics { contentDescription = "Open navigation" }) { OscarIcon("menu") }
                }
            }, bottomBar = {
                if (destination == Destination.OSCAR) {
                    Surface(Modifier.fillMaxWidth(), color = MaterialTheme.colorScheme.surfaceContainer) {
                        Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                        Column(Modifier.widthIn(max = 720.dp).fillMaxWidth().navigationBarsPadding().padding(horizontal = if (widthDp < 360.dp) 16.dp else 24.dp, vertical = 12.dp)) {
                            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                IconButton(onClick = { focus.clearFocus(); keyboard?.hide(); if (voiceOpen) VoicePresentation.cancel(session.getApplication()); voiceOpen = !voiceOpen }, modifier = Modifier.size(64.dp).testTag("orb").semantics { contentDescription = if (voiceOpen) "Close voice interaction" else "Open voice interaction" }) {
                                    Box(Modifier.size(56.dp)) {
                                        OscarOrb(state, composing = draft.isNotBlank(), size = 56.dp)
                                        Box(Modifier.align(Alignment.BottomEnd).size(16.dp).background(MaterialTheme.colorScheme.surfaceContainer, androidx.compose.foundation.shape.CircleShape)) { OscarIcon("voice") }
                                    }
                                }
                                Column(Modifier.weight(1f)) { InteractionComposer(state, draft, session::writeDraft, { focus.clearFocus(); keyboard?.hide(); session.send(draft) }, session::cancelRequest,
                                    { focus.clearFocus(); keyboard?.hide(); voiceOpen = true }) }
                            }
                        }
                        }
                    }
                }
            }) { insets ->
            Box(Modifier.fillMaxSize().padding(insets), contentAlignment = Alignment.TopCenter) {
            Column(Modifier.widthIn(max = 720.dp).fillMaxWidth().padding(horizontal = if (widthDp < 360.dp) 16.dp else 24.dp)
                .verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Spacer(Modifier.height(16.dp))
                if (state.link != Link.CONNECTED && destination == Destination.OSCAR && !voiceOpen) {
                    Spacer(Modifier.height(32.dp))
                    OscarIcon("desktop")
                    Text(if (state.link == Link.CONNECTING) "Connecting to OSCAR" else "Connect OSCAR", style = MaterialTheme.typography.titleLarge)
                    Text("Requests are paused.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { pairing = true }, shape = MaterialTheme.shapes.small) { Text("Connect Core") }
                        TextButton(onClick = session::refreshNow, enabled = !state.busy) { Text("Refresh") }
                    }
                }
                when (destination) {
                    Destination.OSCAR -> if (voiceOpen) VoiceExperience({ voiceOpen = false }, { VoicePresentation.cancel(session.getApplication()); voiceOpen = false; selected = Destination.SETTINGS.name; settingsPage = "Privacy" }) else PresenceScreen(state, draft, session::writeDraft, { focus.clearFocus(); keyboard?.hide(); session.send(draft) }, session::cancelRequest,
                        { navigate(Destination.ACTIVITY) }, { focus.clearFocus(); keyboard?.hide(); voiceOpen = true }, showComposer = false, inspect = session::inspect)
                    Destination.ACTIVITY -> ActivityScreen(state, session::inspect, session::review)
                    Destination.DEVICES -> DevicesScreen(state, { pairing = true }, session::disconnect)
                    Destination.SETTINGS -> SettingsScreen(settingsPage, { settingsPage = it }, session, state)
                }
                state.message?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis, modifier = Modifier.testTag("message").semantics { liveRegion = LiveRegionMode.Polite })
                    if (it.length > 120) Disclosure("Message details") { androidx.compose.foundation.text.selection.SelectionContainer { Text(it) } }
                }
                if (draft.isNotEmpty() || state.interactions.isNotEmpty() || state.privateSuppressed) {
                    TextButton(onClick = session::discard) { Text(if (state.privateSuppressed) "Clear Core private context" else "Discard private interaction") }
                }
                Spacer(Modifier.height(16.dp))
            }
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
