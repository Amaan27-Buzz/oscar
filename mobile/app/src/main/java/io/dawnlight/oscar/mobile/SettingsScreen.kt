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
    when (page) {
        "Voice" -> VoiceSettings()
        "Persona" -> PersonaPreview()
        "Accessibility" -> AppearanceSettings()
        "Diagnostics" -> DiagnosticsSettings(state)
        "Privacy" -> PrivacySettings()
        "Awareness" -> AwarenessScreen { navigate("Privacy") }
        "Access" -> AccessScreen(state)
        "Memory" -> {
            FeatureRow("History & recall", "Managed by your OSCAR Core", "Conversation")
            StatusLabel("Memory tools are unavailable on this phone.")
            SupportingDetails("Drafts & memory") { Text("Unsent drafts use encrypted recovery. Discard clears the draft, not Core memory. History, forgetting and retention controls are managed by Core.", style = MaterialTheme.typography.bodySmall) }
        }
        "Platform" -> PlatformSettings()
        "Notifications" -> NotificationSettings(session, state)
        "About" -> {
            Text("OSCAR", style = MaterialTheme.typography.headlineLarge)
            Text("Dawnlight Labs · ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.bodyMedium)
            SupportingDetails("Privacy & device setup") {
                Text("Unsent drafts use encrypted recovery. Responses and decisions clear when leaving the foreground. Changing Core or discarding clears the draft.", style = MaterialTheme.typography.bodySmall)
                Text("Voice, biometric, assistant-role and notification integration need separate device acceptance.", style = MaterialTheme.typography.bodySmall)
                TextButton(onClick = session::publicIdentity) { Text("Show public owner identity") }
            }
        }
        else -> {
            val areas = listOf(
                Triple("Persona", "Preview expressions", "Preferences"),
                Triple("Voice", "Voice & input", "Voice"),
                Triple("Privacy", "Permissions & capture", "Preferences"),
                Triple("Awareness", "Off", "Activity"),
                Triple("Memory", "History tools unavailable", "Conversation"),
                Triple("Access", "Ask", "Automations"),
                Triple("Platform", "Android assistant & permissions", "Devices"),
                Triple("Notifications", "Alerts & confirmed replies", "Conversation"),
                Triple("Accessibility", "Appearance & motion", "Preferences"),
                Triple("Diagnostics", "Connection & app information", "Devices"),
                Triple("About", "OSCAR · Dawnlight Labs", "Preferences"))
            areas.forEachIndexed { index, (item, subtitle, icon) ->
                FeatureRow(if (item == "Platform") "Android permissions" else if (item == "Accessibility") "Appearance" else item,
                    subtitle, icon, listOf(Sage, Clay, Sage, Clay, Sage)[index % 5], action = { navigate(item) })
                HorizontalDivider()
            }
            TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) } catch (_: Exception) { session.message("Android accessibility settings are unavailable.") } }) { Text("Android accessibility settings") }
            SupportingDetails("Connection") {
                TextButton(onClick = session::disconnect) { Text("Disconnect locally") }
                Text("Removes this app's credentials. Remote revocation is a separate Core action.", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
@Composable fun VoiceSettings() {
    val (context, revision) = observedPermissions()
    StatusLabel("Voice setup incomplete")
    Text("Listening, playback and voice enrollment are unavailable.", style = MaterialTheme.typography.bodyMedium)
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
    SupportingDetails("Voice identity & audio") { Text("Voice identity is managed by OSCAR Core. Microphone permission alone does not enable listening. Audio processing and real-room playback need device commissioning.", style = MaterialTheme.typography.bodySmall) }
}
@Composable fun PlatformSettings() {
    val (context, revision) = observedPermissions()
    val role = context.getSystemService(RoleManager::class.java)
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { }
    var unavailable by remember { mutableStateOf(false) }
    val selected = remember(revision) { VoiceInteractionService.isActiveService(context, ComponentName(context, AssistantService::class.java)) }
    Text("Assistant · ${if (selected) "Selected" else "Not selected"}")
    TextButton(onClick = { try { if (role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) launcher.launch(role.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT)) } catch (_: Exception) { unavailable = true } }, enabled = role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) { Text("Choose assistant") }
    if (unavailable) Text("Android assistant selection is unavailable; no role change is confirmed.")
    Text("Assistant selection opens OSCAR. It does not enable background listening or grant other permissions.")
    SupportingDetails("Other Android features") {
        Text("Overlay · unavailable\nWidgets · unavailable", style = MaterialTheme.typography.bodySmall)
        Text("Background microphone access is unavailable until voice setup is complete. OSCAR does not start capture at boot or use Accessibility automation.", style = MaterialTheme.typography.bodySmall)
    }
}
