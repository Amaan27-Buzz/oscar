package io.dawnlight.oscar.mobile

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.os.Bundle
import android.os.Build
import android.graphics.Path
import android.graphics.Rect
import android.accessibilityservice.GestureDescription
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/** User-enabled exact-task adapter. Events are discarded; no continuous capture. */
class AppControlService : AccessibilityService() {
    internal fun selectedPackage(): String? = rootInActiveWindow?.packageName?.toString()
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
            "android.ui.scroll" -> node.isScrollable && action.value in setOf("forward", "backward") && node.performAction(
                if (action.value == "forward") AccessibilityNodeInfo.ACTION_SCROLL_FORWARD else AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD)
            "android.ui.gesture" -> {
                val bounds = Rect().also(node::getBoundsInScreen)
                val rootBounds = Rect().also(root::getBoundsInScreen)
                if (node.isEditable || bounds.width() < 20 || bounds.height() < 20 || !rootBounds.contains(bounds) ||
                    action.value !in setOf("up", "down", "left", "right") || !current()) return result("blocked", "Safe target-relative gesture required")
                val x = bounds.exactCenterX(); val y = bounds.exactCenterY()
                val dx = bounds.width() * 0.3f; val dy = bounds.height() * 0.3f
                val path = Path().apply { when(action.value) {
                    "up" -> { moveTo(x, y + dy); lineTo(x, y - dy) }
                    "down" -> { moveTo(x, y - dy); lineTo(x, y + dy) }
                    "left" -> { moveTo(x + dx, y); lineTo(x - dx, y) }
                    else -> { moveTo(x - dx, y); lineTo(x + dx, y) }
                } }
                dispatchGesture(GestureDescription.Builder().addStroke(GestureDescription.StrokeDescription(path, 0, 200)).build(), null, null)
            }
            else -> false
        }
        return result(if (accepted) "reported" else "failed", if (accepted) "Android accepted the action; fresh independent result readback is required" else "Android did not perform the action")
    }

    private fun sensitive(node: AccessibilityNodeInfo) = Build.VERSION.SDK_INT >= 34 && node.isAccessibilityDataSensitive

    companion object { @Volatile internal var connected: AppControlService? = null; private set }
}
