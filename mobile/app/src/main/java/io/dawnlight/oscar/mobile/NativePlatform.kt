package io.dawnlight.oscar.mobile

import android.content.*
import android.media.session.MediaSessionManager
import android.net.Uri
import android.os.Build
import android.provider.DocumentsContract
import org.json.JSONObject

/** Scoped platform operations; no broad storage, contacts, SMS, call or settings privileges. */
internal class NativePlatform(private val context: Context) {
    private val prefs get() = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
    fun available(id: String): Boolean = when {
        id.startsWith("android.files.") -> tree(id.endsWith("write")) != null && prefs.getBoolean(if (id.endsWith("read")) "file_perception" else "file_actions", false)
        id.startsWith("android.clipboard.") -> MainActivity.foregroundActivity?.hasWindowFocus() == true && prefs.getBoolean(if (id.endsWith("read")) "clipboard_perception" else "clipboard_actions", false)
        id.startsWith("android.media.") -> context.getSystemService(android.app.NotificationManager::class.java).isNotificationListenerAccessGranted(ComponentName(context, NotificationBoundary::class.java)) &&
            prefs.getBoolean(if (id.endsWith("inspect")) "media_perception" else "media_actions", false)
        id == "android.screen.capture" -> NativeScreenService.current != null && prefs.getBoolean("screen_perception", false) && accessibilityEnabled(context) && prefs.getBoolean("accessibility_perception", false)
        else -> false
    }
    fun execute(action: NativeAction, current: () -> Boolean): NativeResult {
        fun result(state: String, detail: String, data: String? = null) = NativeResult(action.requestId, action.taskId, state, detail,
            if (data == null) emptyList() else listOf(NativeObservation(action.target.ifEmpty { action.capability }, data, false, false)))
        if (!available(action.capability) || !current()) return result("blocked", "Separate current platform grant required")
        return try {
            when {
                action.capability.startsWith("android.files.") -> {
                    require(action.packageName == context.packageName)
                    val root = tree(action.capability.endsWith("write")) ?: return result("blocked", "Choose an Android document folder first")
                    val rootId = DocumentsContract.getTreeDocumentId(root)
                    val children = DocumentsContract.buildChildDocumentsUriUsingTree(root, rootId)
                    val matches = mutableListOf<String>()
                    context.contentResolver.query(children, arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID, DocumentsContract.Document.COLUMN_DISPLAY_NAME), null, null, null)?.use { cursor ->
                        var scanned = 0
                        while (cursor.moveToNext()) {
                            require(++scanned <= 512 && current())
                            if (cursor.getString(1) == action.target) matches.add(cursor.getString(0))
                        }
                    } ?: return result("blocked", "Document provider could not enumerate selected folder")
                    require(matches.size <= 1)
                    var document = matches.singleOrNull()?.let { DocumentsContract.buildDocumentUriUsingTree(root, it) }
                    if (action.capability.endsWith("write")) {
                        if (!current()) return result("cancelled", "Authority changed before document mutation")
                        if (document == null) document = DocumentsContract.createDocument(context.contentResolver,
                            DocumentsContract.buildDocumentUriUsingTree(root, rootId), "text/plain", action.target)
                        require(document != null && current())
                        context.contentResolver.openOutputStream(document, "wt")?.use { stream ->
                            require(current()); stream.write(action.value.toByteArray(Charsets.UTF_8)); stream.flush()
                        } ?: return result("failed", "Document provider did not open the selected document")
                        result("reported", "Document stream written; separate readback required")
                    } else {
                        require(document != null && current())
                        val bytes = context.contentResolver.openInputStream(document)?.use { stream ->
                            val buffer = ByteArray(4097); var size = 0
                            while (size < buffer.size) { require(current()); val read = stream.read(buffer, size, buffer.size - size); if (read < 0) break; size += read }
                            buffer.copyOf(size)
                        } ?: return result("blocked", "Selected document unavailable")
                        require(bytes.size <= 4096 && current())
                        val text = Charsets.UTF_8.newDecoder().onMalformedInput(java.nio.charset.CodingErrorAction.REPORT).decode(java.nio.ByteBuffer.wrap(bytes)).toString()
                        result("reported", "Fresh bounded selected document read", text)
                    }
                }
                action.capability.startsWith("android.clipboard.") -> {
                    require(action.packageName == context.packageName && MainActivity.foregroundActivity?.hasWindowFocus() == true && current())
                    val clipboard = context.getSystemService(ClipboardManager::class.java)
                    if (action.capability.endsWith("write")) {
                        clipboard.setPrimaryClip(ClipData.newPlainText("OSCAR", action.value))
                        result("reported", "Plain text clipboard write; separate readback required")
                    } else {
                        val clip = clipboard.primaryClip ?: return result("blocked", "Clipboard unavailable in this foreground context")
                        require(clip.itemCount == 1 && !(Build.VERSION.SDK_INT >= 33 && clip.description.extras?.getBoolean("android.content.extra.IS_SENSITIVE", false) == true))
                        val item = clip.getItemAt(0); require(item.uri == null && item.intent == null)
                        val text = item.text?.toString() ?: return result("blocked", "Only plain text clipboard content is supported")
                        require(text.length <= 2000 && current()); result("reported", "Fresh foreground clipboard read", text)
                    }
                }
                action.capability.startsWith("android.media.") -> {
                    val sessions = context.getSystemService(MediaSessionManager::class.java).getActiveSessions(ComponentName(context, NotificationBoundary::class.java)).filter { it.packageName == action.packageName }
                    require(sessions.size == 1 && current()); val session = sessions.single()
                    if (action.capability.endsWith("control")) {
                        when (action.value) { "play" -> session.transportControls.play(); "pause" -> session.transportControls.pause(); "next" -> session.transportControls.skipToNext(); "previous" -> session.transportControls.skipToPrevious(); "stop" -> session.transportControls.stop(); else -> throw IllegalArgumentException() }
                        result("reported", "Media command dispatched; fresh playback-state readback required")
                    } else result("reported", "Fresh selected media session read", JSONObject().put("package", session.packageName)
                        .put("state", session.playbackState?.state ?: JSONObject.NULL).put("position_ms", session.playbackState?.position ?: JSONObject.NULL).toString())
                }
                action.capability == "android.screen.capture" -> {
                    require(AppControlService.connected?.selectedPackage() == action.packageName && current())
                    val image = NativeScreenService.current?.capture(action.packageName, current) ?: return result("blocked", "No fresh consented screen frame")
                    require(current() && AppControlService.connected?.selectedPackage() == action.packageName)
                    result("reported", "Transient observation within Android screen-sharing consent", image)
                }
                else -> result("blocked", "Platform capability unavailable")
            }
        } catch (_: SecurityException) { result("blocked", "Android denied the selected platform operation") }
        catch (_: Exception) { result("failed", "Platform state changed or operation is unavailable; inspect before retry") }
    }
    private fun tree(write: Boolean = false): Uri? {
        val uri = prefs.getString("document_tree", null)?.let(Uri::parse) ?: return null
        return uri.takeIf { selected -> context.contentResolver.persistedUriPermissions.any { it.uri == selected && it.isReadPermission && (!write || it.isWritePermission) } }
    }
}
