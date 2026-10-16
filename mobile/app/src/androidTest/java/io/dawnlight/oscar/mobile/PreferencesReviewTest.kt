package io.dawnlight.oscar.mobile

import android.content.Context
import androidx.activity.compose.setContent
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import androidx.lifecycle.ViewModelProvider
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class PreferencesReviewTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private var isolated = false
    @After fun cleanup() {
        if (isolated) compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().clear().commit()
    }

    @Test fun themePersistsAndEveryPageSupportsLargeText() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        isolated = true
        val session = ViewModelProvider(compose.activity)[CoreSession::class.java]
        compose.waitUntil(5000) { !session.state.value.restoring }
        compose.runOnIdle {
            compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            session.disconnect()
            compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("theme", "light").putString("motion", "reduced").commit()
        }
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText("Appearance").performScrollTo().performClick()
        val themeRows = listOf("system", "light", "dark").map { compose.onNodeWithTag("theme-$it").fetchSemanticsNode().boundsInRoot.top }
        assertEquals("Theme previews must share one row at normal text size", 1, themeRows.distinct().size)
        for (theme in listOf("dark", "system", "light")) {
            compose.onNodeWithTag("theme-$theme").performClick().assertIsSelected()
            compose.runOnIdle { assertEquals(theme, compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).getString("theme", "")) }
        }
        compose.activityRule.scenario.recreate()
        compose.onNodeWithTag("theme-light").assertIsSelected()
        compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("theme", "dark").commit()
        compose.runOnIdle {
            compose.activity.setContent {
                CompositionLocalProvider(LocalDensity provides Density(LocalDensity.current.density, 1.8f)) {
                    OscarApp(ViewModelProvider(compose.activity)[CoreSession::class.java], OwnerConfirmation(compose.activity))
                }
            }
        }
        for ((label, name) in listOf("Persona" to "persona", "Voice" to "voice-settings", "Privacy" to "privacy",
            "Awareness" to "awareness", "Memory" to "memory", "Access" to "access", "Android permissions" to "android",
            "Notifications" to "notifications", "Appearance" to "appearance", "Diagnostics" to "diagnostics", "About" to "about")) {
            navigateReview(compose, "SETTINGS")
            if (label == "Persona") captureReview(compose, "prefs-large-preferences")
            compose.onNodeWithText(label).performScrollTo().performClick()
            compose.onAllNodesWithTag("app-toolbar").assertCountEquals(1)
            compose.onAllNodesWithTag("page-back").assertCountEquals(1)
            compose.onNodeWithTag("primary-navigation").assertDoesNotExist()
            captureReview(compose, "prefs-large-$name")
            when (label) {
                "Appearance" -> {
                    compose.onNodeWithContentDescription("Reduce OSCAR motion").performScrollTo().assertIsDisplayed().assertIsOn()
                    captureReview(compose, "prefs-large-comfort")
                }
                "Privacy" -> {
                    compose.onNodeWithText("Revoke OSCAR grants").performScrollTo().assertIsDisplayed()
                    captureReview(compose, "prefs-large-actions")
                }
            }
        }
    }
}
