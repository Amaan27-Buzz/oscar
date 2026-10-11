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
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import androidx.lifecycle.repeatOnLifecycle
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion

@Composable internal fun observedPermissions(): Pair<Context, Int> {
    val context = LocalContext.current
    var revision by remember { mutableIntStateOf(0) }
    val owner = LocalLifecycleOwner.current
    DisposableEffect(owner) {
        val prefs = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
        val changes = android.content.SharedPreferences.OnSharedPreferenceChangeListener { _, _ -> revision++ }
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_RESUME) {
            revision++; NotificationBoundary.privacyChanged()
        } }
        owner.lifecycle.addObserver(observer)
        prefs.registerOnSharedPreferenceChangeListener(changes)
        onDispose { owner.lifecycle.removeObserver(observer); prefs.unregisterOnSharedPreferenceChangeListener(changes) }
    }
    return context to revision
}
@Composable internal fun LocalGrant(label: String, key: String, explanation: String) {
    val (context, revision) = observedPermissions()
    val prefs = remember { context.getSharedPreferences("permissions", Context.MODE_PRIVATE) }
    var checked by remember { mutableStateOf(prefs.getBoolean(key, false)) }
    var failed by remember { mutableStateOf(false) }
    var saving by remember { mutableStateOf(false) }
    LaunchedEffect(revision) { checked = prefs.getBoolean(key, false) }
    val scope = rememberCoroutineScope()
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, modifier = Modifier.weight(1f).padding(top = 12.dp))
        Switch(checked, { next -> saving = true; scope.launch {
            if (withContext(Dispatchers.IO) { prefs.edit().putBoolean(key, next).commit() }) {
                checked = next; failed = false
            } else failed = true
            NotificationBoundary.privacyChanged()
            if (key == "microphone_perception" && !next) VoicePresentation.cancel(context)
            saving = false
        } }, enabled = !saving, modifier = Modifier.semantics { contentDescription = label })
    }
    Text(explanation, style = MaterialTheme.typography.bodySmall)
    if (failed) Text("Persistence is unverified. Inspect current grants before continuing.", color = MaterialTheme.colorScheme.error)
}
@Composable internal fun AndroidGrant(label: String, permission: String) {
    val (context, resumed) = observedPermissions()
    var result by remember { mutableIntStateOf(0) }
    var unavailable by remember { mutableStateOf(false) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { result++ }
    val granted = remember(resumed, result) { context.checkSelfPermission(permission) == PackageManager.PERMISSION_GRANTED }
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("$label · ${if (granted) "Granted" else "Not granted"}", modifier = Modifier.weight(1f).padding(top = 12.dp))
        TextButton(onClick = { try {
            if (granted) context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, android.net.Uri.parse("package:${context.packageName}"))) else launcher.launch(permission)
            unavailable = false
        } catch (_: Exception) { unavailable = true } }) { Text(if (granted) "Manage" else "Request") }
    }
    if (unavailable) Text("Android permission controls are unavailable. No new grant is confirmed.", color = MaterialTheme.colorScheme.error)
}
@Composable fun PrivacySettings() {
    val (context, revision) = observedPermissions()
    Text("Permissions & privacy", style = MaterialTheme.typography.titleLarge)
    Text("Can perceive", style = MaterialTheme.typography.titleMedium)
    AndroidGrant("Microphone", Manifest.permission.RECORD_AUDIO)
    LocalGrant("Allow microphone perception", "microphone_perception", "Separate OSCAR grant. Capture also requires Android permission and a commissioned Voice Core binding.")
    LocalGrant("Selected notification context", "notification_context", "Requires explicit Android listener access and an allowlist. It grants no retention or reply authority.")
    val listener = context.getSystemService(NotificationManager::class.java).isNotificationListenerAccessGranted(ComponentName(context, NotificationBoundary::class.java))
    Text("Android listener access · ${if (listener) "Granted" else "Not granted"}")
    var platformUnavailable by remember { mutableStateOf(false) }
    TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)); platformUnavailable = false }
        catch (_: Exception) { platformUnavailable = true } }) { Text("Manage listener access") }
    if (platformUnavailable) Text("Android listener settings are unavailable. Access is unchanged.", color = MaterialTheme.colorScheme.error)
    val prefs = remember { context.getSharedPreferences("permissions", Context.MODE_PRIVATE) }
    var sources by remember { mutableStateOf(prefs.getString("notification_sources", "") ?: "") }
    var sourceError by remember { mutableStateOf(false) }
    var sourceSaveFailed by remember { mutableStateOf(false) }
    var saved by remember { mutableStateOf(false) }
    val storedSources = remember(revision) { prefs.getString("notification_sources", "") ?: "" }
    LaunchedEffect(storedSources) { sources = storedSources }
    val scope = rememberCoroutineScope()
    OutlinedTextField(sources, { sources = it.take(1000); saved = false }, label = { Text("Allowed notification package IDs") }, supportingText = { Text("Comma-separated; every unlisted app is excluded. Empty means no sources.") }, isError = sourceError, modifier = Modifier.fillMaxWidth().testTag("notificationSources"))
    TextButton(onClick = {
        val names = sources.split(',').map { it.trim() }.filter { it.isNotEmpty() }
        sourceError = names.size > 32 || names.any { !it.matches(Regex("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) }
        sourceSaveFailed = false
        if (!sourceError) scope.launch {
            sourceSaveFailed = !withContext(Dispatchers.IO) { prefs.edit().putString("notification_sources", names.distinct().joinToString(",")).commit() }
            NotificationBoundary.privacyChanged()
            saved = !sourceSaveFailed
        }
    }) { Text("Save sources") }
    if (sourceError) Text("Use up to 32 package IDs, such as example.app. Nothing was enabled.", color = MaterialTheme.colorScheme.error)
    if (sourceSaveFailed) Text("Source persistence is unverified. Inspect current exclusions before continuing.", color = MaterialTheme.colorScheme.error)
    if (saved) Text("Source exclusions saved.", modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
    Text("Notification content stays hidden in this surface. Only the source app and available reply action are shown; no notification archive is written.", style = MaterialTheme.typography.bodySmall)
    TextButton(onClick = { NotificationBoundary.privacyChanged() }) { Text("Clear transient notification context") }
    Text("Location · not configured\nCamera · not configured\nSentry awareness · not commissioned\nVoice Match / Map · not enrolled", style = MaterialTheme.typography.bodyMedium)
    HorizontalDivider()
    Text("Can retain", style = MaterialTheme.typography.titleMedium)
    Text("Raw audio and notification retention are off. Only an unsent text draft is encrypted for recovery. Discard clears that draft; Core memory retention and source/person exclusions require separate Core policy. Perception never enables retention.")
    HorizontalDivider()
    Text("Can act", style = MaterialTheme.typography.titleMedium)
    LocalGrant("Allow confirmed notification replies", "notification_reply", "Only exposed source-app reply actions; fresh Core permission, policy and signed confirmation are still required.")
    Text("Remote task control uses scoped Core pairing and one-decision confirmation. Broader communication, location and camera actions are unavailable.")
    Text("Overlay · unavailable in this slice\nAssistant role · managed separately in Android presence\nLocal/cloud routing preference · unavailable until Core exposes a supported setting")
    var revokeFailed by remember { mutableStateOf(false) }
    TextButton(onClick = { scope.launch {
        val applied = withContext(Dispatchers.IO) { prefs.edit().putBoolean("microphone_perception", false)
            .putBoolean("notification_context", false).putBoolean("notification_reply", false).putString("notification_sources", "").commit() }
        revokeFailed = !applied
        NotificationBoundary.privacyChanged(); VoicePresentation.cancel(context)
    } }) { Text("Revoke local perception and reply grants") }
    if (revokeFailed) Text("Revocation persistence is unverified. Inspect current permissions before continuing.", color = MaterialTheme.colorScheme.error)
    Text("Android permissions and remote Core grants are independent. Manage or revoke them at their own source.", style = MaterialTheme.typography.bodySmall)
}
@Composable internal fun NotificationSettings(session: CoreSession, state: MobileState) {
    val (context, revision) = observedPermissions()
    val manager = context.getSystemService(NotificationManager::class.java)
    val access = remember(revision) { manager.isNotificationListenerAccessGranted(ComponentName(context, NotificationBoundary::class.java)) }
    Text("Notifications", style = MaterialTheme.typography.titleLarge)
    if (Build.VERSION.SDK_INT >= 33) AndroidGrant("OSCAR alerts", Manifest.permission.POST_NOTIFICATIONS)
    LocalGrant("Task alerts", "task_alerts", "Alerts for observed Core task completion, approval requests and failures. Background push/continuous polling is not implemented.")
    Text("Source notification access · ${if (access) "Granted" else "Not granted"}")
    TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }
        catch (_: Exception) { session.message("Android listener settings are unavailable. Access is unchanged.") } }) { Text("Manage listener access") }
    Text("Perception and reply grants are managed separately in Privacy. Only real exposed reply actions are available.")
    var replies by remember { mutableStateOf(emptyList<org.json.JSONObject>()) }
    var draft by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<org.json.JSONObject?>(null) }
    val owner = LocalLifecycleOwner.current
    var boundaryRevision by remember { mutableLongStateOf(NotificationBoundary.revision()) }
    LaunchedEffect(owner) { owner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
        while (isActive) { boundaryRevision = NotificationBoundary.revision(); delay(1000) }
    } }
    LaunchedEffect(state.epoch, revision, boundaryRevision) {
        replies = emptyList(); selected = null; draft = ""
        if (state.approval?.operation == "reply") session.dismissApproval()
    }
    TextButton(onClick = { try { replies = NotificationBoundary.exposed() } catch (_: Exception) { session.message("Notification access unavailable.") } }) { Text("Inspect exposed replies") }
    replies.forEach { source -> TextButton(onClick = { selected = source }) { Text(source.getString("title")) } }
    selected?.let { source ->
        OutlinedTextField(draft, { draft = it.take(500) }, label = { Text("Reply") }, modifier = Modifier.fillMaxWidth())
        val replyGrant = context.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("notification_reply", false)
        TextButton(onClick = { if (NotificationBoundary.current(source)) session.reviewReply(source, draft); draft = ""; selected = null }, enabled = replyGrant && draft.isNotBlank() && state.link == Link.CONNECTED && !state.busy && !state.privateSuppressed && NotificationBoundary.current(source)) { Text("Review with Core") }
        if (!replyGrant) Text("Confirmed reply grant is off. Perception alone cannot send.")
    }
}
