package io.dawnlight.oscar.mobile

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.os.Bundle
import android.os.Build
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/** User-enabled deterministic adapter. Events are discarded; no background capture or autonomous actions. */
class AppControlService : AccessibilityService() {
    override fun onServiceConnected() { connected = this }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit
    override fun onInterrupt() { if (connected === this) connected = null }
    override fun onUnbind(intent: Intent?): Boolean { if (connected === this) connected = null; return super.onUnbind(intent) }
    override fun onDestroy() { if (connected === this) connected = null; super.onDestroy() }

    internal fun perform(action: NativeAction, current: () -> Boolean): NativeResult {
        fun result(state: String, detail: String, observations: List<NativeObservation> = emptyList()) = NativeResult(action.requestId, action.taskId, state, detail, observations)
        if (!current()) return result("cancelled", "Authority is no longer current")
        val root = rootInActiveWindow ?: return result("blocked", "No accessible foreground window")
        if (root.packageName?.toString() != action.packageName) return result("blocked", "Foreground app differs from the reviewed target")
        if (action.capability == "android.ui.inspect") {
            val pending = java.util.ArrayDeque<AccessibilityNodeInfo>().apply { add(root) }
            val observations = mutableListOf<NativeObservation>()
            var visited = 0
            while (pending.isNotEmpty() && visited++ < 128) {
                if (!current()) return result("cancelled", "Authority changed during inspection")
                val node = pending.removeFirst()
                if (node.packageName?.toString() != action.packageName || !node.isVisibleToUser || node.isPassword || sensitive(node)) continue
                observations.add(NativeObservation(node.viewIdResourceName.orEmpty(), (node.text?.toString() ?: node.contentDescription?.toString()).orEmpty().take(256), node.isClickable, node.isEditable))
                for (index in 0 until node.childCount.coerceAtMost(128 - pending.size)) node.getChild(index)?.let(pending::add)
            }
            return result("reported", "Bounded transient UI observation; no retained content or independent verification", observations)
        }
        if (!action.target.startsWith("${action.packageName}:id/")) return result("blocked", "Exact target resource ID required")
        val nodes = root.findAccessibilityNodeInfosByViewId(action.target).filter { it.packageName?.toString() == action.packageName && it.isVisibleToUser }
        if (nodes.size != 1) return result("blocked", "Target is missing or ambiguous")
        val node = nodes.single()
        if (!node.refresh() || node.packageName?.toString() != action.packageName || !node.isVisibleToUser || node.isPassword || sensitive(node) || !node.isEnabled || !current()) return result("blocked", "Target is sensitive, stale or no longer permitted")
        val foreground = rootInActiveWindow
        if (foreground?.packageName?.toString() != action.packageName || foreground.windowId != node.windowId) return result("blocked", "Foreground target changed before the action")
        val accepted = when (action.capability) {
            "android.ui.click" -> node.isClickable && node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            "android.ui.set_text" -> node.isEditable && node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,
                Bundle().apply { putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, action.value) })
            else -> false
        }
        return result(if (accepted) "reported" else "failed", if (accepted) "Android accepted the action; fresh independent result readback is required" else "Android did not perform the action")
    }

    private fun sensitive(node: AccessibilityNodeInfo) = Build.VERSION.SDK_INT >= 34 && node.isAccessibilityDataSensitive

    companion object { @Volatile internal var connected: AppControlService? = null; private set }
}
