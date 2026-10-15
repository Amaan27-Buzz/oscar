package io.dawnlight.oscar.mobile

import android.content.Context
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.graphics.asAndroidBitmap
import org.junit.Assert.*
import org.junit.*

/** Disposable emulator policy/render proof. No listener grant, real message or owner recording. */
class MobilePrivacyTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private var isolated = false
    private val prefs get() = compose.activity.getSharedPreferences("permissions", Context.MODE_PRIVATE)
    @Before fun isolate() {
        Assume.assumeTrue("Disposable emulator only", allowDisposableReview())
        isolated = true
        prefs.edit().clear().commit()
        NotificationBoundary.privacyChanged()
    }
    @After fun clear() { if (isolated) { prefs.edit().clear().commit(); NotificationBoundary.privacyChanged() } }

    @Test fun sourceExclusionsAndRevocationKeepPerceiveRetainActIndependent() {
        val context = compose.activity
        prefs.edit().putBoolean("notification_context", true).putString("notification_sources", "example.allowed").commit()
        // A simulated platform input proves policy logic; real listener permission stays denied.
        assertTrue(NotificationBoundary.sourceAllowed(context, "example.allowed", true))
        assertFalse(NotificationBoundary.sourceAllowed(context, "example.allowed", false))
        assertFalse(NotificationBoundary.sourceAllowed(context, "example.excluded", true))
        assertFalse(prefs.getBoolean("notification_reply", false))
        prefs.edit().putBoolean("notification_context", false).putBoolean("notification_reply", true).commit()
        NotificationBoundary.privacyChanged()
        assertFalse(NotificationBoundary.sourceAllowed(context, "example.allowed", true))
        assertFalse(NativeVoice.permitted(context))
        assertTrue(NotificationBoundary.exposed().isEmpty())
        assertFalse(NotificationBoundary.current(org.json.JSONObject().put("package", "example.allowed").put("key_hash", "a".repeat(64))))
    }

    @Test fun notificationMetadataHidesSensitiveContentAndIdentityRejectsChanges() {
        fun fixture(text: String): android.service.notification.StatusBarNotification {
            val notification = android.app.Notification.Builder(compose.activity, "reference")
                .setContentTitle("Synthetic OTP 111111").setContentText(text).build()
            return android.service.notification.StatusBarNotification("example.allowed", "example.allowed", 1, null,
                0, 0, 0, notification, android.os.Process.myUserHandle(), 123L)
        }
        val original = fixture("Synthetic password-only fixture")
        val data = NotificationBoundary.metadata(original).toString()
        assertFalse(data.contains("111111")); assertFalse(data.contains("password")); assertFalse(data.contains("OTP"))
        assertTrue(data.contains("example.allowed"))
        assertNotEquals(NotificationBoundary.identity(original), NotificationBoundary.identity(fixture("Changed synthetic content")))
    }

    @Test fun invalidSourcesDeniedAccessAndLiveLocalRevocationRemainUsable() {
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText("Privacy").performClick()
        compose.onNodeWithText("Choose notification sources").performScrollTo().performClick()
        compose.onNodeWithTag("notificationSources").performScrollTo().performTextInput("invalid")
        compose.onNodeWithTag("notificationSources").assertTextContains("invalid")
        androidx.test.espresso.Espresso.closeSoftKeyboard()
        compose.waitUntil(5000) { !compose.activity.window.decorView.rootWindowInsets.isVisible(android.view.WindowInsets.Type.ime()) }
        compose.onNodeWithText("Save sources").performScrollTo().performClick()
        compose.onNodeWithText("Use up to 32 package IDs, such as example.app. Nothing was enabled.").assertExists()
        assertEquals("", prefs.getString("notification_sources", ""))
        compose.onNodeWithTag("notificationSources").performTextReplacement("example.allowed")
        androidx.test.espresso.Espresso.closeSoftKeyboard()
        compose.waitUntil(5000) { !compose.activity.window.decorView.rootWindowInsets.isVisible(android.view.WindowInsets.Type.ime()) }
        compose.onNodeWithText("Save sources").performScrollTo().performClick()
        compose.waitUntil(5000) { prefs.getString("notification_sources", "") == "example.allowed" }
        val contextGrant = compose.onNodeWithContentDescription("Selected notification context")
        contextGrant.performScrollTo().performClick()
        compose.waitUntil(5000) { prefs.getBoolean("notification_context", false) }
        assertFalse(compose.activity.getSystemService(android.app.NotificationManager::class.java)
            .isNotificationListenerAccessGranted(android.content.ComponentName(compose.activity, NotificationBoundary::class.java)))
        assertTrue(NotificationBoundary.exposed().isEmpty())
        prefs.edit().putBoolean("notification_context", false).commit()
        contextGrant.assertIsOff()
        val voiceEpoch = VoicePresentation.begin()
        compose.onNodeWithText("Revoke OSCAR grants").performScrollTo().performClick()
        compose.waitUntil(5000) { prefs.getString("notification_sources", "") == "" }
        compose.waitUntil(5000) { !VoicePresentation.current(voiceEpoch) }
        assertFalse(prefs.getBoolean("microphone_perception", false)); assertFalse(prefs.getBoolean("notification_reply", false))
        assertFalse(NativeVoice.permitted(compose.activity))
        assertFalse(VoicePresentation.current(voiceEpoch))
        compose.onNodeWithText("Perception").performScrollTo()
        capture()
    }

    private fun capture() = captureReview(compose, "13-6-privacy-reference")
}
