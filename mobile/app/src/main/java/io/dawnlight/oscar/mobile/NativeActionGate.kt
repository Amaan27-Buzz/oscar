package io.dawnlight.oscar.mobile

import java.util.UUID

/** Native admission is subordinate to an exact, live Core decision. It creates no grants. */
internal data class NativeAction(
    val requestId: String, val taskId: String, val nodeId: String, val sessionId: String,
    val taskGeneration: Long, val authorityEpoch: Long,
    val generation: String, val deadlineElapsed: Long, val capability: String,
    val packageName: String, val target: String = "", val value: String = "",
)
internal data class NativeResult(
    val requestId: String, val taskId: String, val state: String, val detail: String,
    val observations: List<NativeObservation> = emptyList(),
)
internal data class NativeObservation(val resourceId: String, val text: String, val clickable: Boolean, val editable: Boolean)

internal class NativeActionGate(private val now: () -> Long, private val authorize: (NativeAction) -> Boolean) {
    var generation: String = UUID.randomUUID().toString(); private set
    private var foreground = false
    private val admitted = mutableSetOf<String>()
    private val cancelled = mutableSetOf<String>()

    @Synchronized fun foreground(value: Boolean) { if (!value) invalidate(); foreground = value }
    @Synchronized fun invalidate() { generation = UUID.randomUUID().toString(); admitted.clear(); cancelled.clear() }
    @Synchronized fun cancel(requestId: String) { if (cancelled.size < 128) cancelled.add(requestId) else invalidate() }
    @Synchronized fun current(action: NativeAction): Boolean = foreground && action.generation == generation &&
        action.requestId !in cancelled && action.deadlineElapsed > now() && action.deadlineElapsed - now() <= 60_000 &&
        try { authorize(action) } catch (_: Exception) { false }

    @Synchronized fun admit(action: NativeAction): Boolean {
        if (listOf(action.requestId, action.taskId, action.nodeId, action.sessionId).any { it.isBlank() || it.length > 128 } ||
            action.taskGeneration < 0 || action.authorityEpoch < 0 ||
            action.packageName.length > 256 || !action.packageName.matches(Regex("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) ||
            action.target.length > 512 || action.value.length > 2000 || action.capability !in nativeCapabilityIds ||
            admitted.size >= 128 || action.requestId in admitted || !current(action)) return false
        admitted.add(action.requestId)
        return true
    }
}

internal val nativeCapabilityIds = setOf("android.app.launch", "android.link.open", "android.share.text", "android.ui.inspect", "android.ui.click", "android.ui.set_text",
    "android.ui.scroll", "android.ui.gesture", "android.phone.dial", "android.message.compose", "android.contact.view", "android.calendar.insert", "android.settings.open",
    "android.files.read", "android.files.write", "android.clipboard.read", "android.clipboard.write", "android.media.inspect", "android.media.control", "android.screen.capture")
