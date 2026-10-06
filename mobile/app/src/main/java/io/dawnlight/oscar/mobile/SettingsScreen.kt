package io.dawnlight.oscar.mobile

import android.Manifest
import android.app.NotificationManager
import android.app.role.RoleManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioManager
import android.os.Build
import android.provider.Settings
import android.service.voice.VoiceInteractionService
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable fun SettingsScreen(page: String, navigate: (String) -> Unit, session: CoreSession, state: MobileState) {
    val context = LocalContext.current
    if (page != "Settings") TextButton(onClick = { navigate("Settings") }) { Text("Back to Settings") }
    when (page) {
        "Voice" -> VoiceSettings()
        "Privacy" -> PrivacySettings()
        "Platform" -> PlatformSettings()
        "Notifications" -> NotificationSettings(session, state)
        "About" -> {
            Text("OSCAR Mobile · ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.titleLarge)
            Text("Core owns identity, memory, policy, tasks, routing and evidence. This phone is its Android embodiment.")
            Text("Gate C PARTIAL · OWNER_DEVICE_ACCEPTANCE_NOT_RUN. Voice, biometric, assistant-role, notification replies, AEC and Bluetooth require consolidated acceptance.")
            Text("No conversation archive is stored by the app. Current interaction is transient and cleared when leaving the foreground.")
            TextButton(onClick = session::publicIdentity) { Text("Show public owner identity") }
        }
        else -> {
            Text("Your OSCAR", style = MaterialTheme.typography.titleLarge)
            listOf("Voice", "Privacy", "Notifications", "Platform", "About").forEach { item ->
                HorizontalDivider(); TextButton(onClick = { navigate(item) }, modifier = Modifier.fillMaxWidth()) { Text(item) }
            }
            Text("Persona and memory are managed by Core. Local switches cannot expand Core policy.")
            TextButton(onClick = { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }) { Text("Android accessibility settings") }
            TextButton(onClick = session::disconnect) { Text("Disconnect locally") }
            Text("Local disconnect deletes this app's credentials. Remote revocation remains a separate Core action.", style = MaterialTheme.typography.bodySmall)
        }
    }
}
@Composable private fun observedPermissions(): Pair<Context, Int> {
    val context = LocalContext.current
    var revision by remember { mutableIntStateOf(0) }
    val owner = LocalLifecycleOwner.current
    DisposableEffect(owner) {
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_RESUME) revision++ }
        owner.lifecycle.addObserver(observer)
        onDispose { owner.lifecycle.removeObserver(observer) }
    }
    return context to revision
}
@Composable private fun LocalGrant(label: String, key: String, explanation: String) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("permissions", Context.MODE_PRIVATE) }
    var checked by remember { mutableStateOf(prefs.getBoolean(key, false)) }
    val scope = rememberCoroutineScope()
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, modifier = Modifier.weight(1f).padding(top = 12.dp))
        Switch(checked, { next -> scope.launch {
            if (withContext(Dispatchers.IO) { prefs.edit().putBoolean(key, next).commit() }) {
                checked = next; NotificationBoundary.privacyChanged()
            }
        } }, modifier = Modifier.semantics { contentDescription = label })
    }
    Text(explanation, style = MaterialTheme.typography.bodySmall)
}
@Composable private fun AndroidGrant(label: String, permission: String) {
    val (context, resumed) = observedPermissions()
    var result by remember { mutableIntStateOf(0) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { result++ }
    val granted = remember(resumed, result) { context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED }
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("$label · ${if (granted) "Granted" else "Not granted"}", modifier = Modifier.weight(1f).padding(top = 12.dp))
        TextButton(onClick = { if (granted) context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, android.net.Uri.parse("package:${context.packageName}"))) else launcher.launch(permission) }) { Text(if (granted) "Manage" else "Request") }
    }
}
@Composable fun PrivacySettings() {
    val context = LocalContext.current
    Text("Permissions & privacy", style = MaterialTheme.typography.titleLarge)
    Text("Can perceive", style = MaterialTheme.typography.titleMedium)
    AndroidGrant("Microphone", Manifest.permission.RECORD_AUDIO)
    LocalGrant("Allow microphone perception", "microphone_perception", "Separate OSCAR grant. Capture also requires Android permission and a commissioned Voice Core binding.")
    LocalGrant("Selected notification context", "notification_context", "Requires explicit Android listener access and an allowlist. It grants no retention or reply authority.")
    val prefs = remember { context.getSharedPreferences("permissions", Context.MODE_PRIVATE) }
    var sources by remember { mutableStateOf(prefs.getString("notification_sources", "") ?: "") }
    var sourceError by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    OutlinedTextField(sources, { sources = it.take(1000) }, label = { Text("Allowed notification package IDs") }, supportingText = { Text("Comma-separated; only listed source apps may be perceived.") }, isError = sourceError, modifier = Modifier.fillMaxWidth())
    TextButton(onClick = {
        val names = sources.split(',').map { it.trim() }.filter { it.isNotEmpty() }
        sourceError = names.size > 32 || names.any { !it.matches(Regex("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) }
        if (!sourceError) scope.launch {
            sourceError = !withContext(Dispatchers.IO) { prefs.edit().putString("notification_sources", names.distinct().joinToString(",")).commit() }
            NotificationBoundary.privacyChanged()
        }
    }) { Text("Save sources") }
    Text("Location · not configured\nCamera · not configured\nSentry awareness · not commissioned\nVoice Match / Map · not enrolled", style = MaterialTheme.typography.bodyMedium)
    HorizontalDivider()
    Text("Can retain", style = MaterialTheme.typography.titleMedium)
    Text("Raw audio and notification retention are off. No local conversation archive. Core memory retention requires its own policy; perception never enables it.")
    HorizontalDivider()
    Text("Can act", style = MaterialTheme.typography.titleMedium)
    LocalGrant("Allow confirmed notification replies", "notification_reply", "Only exposed source-app reply actions; fresh Core permission, policy and signed confirmation are still required.")
    Text("Remote task control uses scoped Core pairing and one-decision confirmation. Broader communication, location and camera actions are unavailable.")
}
@Composable fun VoiceSettings() {
    val (context, revision) = observedPermissions()
    Text("OSCAR Voice", style = MaterialTheme.typography.titleLarge)
    Text("Voice Identity · OSCAR original reference\nAccepted Core binding: Kokoro neural voice; platform fallbacks stay underneath one identity.")
    Text("Android voice binding is not commissioned. Listening, playback, Voice Match and Voice Map are unavailable.")
    LocalGrant("Voice preference enabled", "voice_preference", "Saved preference only. It does not activate the microphone or imply Android inference is available.")
    AndroidGrant("Microphone", Manifest.permission.RECORD_AUDIO)
    LocalGrant("Interruption preferred", "barge_in_preference", "Applied when a real voice binding is commissioned. Real-room barge-in acceptance is deferred.")
    LocalGrant("Prefer local/private voice", "local_voice_preference", "Routing intent only. No automatic cloud escalation or model download from this phone.")
    if (Build.VERSION.SDK_INT >= 31) {
        AndroidGrant("Headset routing", Manifest.permission.BLUETOOTH_CONNECT)
        val route = remember(revision) {
            if (context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED)
                context.getSystemService(AudioManager::class.java).communicationDevice?.productName?.toString() ?: "No active communication route"
            else "Routing permission not granted"
        }
        Text("Output route · $route")
    }
    Text("Native AudioRecord, AudioTrack, audio focus and AEC adapters remain behind shared Voice contracts. Effect availability does not establish real-room AEC.")
}
@Composable fun PlatformSettings() {
    val (context, revision) = observedPermissions()
    val role = context.getSystemService(RoleManager::class.java)
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { }
    val selected = remember(revision) { VoiceInteractionService.isActiveService(context, ComponentName(context, AssistantService::class.java)) }
    Text("Android presence", style = MaterialTheme.typography.titleLarge)
    Text("Assistant · ${if (selected) "Selected" else "Not selected"}")
    TextButton(onClick = { if (role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) launcher.launch(role.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT)) }, enabled = role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) { Text("Choose assistant") }
    Text("Supported assistant invocation opens this OSCAR surface. Selection does not enable background listening or grant permissions. OEM behavior requires device testing.")
    Text("Overlay · not implemented\nWidgets · not implemented\nBackground microphone · user-started foreground service only, binding unavailable")
    Text("Android restricts background foreground-service starts and microphone access. No boot capture or Accessibility automation is used.")
}
@Composable private fun NotificationSettings(session: CoreSession, state: MobileState) {
    val (context, revision) = observedPermissions()
    val manager = context.getSystemService(NotificationManager::class.java)
    val access = remember(revision) { manager.isNotificationListenerAccessGranted(ComponentName(context, NotificationBoundary::class.java)) }
    Text("Notifications", style = MaterialTheme.typography.titleLarge)
    if (Build.VERSION.SDK_INT >= 33) AndroidGrant("OSCAR alerts", Manifest.permission.POST_NOTIFICATIONS)
    LocalGrant("Task alerts", "task_alerts", "Alerts for observed Core task completion, approval requests and failures. Background push/continuous polling is not implemented.")
    Text("Source notification access · ${if (access) "Granted" else "Not granted"}")
    TextButton(onClick = { context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }) { Text("Manage listener access") }
    Text("Perception and reply grants are managed separately in Privacy. Only real exposed reply actions are available.")
    var replies by remember { mutableStateOf(emptyList<org.json.JSONObject>()) }
    var draft by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<org.json.JSONObject?>(null) }
    TextButton(onClick = { try { replies = NotificationBoundary.exposed() } catch (_: Exception) { session.message("Notification access unavailable.") } }) { Text("Inspect exposed replies") }
    replies.forEach { source -> TextButton(onClick = { selected = source }) { Text(source.getString("title")) } }
    selected?.let { source ->
        OutlinedTextField(draft, { draft = it.take(500) }, label = { Text("Reply") }, modifier = Modifier.fillMaxWidth())
        TextButton(onClick = { session.reviewReply(source, draft); draft = ""; selected = null }, enabled = draft.isNotBlank() && state.link == Link.CONNECTED && !state.busy) { Text("Review with Core") }
    }
}
