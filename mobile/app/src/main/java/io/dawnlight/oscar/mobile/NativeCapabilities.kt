package io.dawnlight.oscar.mobile

import android.accessibilityservice.AccessibilityServiceInfo
import android.app.Activity
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Looper
import android.os.SystemClock
import android.view.accessibility.AccessibilityManager

internal data class NativeCapability(val id: String, val version: Int = 1, val supported: Boolean,
    val permission: String, val availability: String, val verification: String,
    val executor: String = "android-native", val authorityMode: String = "ask",
    val retry: String = "Never automatically replay; inspect resulting state first",
    val sideEffects: String = if (id == "android.ui.inspect") "Transient selected-app observation" else "Changes the reviewed app or foreground Activity")

/** Execution adapter only. Core owns catalog selection, durable tasks, policy, approval and verification. */
internal class NativeCapabilities(private val context: Context, authorize: (NativeAction) -> Boolean = { false }) : AutoCloseable {
    val gate = NativeActionGate(SystemClock::elapsedRealtime, authorize)
    private val preferences get() = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
    private val changes = android.content.SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        if (key in setOf("app_actions", "accessibility_perception", "accessibility_actions", "native_action_packages")) gate.invalidate()
    }
    init { preferences.registerOnSharedPreferenceChangeListener(changes) }
    override fun close() { gate.foreground(false); preferences.unregisterOnSharedPreferenceChangeListener(changes) }

    fun status(): List<NativeCapability> = nativeCapabilityIds.map { id ->
        val accessibility = id.startsWith("android.ui.")
        val permission = if (accessibility) {
            if (!accessibilityEnabled(context)) "Android accessibility access not granted"
            else if (!preferences.getBoolean("accessibility_perception", false)) "App inspection not permitted"
            else if (id != "android.ui.inspect" && !preferences.getBoolean("accessibility_actions", false)) "App actions not permitted"
            else "Requires an exact Core review and selected app"
        } else if (!preferences.getBoolean("app_actions", false)) "App actions not permitted" else "Requires an exact Core review and selected app"
        NativeCapability(id, supported = true, permission = permission, availability = "blocked",
            verification = if (accessibility) "Fresh target UI readback; action return alone is REPORTED" else "Intent dispatch is REPORTED; target result requires independent readback")
    }

    fun cancel(requestId: String) = gate.cancel(requestId)
    fun revoke() = gate.invalidate()

    /** Package visibility is platform-controlled. Only an already selected app is queried. */
    fun discover(packageName: String): List<String> {
        if (packageName !in preferences.getString("native_action_packages", "").orEmpty().split(',').map(String::trim)) return emptyList()
        @Suppress("DEPRECATION")
        return context.packageManager.queryIntentActivities(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER).setPackage(packageName), 0)
            .filter { it.activityInfo.enabled && it.activityInfo.exported && it.activityInfo.packageName == packageName }
            .take(32).map { it.activityInfo.name }.distinct()
    }

    private fun allowed(action: NativeAction): Boolean {
        val packages = preferences.getString("native_action_packages", "").orEmpty().split(',').map(String::trim)
        if (action.packageName !in packages) return false
        return if (action.capability.startsWith("android.ui.")) accessibilityEnabled(context) &&
            preferences.getBoolean("accessibility_perception", false) &&
            (action.capability == "android.ui.inspect" || preferences.getBoolean("accessibility_actions", false))
        else preferences.getBoolean("app_actions", false)
    }

    fun execute(activity: Activity, action: NativeAction): NativeResult {
        check(Looper.myLooper() == Looper.getMainLooper()) { "Native actions require the UI thread" }
        fun result(state: String, detail: String, observations: List<NativeObservation> = emptyList()) =
            NativeResult(action.requestId, action.taskId, state, detail, observations)
        if (!allowed(action) || !gate.admit(action)) return result("blocked", "Current scoped Core approval, foreground session and local grants required")
        val current = { gate.current(action) && allowed(action) &&
            (action.capability.startsWith("android.ui.") || activity.hasWindowFocus()) && !activity.isFinishing && !activity.isDestroyed }
        return try {
            if (action.capability.startsWith("android.ui.")) {
                val service = AppControlService.connected ?: return result("blocked", "Accessibility service is not connected")
                service.perform(action, current)
            } else {
                val component = ComponentName(action.packageName, action.target)
                @Suppress("DEPRECATION") val info = context.packageManager.getActivityInfo(component, 0)
                if (!info.enabled || (!info.exported && action.packageName != context.packageName)) return result("blocked", "Target Activity is unavailable")
                val intent = when (action.capability) {
                    "android.app.launch" -> Intent(Intent.ACTION_MAIN).setComponent(component)
                    "android.link.open" -> {
                        val uri = Uri.parse(action.value)
                        if (uri.scheme != "https" || uri.host.isNullOrBlank() || uri.userInfo != null) return result("blocked", "Only an exact HTTPS app link is supported")
                        Intent(Intent.ACTION_VIEW, uri).addCategory(Intent.CATEGORY_BROWSABLE).setComponent(component)
                    }
                    "android.share.text" -> Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, action.value).setComponent(component)
                    else -> return result("blocked", "Native capability unavailable")
                }
                if (!current()) return result("cancelled", "Authority or lifecycle changed before dispatch")
                activity.startActivity(intent)
                result("reported", "Intent dispatched to the exact Activity; resulting state is not yet verified")
            }
        } catch (_: SecurityException) { result("blocked", "Android denied access to the target") }
        catch (_: PackageManager.NameNotFoundException) { result("blocked", "Target Activity is not visible or installed") }
        catch (_: android.content.ActivityNotFoundException) { result("blocked", "Target Activity is unavailable") }
        catch (_: IllegalArgumentException) { result("blocked", "Invalid native target") }
    }
}

internal fun accessibilityEnabled(context: Context): Boolean = context.getSystemService(AccessibilityManager::class.java)
    .getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK).any {
        ComponentName(it.resolveInfo.serviceInfo.packageName, it.resolveInfo.serviceInfo.name) == ComponentName(context, AppControlService::class.java)
    }
