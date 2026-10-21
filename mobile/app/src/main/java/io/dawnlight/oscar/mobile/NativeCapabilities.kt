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
internal class NativeCapabilities(private val context: Context, private val executionReady: Boolean = false, authorize: (NativeAction) -> Boolean = { false }) : AutoCloseable {
    val gate = NativeActionGate(SystemClock::elapsedRealtime, authorize)
    private val platform = NativePlatform(context)
    private val preferences get() = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
    private val changes = android.content.SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        if (key in setOf("app_actions", "accessibility_perception", "accessibility_actions", "native_action_packages", "file_perception", "file_actions", "document_tree", "clipboard_perception", "clipboard_actions", "media_perception", "media_actions", "screen_perception")) gate.invalidate()
    }
    init { preferences.registerOnSharedPreferenceChangeListener(changes) }
    override fun close() { gate.foreground(false); preferences.unregisterOnSharedPreferenceChangeListener(changes) }

    fun status(): List<NativeCapability> = nativeCapabilityIds.map { id ->
        val accessibility = id.startsWith("android.ui.")
        val permission = if (accessibility) {
            if (!accessibilityEnabled(context)) "Android accessibility access not granted"
            else if (!preferences.getBoolean("accessibility_perception", false)) "App inspection not permitted"
            else if (id != "android.ui.inspect" && !preferences.getBoolean("accessibility_actions", false)) "App actions not permitted"
            else "Selected-app inspection and actions permitted locally"
        } else if (!preferences.getBoolean("app_actions", false)) "App actions not permitted" else "Selected-app actions permitted locally"
        val platformOperation = platformCapability(id)
        val local = selectedPackages().isNotEmpty() && if (platformOperation) platform.available(id) else if (accessibility) accessibilityEnabled(context) &&
            preferences.getBoolean("accessibility_perception", false) && (id == "android.ui.inspect" || preferences.getBoolean("accessibility_actions", false))
            else preferences.getBoolean("app_actions", false)
        NativeCapability(id, supported = true, permission = permission, availability = if (executionReady && local) "available" else "blocked",
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

    private fun selectedPackages() = preferences.getString("native_action_packages", "").orEmpty().split(',').map(String::trim).filter(String::isNotEmpty)

    private fun allowed(action: NativeAction): Boolean {
        val packages = selectedPackages()
        if (action.packageName !in packages) return false
        if (platformCapability(action.capability)) return platform.available(action.capability)
        return if (action.capability.startsWith("android.ui.")) accessibilityEnabled(context) &&
            preferences.getBoolean("accessibility_perception", false) &&
            (action.capability == "android.ui.inspect" || preferences.getBoolean("accessibility_actions", false))
        else preferences.getBoolean("app_actions", false)
    }

    fun execute(activity: Context, action: NativeAction): NativeResult {
        check(action.capability.startsWith("android.files.") || action.capability == "android.screen.capture" || Looper.myLooper() == Looper.getMainLooper()) { "Native actions require the UI thread" }
        fun result(state: String, detail: String, observations: List<NativeObservation> = emptyList()) =
            NativeResult(action.requestId, action.taskId, state, detail, observations)
        try { validateNativeParameters(action.capability, org.json.JSONObject().put("package", action.packageName).put("target", action.target).put("value", action.value)) }
        catch (_: IllegalArgumentException) { return result("blocked", "Typed native parameters rejected") }
        if (!allowed(action) || !gate.admit(action)) return result("blocked", "Current scoped Core approval, foreground session and local grants required")
        val current = { gate.current(action) && allowed(action) && (activity !is Activity ||
            (action.capability.startsWith("android.ui.") || activity.hasWindowFocus()) && !activity.isFinishing && !activity.isDestroyed) }
        return try {
            if (platformCapability(action.capability)) platform.execute(action, current)
            else if (action.capability.startsWith("android.ui.")) {
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
                    "android.phone.dial" -> {
                        require(action.value.matches(Regex("\\+?[0-9 ()-]{1,40}")))
                        Intent(Intent.ACTION_DIAL, Uri.fromParts("tel", action.value, null)).setComponent(component)
                    }
                    "android.message.compose" -> {
                        val draft = org.json.JSONObject(action.value)
                        require(draft.keysSet() == setOf("number", "text") && draft.getString("number").matches(Regex("\\+?[0-9 ()-]{1,40}")) && draft.getString("text").length <= 1000)
                        Intent(Intent.ACTION_SENDTO, Uri.fromParts("smsto", draft.getString("number"), null))
                            .putExtra("sms_body", draft.getString("text")).setComponent(component)
                    }
                    "android.contact.view" -> {
                        require(action.value.matches(Regex("[0-9]{1,20}")))
                        Intent(Intent.ACTION_VIEW, android.content.ContentUris.withAppendedId(android.provider.ContactsContract.Contacts.CONTENT_URI, action.value.toLong())).setComponent(component)
                    }
                    "android.calendar.insert" -> {
                        val draft = org.json.JSONObject(action.value)
                        require(draft.keysSet() == setOf("title", "begin_ms", "end_ms") && draft.getString("title").length in 1..300 &&
                            draft.getLong("begin_ms") > 0 && draft.getLong("begin_ms") < draft.getLong("end_ms") && draft.getLong("end_ms") < 4_102_444_800_000L)
                        Intent(Intent.ACTION_INSERT, android.provider.CalendarContract.Events.CONTENT_URI)
                            .putExtra(android.provider.CalendarContract.Events.TITLE, draft.getString("title"))
                            .putExtra(android.provider.CalendarContract.EXTRA_EVENT_BEGIN_TIME, draft.getLong("begin_ms"))
                            .putExtra(android.provider.CalendarContract.EXTRA_EVENT_END_TIME, draft.getLong("end_ms")).setComponent(component)
                    }
                    "android.settings.open" -> {
                        val setting = when(action.value) {
                            "wifi" -> android.provider.Settings.ACTION_WIFI_SETTINGS
                            "bluetooth" -> android.provider.Settings.ACTION_BLUETOOTH_SETTINGS
                            "sound" -> android.provider.Settings.ACTION_SOUND_SETTINGS
                            "display" -> android.provider.Settings.ACTION_DISPLAY_SETTINGS
                            "application" -> android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS
                            else -> throw IllegalArgumentException("Unsupported settings page")
                        }
                        Intent(setting).apply { if (action.value == "application") data = Uri.parse("package:${context.packageName}") }.setComponent(component)
                    }
                    else -> return result("blocked", "Native capability unavailable")
                }
                if (!current()) return result("cancelled", "Authority or lifecycle changed before dispatch")
                if (activity !is Activity) intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                activity.startActivity(intent)
                result("reported", "Intent dispatched to the exact Activity; resulting state is not yet verified")
            }
        } catch (_: SecurityException) { result("blocked", "Android denied access to the target") }
        catch (_: PackageManager.NameNotFoundException) { result("blocked", "Target Activity is not visible or installed") }
        catch (_: android.content.ActivityNotFoundException) { result("blocked", "Target Activity is unavailable") }
        catch (_: IllegalArgumentException) { result("blocked", "Invalid native target") }
        catch (_: org.json.JSONException) { result("blocked", "Invalid typed native parameters") }
    }
}

internal fun platformCapability(id: String) = id.startsWith("android.files.") || id.startsWith("android.clipboard.") || id.startsWith("android.media.") || id == "android.screen.capture"

internal fun accessibilityEnabled(context: Context): Boolean = context.getSystemService(AccessibilityManager::class.java)
    .getEnabledAccessibilityServiceList(AccessibilityServiceInfo.FEEDBACK_ALL_MASK).any {
        ComponentName(it.resolveInfo.serviceInfo.packageName, it.resolveInfo.serviceInfo.name) == ComponentName(context, AppControlService::class.java)
    }
