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
    if (page != "Settings") TextButton(onClick = { navigate("Settings") }) { Glyph("Back"); Text("Back to Preferences") }
    when (page) {
        "Voice" -> VoiceSettings()
        "Persona" -> PersonaPreview()
        "Accessibility" -> AppearanceSettings()
        "Diagnostics" -> DiagnosticsSettings(state)
        "Privacy" -> PrivacySettings()
        "Awareness" -> AwarenessScreen { navigate("Privacy") }
        "Access" -> AccessScreen(state)
        "Memory" -> {
            EditorialHeading("Memory", "One continuing relationship.")
            FeatureRow("History & recall", "Managed by your OSCAR Core", "Conversation")
            Text("Memory inspection, forgetting and retention policy are not exposed by this Mobile API. No recalled history is fabricated or stored in a separate phone archive.")
            Text("Your unsent draft is encrypted for recovery. Discard private interaction clears it; it does not delete Core memory.", style = MaterialTheme.typography.bodySmall)
        }
        "Platform" -> PlatformSettings()
        "Notifications" -> NotificationSettings(session, state)
        "About" -> {
            Text("OSCAR Mobile · ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.titleLarge)
            Text("Core owns identity, memory, policy, tasks, routing and evidence. This phone is its Android embodiment.")
            Text("Gate C PARTIAL · OWNER_DEVICE_ACCEPTANCE_NOT_RUN. Voice, biometric, assistant-role, notification replies, AEC and Bluetooth require consolidated acceptance.")
            Text("No conversation archive is stored by the app. Only your unsent draft is encrypted locally for recovery; responses and decisions are cleared when leaving the foreground. A different source or discard clears the draft.")
            TextButton(onClick = session::publicIdentity) { Text("Show public owner identity") }
        }
        else -> {
            Row(Modifier.fillMaxWidth(), verticalAlignment = androidx.compose.ui.Alignment.Bottom) {
                Column(Modifier.weight(1f)) { EditorialHeading("Make OSCAR", "yours.") }
                Illustration(R.drawable.illustration_preferences, Modifier.width(136.dp), height = 160.dp)
            }
            val areas = listOf(
                Triple("Persona", "Expression preview · Core settings unavailable", "Preferences"),
                Triple("Voice", "Voice & input", "Voice"),
                Triple("Privacy", "Permissions & capture", "Preferences"),
                Triple("Awareness", "Manual · Sentry unavailable", "Activity"),
                Triple("Memory", "History & forgetting", "Conversation"),
                Triple("Access", "Ask · delegation unavailable", "Automations"),
                Triple("Platform", "Android assistant & permissions", "Devices"),
                Triple("Notifications", "Alerts & confirmed replies", "Conversation"),
                Triple("Accessibility", "Appearance & motion", "Preferences"),
                Triple("Diagnostics", "Devices & technical details", "Devices"),
                Triple("About", "OSCAR · Dawnlight Labs", "Preferences"))
            areas.forEachIndexed { index, (item, subtitle, icon) ->
                FeatureRow(if (item == "Platform") "Android permissions" else if (item == "Accessibility") "Appearance" else item,
                    subtitle, icon, listOf(Sage, Clay, Sage, Clay, Sage)[index % 5], action = { navigate(item) })
                HorizontalDivider()
            }
            Text("Persona and memory are managed by Core. Local switches cannot expand Core policy.")
            TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) } catch (_: Exception) { session.message("Android accessibility settings are unavailable.") } }) { Text("Android accessibility settings") }
            TextButton(onClick = session::disconnect) { Text("Disconnect locally") }
            Text("Local disconnect deletes this app's credentials. Remote revocation remains a separate Core action.", style = MaterialTheme.typography.bodySmall)
        }
    }
}
@Composable fun VoiceSettings() {
    val (context, revision) = observedPermissions()
    Text("OSCAR Voice", style = MaterialTheme.typography.titleLarge)
    Text("Voice Identity · OSCAR original reference\nAccepted Core binding: Kokoro neural voice; platform fallbacks stay underneath one identity.")
    Text("Android voice binding is not commissioned. Listening, playback, Voice Match and Voice Map are unavailable.")
    AndroidGrant("Microphone", Manifest.permission.RECORD_AUDIO)
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
    var unavailable by remember { mutableStateOf(false) }
    val selected = remember(revision) { VoiceInteractionService.isActiveService(context, ComponentName(context, AssistantService::class.java)) }
    Text("Android presence", style = MaterialTheme.typography.titleLarge)
    Text("Assistant · ${if (selected) "Selected" else "Not selected"}")
    TextButton(onClick = { try { if (role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) launcher.launch(role.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT)) } catch (_: Exception) { unavailable = true } }, enabled = role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) { Text("Choose assistant") }
    if (unavailable) Text("Android assistant selection is unavailable; no role change is confirmed.")
    Text("Supported assistant invocation opens this OSCAR surface. Selection does not enable background listening or grant permissions. OEM behavior requires device testing.")
    Text("Overlay · unavailable (Slice 16 runtime)\nWidgets · unavailable (Slice 16 runtime)\nBackground microphone · user-started foreground service only, binding unavailable")
    Text("Android restricts background foreground-service starts and microphone access. No boot capture or Accessibility automation is used.")
}
