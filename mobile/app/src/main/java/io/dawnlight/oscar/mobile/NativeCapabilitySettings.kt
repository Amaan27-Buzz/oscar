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
    PreferenceGroup("App capabilities") {
        PreferenceValue("Accessibility access", if (access) "Enabled in Android" else "Not enabled")
        TextButton(onClick = { try { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)); failed = false }
            catch (_: Exception) { failed = true } }) { Text("Manage Android accessibility") }
        if (failed) Text("Android accessibility settings are unavailable. Access is unchanged.", color = MaterialTheme.colorScheme.error)
        Text("Inspection and actions need separate grants and selected apps in Privacy. Enabling Android access does not authorize a task.", style = MaterialTheme.typography.bodySmall)
        SupportingDetails("Available interfaces") {
            remember(revision) { adapter.status() }.forEach { capability ->
                PreferenceValue(when (capability.id) {
                    "android.app.launch" -> "Open app"; "android.link.open" -> "Open HTTPS app link"; "android.share.text" -> "Share text"
                    "android.ui.inspect" -> "Inspect selected app"; "android.ui.click" -> "Click reviewed control"; else -> "Enter reviewed text"
                }, capability.permission)
            }
            Text("These native adapters require a commissioned Core execution binding. Remote app control is currently unavailable. Screen recording, coordinate gestures and broad phone control are unavailable.", style = MaterialTheme.typography.bodySmall)
        }
    }
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
