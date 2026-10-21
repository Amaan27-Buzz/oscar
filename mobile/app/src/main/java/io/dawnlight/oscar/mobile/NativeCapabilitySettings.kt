package io.dawnlight.oscar.mobile

import android.content.Intent
import android.provider.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxWidth
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable internal fun NativeCapabilitySettings() {
    val (context, revision) = observedPermissions()
    val access = remember(revision) { accessibilityEnabled(context) }
    val adapter = remember(context) { NativeCapabilities(context) }
    DisposableEffect(adapter) { onDispose { adapter.close() } }
    var failed by remember { mutableStateOf(false) }
    var workerStatus by remember { mutableStateOf(NativeWorker.status) }
    LaunchedEffect(Unit) { while (true) { workerStatus = NativeWorker.status; kotlinx.coroutines.delay(1000) } }
    PreferenceGroup("App capabilities") {
        PreferenceValue("Accessibility access", if (access) "Enabled in Android" else "Not enabled")
        TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)); failed = false }
            catch (_: Exception) { failed = true } }) { Text("Manage Android accessibility") }
        if (failed) Text("Android accessibility settings are unavailable. Access is unchanged.", color = MaterialTheme.colorScheme.error)
        Text("Inspection and actions need separate grants and selected apps in Privacy. Enabling Android access does not authorize a task.", style = MaterialTheme.typography.bodySmall)
        PreferenceValue("Phone tasks", workerStatus)
        TextButton(onClick = { try { if (NativeWorker.running) NativeWorker.stop(context) else NativeWorker.start(context); failed = false }
            catch (_: Exception) { failed = true } }) { Text(if (NativeWorker.running) "Stop phone tasks" else "Start phone tasks") }
        Text("Start while unlocked after enrolling this phone for execution. A visible notification remains while selected-app tasks run. Locking, Stop, revoked grants or a lost Core connection withdraws execution. Android may require opening OSCAR before launching another app.", style = MaterialTheme.typography.bodySmall)
        SupportingDetails("Available interfaces") {
            remember(revision) { adapter.status() }.forEach { capability ->
                PreferenceValue(when (capability.id) {
                    "android.app.launch" -> "Open app"; "android.link.open" -> "Open HTTPS app link"; "android.share.text" -> "Share text"
                    "android.ui.inspect" -> "Inspect selected app"; "android.ui.click" -> "Click reviewed control"; else -> "Enter reviewed text"
                }, capability.permission)
            }
            Text("App launch, links, text share, selected-app inspection, click, text input, scroll and target-relative gestures use current Core authority. Dial, message and calendar actions open system-supported review screens; they do not claim completed calls, sent messages or saved events. Screen capture remains separately consented.", style = MaterialTheme.typography.bodySmall)
        }
    }
    NativePlatformSettings()
}

@Composable internal fun NativeAppScope() {
    val (context, revision) = observedPermissions()
    val prefs = remember { context.getSharedPreferences("permissions", android.content.Context.MODE_PRIVATE) }
    var packages by remember { mutableStateOf(prefs.getString("native_action_packages", "").orEmpty()) }
    var message by remember { mutableStateOf("") }
    var saving by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    LaunchedEffect(revision) { packages = prefs.getString("native_action_packages", "").orEmpty() }
    SupportingDetails("Choose apps for reviewed actions") {
        OscarField(packages, { packages = it.take(1000); message = "" }, label = "Allowed app package IDs",
            supportingText = "Comma-separated; empty excludes every app. No accounts or app data are inspected.", modifier = Modifier.fillMaxWidth())
        TextButton(enabled = !saving, onClick = {
            val names = packages.split(',').map(String::trim).filter(String::isNotEmpty).distinct()
            if (names.size > 32 || names.any { !it.matches(Regex("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) }) message = "Use up to 32 valid package IDs. Nothing was enabled."
            else { saving = true; scope.launch {
                val saved = withContext(Dispatchers.IO) { prefs.edit().putString("native_action_packages", names.joinToString(",")).commit() }
                message = if (saved) "App exclusions saved; Core approval is still required." else "Persistence is unverified. Inspect current exclusions."
                saving = false
            } }
        }) { Text("Save apps") }
        if (message.isNotEmpty()) Text(message, style = MaterialTheme.typography.bodySmall)
    }
}
