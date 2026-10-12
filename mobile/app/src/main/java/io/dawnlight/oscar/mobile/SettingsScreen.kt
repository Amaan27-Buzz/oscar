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
import androidx.compose.foundation.clickable
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
            Text("Preferences", style = MaterialTheme.typography.titleMedium)
            listOf("Persona", "Voice", "Privacy", "Notifications", "Platform", "Accessibility", "Diagnostics", "About").forEach { item ->
                ListItem(headlineContent = { Text(item) }, supportingContent = { Text(when(item) {
                    "Persona" -> "Expression preview"; "Voice" -> "Input and availability"; "Privacy" -> "Permissions and local grants"; "Notifications" -> "Alerts and reply access"
                    "Platform" -> "Android assistant entry"; "Accessibility" -> "Appearance and motion"; "Diagnostics" -> "Connection details"; else -> "Version and boundaries"
                }) }, leadingContent = { OscarIcon(when(item) { "Voice" -> "voice"; "Privacy", "Notifications" -> "privacy"; "Platform" -> "phone"; "Diagnostics" -> "desktop"; "Accessibility" -> "type"; "About" -> "info"; else -> "sliders" }) },
                    trailingContent = { OscarIcon("chevron") }, colors = ListItemDefaults.colors(containerColor = androidx.compose.ui.graphics.Color.Transparent),
                    modifier = Modifier.fillMaxWidth().clickable { navigate(item) }.heightIn(min = 72.dp))
            }
            Disclosure("Connection & Android settings") {
                TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) } catch (_: Exception) { session.message("Android accessibility settings are unavailable.") } }) { Text("Android accessibility settings") }
                TextButton(onClick = session::disconnect) { Text("Disconnect locally") }
                Text("Local disconnect removes this app’s credentials; remote revocation is separate.", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
@Composable fun VoiceSettings() {
    val (context, revision) = observedPermissions()
    Text("OSCAR Voice", style = MaterialTheme.typography.headlineMedium)
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
    Disclosure("Voice identity & platform details") {
        Text("Voice Identity · OSCAR original reference\nAccepted Core binding: Kokoro neural voice; platform fallbacks stay underneath one identity.")
        Text("Native AudioRecord, AudioTrack, audio focus and AEC adapters remain behind shared Voice contracts. Effect availability does not establish real-room AEC.")
    }
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
