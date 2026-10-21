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
import androidx.compose.ui.graphics.Color
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
        "Awareness" -> AwarenessScreen(session, state) { navigate("Privacy") }
        "Access" -> AccessScreen(session, state)
        "Connections" -> ConnectionsScreen(session, state)
        "Memory" -> {
            IllustratedIntro("Memory", artwork = R.drawable.illustration_reading, height = 112.dp)
            PreferenceGroup("History & recall") {
                FeatureRow("OSCAR memory", "Managed by your Core", "Book", Lilac)
                HorizontalDivider()
                PreferenceValue("History tools", "Unavailable on this phone")
            }
            PreferenceGroup("On this phone") {
                PreferenceValue("Unsent drafts", "Encrypted recovery")
                HorizontalDivider()
                PreferenceValue("Responses", "Cleared on leaving the app")
            }
            SupportingDetails("Drafts & memory") { Text("Unsent drafts use encrypted recovery. Discard clears the draft, not Core memory. History, forgetting and retention controls are managed by Core.", style = MaterialTheme.typography.bodySmall) }
        }
        "Platform" -> PlatformSettings()
        "Notifications" -> NotificationSettings(session, state)
        "About" -> {
            Row(Modifier.fillMaxWidth().padding(vertical = 20.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Box(Modifier.width(88.dp)) { OscarOrb(state, size = 72.dp) }
                Column { Text("OSCAR", style = MaterialTheme.typography.headlineLarge); Text("Dawnlight Labs", style = MaterialTheme.typography.bodyMedium) }
            }
            PreferenceGroup("Application") { PreferenceValue("Version", BuildConfig.VERSION_NAME); HorizontalDivider(); PreferenceValue("Surface", "OSCAR Mobile") }
            SupportingDetails("Privacy & device setup") {
                Text("Unsent drafts use encrypted recovery. Responses and decisions clear when leaving the foreground. Changing Core or discarding clears the draft.", style = MaterialTheme.typography.bodySmall)
                Text("Voice, biometric, assistant-role and notification integration need separate device acceptance.", style = MaterialTheme.typography.bodySmall)
                TextButton(onClick = session::publicIdentity) { Text("Show public owner identity") }
            }
        }
        else -> {
            IllustratedIntro("Make OSCAR", "yours.", artwork = R.drawable.illustration_preferences, height = 144.dp)
            val groups = listOf(
                "Personal" to listOf(Triple("Persona", "Expression preview", "Persona"), Triple("Voice", "Audio & input", "Voice"), Triple("Accessibility", "Theme & motion", "Appearance")),
                "Your context" to listOf(Triple("Privacy", "Permissions & capture", "Privacy"), Triple("Awareness", if (state.snapshot?.management == null) "Check connection" else "Sources & permissions", "Awareness"), Triple("Memory", "History & drafts", "Memory"), Triple("Notifications", "Alerts & replies", "Notifications")),
                "Control" to listOf(Triple("Access", state.snapshot?.management?.mode?.replaceFirstChar { it.uppercase() } ?: "Check connection", "Conversation"), Triple("Connections", "Accounts & tools", "Devices"), Triple("Platform", "Assistant & system access", "Android")),
                "Application" to listOf(Triple("Diagnostics", "Connection & device", "Activity"), Triple("About", "OSCAR · Dawnlight Labs", "About")))
            groups.forEach { (title, areas) ->
                PreferenceGroup(title, flat = true) {
                    areas.forEachIndexed { index, (item, subtitle, icon) ->
                        if (index > 0) HorizontalDivider()
                        FeatureRow(if (item == "Platform") "Android permissions" else if (item == "Accessibility") "Appearance" else item,
                            subtitle, icon, color = when (item) {
                                "Voice", "Accessibility" -> Clay
                                "Privacy", "Access" -> Color(0xFFE7AD3B)
                                "Memory", "Notifications" -> Lilac
                                else -> Sage
                            }, action = { navigate(item) })
                    }
                }
            }
            TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) } catch (_: Exception) { session.message("Android accessibility settings are unavailable.") } }) { Text("Android accessibility settings") }
            SupportingDetails("Connection") {
                state.snapshot?.setup?.forEach { (section, status) -> PreferenceValue(section.replaceFirstChar { it.uppercase() }, status) }
                TextButton(onClick = session::disconnect) { Text("Disconnect locally") }
                Text("Removes this app's credentials. Remote revocation is a separate Core action.", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
@Composable fun VoiceSettings() {
    val (context, revision) = observedPermissions()
    IllustratedIntro("Voice & input", artwork = R.drawable.illustration_preferences, height = 112.dp)
    StatusLabel("Voice setup incomplete")
    StatusLabel("Listening, playback and enrollment unavailable")
    PreferenceGroup("Audio permissions") {
        AndroidGrant("Microphone", Manifest.permission.RECORD_AUDIO)
        if (Build.VERSION.SDK_INT >= 31) {
            HorizontalDivider()
            AndroidGrant("Headset routing", Manifest.permission.BLUETOOTH_CONNECT)
            val route = remember(revision) {
                if (context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED)
                    context.getSystemService(AudioManager::class.java).communicationDevice?.productName?.toString() ?: "No active communication route"
                else "Routing permission not granted"
            }
            HorizontalDivider()
            PreferenceValue("Output route", route)
        }
    }
    SupportingDetails("Voice identity & audio") { Text("Voice identity is managed by OSCAR Core. Microphone permission alone does not enable listening. Audio processing and real-room playback need device commissioning.", style = MaterialTheme.typography.bodySmall) }
}
@Composable fun PlatformSettings() {
    val (context, revision) = observedPermissions()
    val role = context.getSystemService(RoleManager::class.java)
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { }
    var unavailable by remember { mutableStateOf(false) }
    val selected = remember(revision) { VoiceInteractionService.isActiveService(context, ComponentName(context, AssistantService::class.java)) }
    PreferenceGroup("Android assistant") {
        FeatureRow("OSCAR as your assistant", if (selected) "Selected" else "Not selected", "Android")
        OscarButton(onClick = { try { if (role.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) launcher.launch(role.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT)) } catch (_: Exception) { unavailable = true } }, enabled = role.isRoleAvailable(RoleManager.ROLE_ASSISTANT), modifier = Modifier.fillMaxWidth()) { Text("Choose assistant") }
        if (unavailable) Text("Android assistant selection is unavailable; no role change is confirmed.", color = MaterialTheme.colorScheme.error)
        Text("Opens OSCAR when invoked. Listening and permissions stay separate.", style = MaterialTheme.typography.bodySmall)
    }
    SupportingDetails("Other Android features") {
        Text(if (remember(revision) { Settings.canDrawOverlays(context) }) "Overlay permission granted" else "Overlay permission not granted", style = MaterialTheme.typography.bodySmall)
        TextButton(onClick = { try { launcher.launch(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, android.net.Uri.parse("package:${context.packageName}"))) } catch (_: Exception) { unavailable = true } }) { Text("Allow display over other apps") }
        if (Build.VERSION.SDK_INT >= 33) AndroidGrant("Companion notification", Manifest.permission.POST_NOTIFICATIONS)
        TextButton(enabled = CompanionOverlay.permitted(context), onClick = { try { CompanionOverlay.show(context) } catch (_: Exception) { unavailable = true } }) { Text("Show Companion Orb") }
        TextButton(onClick = { CompanionOverlay.hide(context) }) { Text("Hide Companion") }
        TextButton(onClick = { CompanionOverlay.hide(context, disable = true) }) { Text("Disable Companion overlay") }
        Text("Requires separately authorized Core presence. Stops on lock, disconnection or permission loss. Does not listen or display conversations. Widgets remain unavailable.", style = MaterialTheme.typography.bodySmall)
        Text("Background microphone access is unavailable until voice setup is complete. OSCAR does not start capture at boot.", style = MaterialTheme.typography.bodySmall)
    }
    NativeCapabilitySettings()
}
