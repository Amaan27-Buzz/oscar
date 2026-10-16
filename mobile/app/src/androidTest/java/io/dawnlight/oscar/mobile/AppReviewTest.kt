package io.dawnlight.oscar.mobile

import android.content.Context
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.Before
import org.junit.Rule
import org.junit.Test

/** Visit actual production routes; fixtures remain isolated from the owner's app. */
class AppReviewTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Before fun prepare() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        val session = androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java]
        compose.waitUntil(5000) { !session.state.value.restoring }
        compose.runOnIdle {
            compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            session.disconnect()
            compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("theme", "light").putString("motion", "reduced").commit()
        }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
        compose.runOnIdle { session.message("") }
    }
    private fun secondary(name: String) {
        compose.onAllNodesWithTag("app-toolbar").assertCountEquals(1)
        compose.onAllNodesWithTag("page-back").assertCountEquals(1)
        compose.onNodeWithTag("primary-navigation").assertDoesNotExist()
        captureReview(compose, "review-$name")
    }
    @Test fun allSettingsAndSecondaryRoutesHaveOneNavigationBar() {
        for ((label, name) in listOf("Persona" to "persona", "Voice" to "voice-settings", "Privacy" to "privacy",
            "Awareness" to "awareness", "Memory" to "memory", "Access" to "access", "Android permissions" to "android",
            "Notifications" to "notifications", "Appearance" to "appearance", "Diagnostics" to "diagnostics", "About" to "about")) {
            navigateReview(compose, "SETTINGS")
            secondary("preferences")
            compose.onNodeWithText(label).performScrollTo().performClick()
            secondary(name)
        }
        navigateReview(compose, "DEVICES")
        secondary("devices")
        compose.onNodeWithText("Connect Core").performClick()
        compose.onNodeWithText("Connect this phone").assertExists()
        compose.onNodeWithText("Connect", substring = false).assertIsNotEnabled()
        captureReview(compose, "review-connection")
        compose.onNodeWithText("Cancel").performClick()
        compose.onNodeWithTag("page-back").performClick()
        navigateReview(compose, "ACTIVITY")
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText("Awareness").performScrollTo().performClick()
        compose.onNodeWithText("Microphone").performScrollTo().performClick()
        secondary("privacy-from-awareness")
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithText("Awareness is off").assertExists()
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithTag("destination-ACTIVITY").assertIsSelected()
        navigateReview(compose, "OSCAR")
        compose.onNodeWithText("Today").performScrollTo().performClick()
        secondary("today")
        navigateReview(compose, "AUTOMATIONS")
        compose.onNodeWithText("Workers").performClick()
        secondary("worker")
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithText("New responsibility").performScrollTo().performClick()
        secondary("create")
        navigateReview(compose, "OSCAR")
        compose.onNodeWithText("Voice").performClick()
        secondary("voice")
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithTag("primary-navigation").assertExists()
        compose.onNodeWithTag("page-back").assertDoesNotExist()
        compose.onNodeWithTag("interactionInput").assertIsDisplayed()
    }
}
