package io.dawnlight.oscar.mobile

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.*
import androidx.compose.runtime.*

@Composable internal fun NativePlatformSettings() {
    val (context, revision) = observedPermissions()
    val prefs = remember { context.getSharedPreferences("permissions", Context.MODE_PRIVATE) }
    var message by remember { mutableStateOf("") }
    val folder = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        if (uri != null) try {
            context.contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            check(prefs.edit().putString("document_tree", uri.toString()).commit())
            message = "Folder selected. Reading and writing remain separate local grants."
        } catch (_: Exception) { message = "Folder permission could not be saved. Access is unconfirmed." }
    }
    val screen = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { response ->
        if (response.resultCode == Activity.RESULT_OK && response.data != null) try {
            context.startForegroundService(Intent(context, NativeScreenService::class.java).putExtra("result", response.resultCode).putExtra("consent", response.data))
            message = "Screen sharing requested. Screen observations still need selected-app perception and current Core authority."
        } catch (_: Exception) { message = "Android did not start screen sharing." }
        else message = "Screen sharing was not enabled."
    }
    PreferenceGroup("Selected platform access") {
        TextButton(onClick = { folder.launch(null) }) { Text("Choose document folder") }
        PreferenceValue("Document folder", if (remember(revision) { prefs.contains("document_tree") }) "Selected in Android" else "Not selected")
        TextButton(onClick = { prefs.getString("document_tree", null)?.let { value ->
            try { context.contentResolver.releasePersistableUriPermission(android.net.Uri.parse(value), Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION) }
            catch (_: Exception) { message = "Android folder permission removal is unverified." }
            prefs.edit().remove("document_tree").putBoolean("file_perception", false).putBoolean("file_actions", false).apply()
        } }) { Text("Remove folder access") }
        LocalGrant("Read selected documents", "file_perception", "Bounded text documents in the selected folder only.")
        LocalGrant("Write selected documents", "file_actions", "Create or replace reviewed text documents. Core action authority is separate.")
        LocalGrant("Read clipboard", "clipboard_perception", "Plain text while OSCAR is the focused app; sensitive clips are excluded.")
        LocalGrant("Write clipboard", "clipboard_actions", "Reviewed plain text while OSCAR is focused.")
        LocalGrant("Inspect media playback", "media_perception", "Selected apps only; Android notification access must also be enabled.")
        LocalGrant("Control media playback", "media_actions", "Play, pause, next, previous and stop in a selected active media session.")
        LocalGrant("Observe shared screen", "screen_perception", "Requires Android screen-sharing consent for every session and selected-app inspection. No recording is retained.")
        Text("Android controls what is shared. Choose one app in its consent screen to limit capture; sharing the entire screen can include overlays and other visible content.", style = MaterialTheme.typography.bodySmall)
        TextButton(onClick = { if (NativeScreenService.current != null) context.stopService(Intent(context, NativeScreenService::class.java))
            else try { screen.launch(context.getSystemService(MediaProjectionManager::class.java).createScreenCaptureIntent()) }
            catch (_: Exception) { message = "Screen-sharing consent is unavailable." } }) { Text(if (NativeScreenService.current != null) "Stop screen sharing" else "Review screen-sharing consent") }
        Text("Calls, messages, contact and calendar actions open supported review screens. They do not grant access to private provider databases or silently send, call or save.", style = MaterialTheme.typography.bodySmall)
        if (message.isNotEmpty()) Text(message, style = MaterialTheme.typography.bodySmall)
    }
}
