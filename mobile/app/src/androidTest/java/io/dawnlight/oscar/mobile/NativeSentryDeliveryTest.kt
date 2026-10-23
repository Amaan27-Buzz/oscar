package io.dawnlight.oscar.mobile

import android.Manifest
import android.app.NotificationManager
import android.app.UiAutomation
import android.content.Context
import android.content.pm.PackageManager
import androidx.activity.compose.setContent
import androidx.compose.material3.Surface
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

/** Real surfaces fed synthetic Core metadata; no live perception or owner commissioning. */
class NativeSentryDeliveryTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun genericSurfaceNotificationPermissionNoReplayAndRevocation() {
        assumeTrue(android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        check(InstrumentationRegistry.getArguments().getString("sentry_disposable") == "true")
        val context = instrumentation.targetContext
        val manager = context.getSystemService(NotificationManager::class.java)
        val preferences = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
        val priorOptIn = preferences.getBoolean("task_alerts", false)
        val priorPermission = context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
        check(!priorPermission) { "Disposable fixture must start without notification permission" }
        val automation = instrumentation.getUiAutomation(UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES)
        fun shell(command: String) = automation.executeShellCommand(command).use { descriptor ->
            android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).use { it.readBytes() }
        }
        val now = System.currentTimeMillis()
        val identifier = java.security.MessageDigest.getInstance("SHA-256").digest("synthetic-$now".toByteArray()).joinToString("") { "%02x".format(it) }
        val secondIdentifier = java.security.MessageDigest.getInstance("SHA-256").digest("synthetic-next-$now".toByteArray()).joinToString("") { "%02x".format(it) }
        val sentry = JSONObject("""{"mode":"sentry","state":"aware","allow_interrupt":true,"generation":1,
            "source_ids":["synthetic-selected"],"trigger_keys":["status"],"sources":[{"id":"synthetic-selected","epoch":1,"perceive":true,"act":true}],
            "alerts":[{"id":"$identifier","source_id":"synthetic-selected","source_epoch":1,"generation":1,"observation_id":"synthetic-observation","key":"status","fresh_until":${(now + 60_000) / 1000.0},"simulated":true,"policy_ids":["synthetic-delivery"]}]}""")
        fun snapshot() = CoreSnapshot(emptyList(), emptyList(), now, management = ManagementView("synthetic-owner", "ask", "inactive", null, 0, emptyList(), emptyList(), JSONObject().put("sentry", sentry).toString()))
        fun posted() = manager.activeNotifications.filter { it.tag == "sentry:$identifier" }
        try {
            preferences.edit().putBoolean("task_alerts", true).commit()
            TaskNotifications(context).changed(null, snapshot(), now)
            assertTrue(posted().isEmpty())
            shell("pm grant ${context.packageName} android.permission.POST_NOTIFICATIONS")
            preferences.edit().putBoolean("task_alerts", false).commit()
            TaskNotifications(context).changed(null, snapshot(), now)
            assertTrue(posted().isEmpty())
            preferences.edit().putBoolean("task_alerts", true).commit()
            TaskNotifications(context).changed(null, snapshot(), now + 60_001)
            assertTrue(posted().isEmpty())
            val current = snapshot()
            compose.runOnIdle { compose.activity.setContent { OscarTheme { Surface {
                SentryNotices(MobileState(link = Link.CONNECTED, snapshot = current, observedAt = now,
                    clock = CoreClock(now, android.os.SystemClock.elapsedRealtime())))
            } } } }
            compose.onNodeWithText("Simulated · synthetic-selected · status").assertIsDisplayed()
            TaskNotifications(context).changed(null, current, now + 10_000)
            compose.waitUntil(5000) { posted().size == 1 }
            val notification = posted().single().notification
            assertTrue(notification.timeoutAfter in 1..50_000)
            assertEquals("OSCAR · Awareness · Simulated", notification.extras.getString("android.title"))
            assertFalse(notification.extras.getString("android.text").orEmpty().contains("synthetic-selected"))
            manager.cancel("sentry:$identifier", 2)
            TaskNotifications(context).changed(null, current, now)
            assertTrue(posted().isEmpty())
            sentry.getJSONArray("alerts").getJSONObject(0).put("id", secondIdentifier)
            TaskNotifications(context).changed(null, snapshot(), now)
            compose.waitUntil(5000) { manager.activeNotifications.any { it.tag == "sentry:$secondIdentifier" } }
            sentry.getJSONArray("sources").getJSONObject(0).put("act", false)
            TaskNotifications(context).changed(null, snapshot(), now)
            assertFalse(manager.activeNotifications.any { it.tag == "sentry:$secondIdentifier" })
            compose.runOnIdle { compose.activity.setContent { OscarTheme { Surface {
                SentryNotices(MobileState(link = Link.CONNECTED, snapshot = snapshot(), observedAt = now,
                    clock = CoreClock(now, android.os.SystemClock.elapsedRealtime())))
            } } } }
            compose.onNodeWithText("Simulated · synthetic-selected · status").assertDoesNotExist()
        } finally {
            manager.cancel("sentry:$identifier", 2)
            manager.cancel("sentry:$secondIdentifier", 2)
            context.getSharedPreferences("sentry_notice_receipts", Context.MODE_PRIVATE).edit().remove(identifier).remove(secondIdentifier).commit()
            preferences.edit().putBoolean("task_alerts", priorOptIn).commit()
            // The disposable fixture is uninstalled by its runner; revoking here kills instrumentation.
        }
    }
}
