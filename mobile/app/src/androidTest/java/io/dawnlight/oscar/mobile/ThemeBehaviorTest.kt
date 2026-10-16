package io.dawnlight.oscar.mobile

import android.content.Context
import android.view.WindowInsetsController
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class ThemeBehaviorTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private var isolated = false
    @Before fun isolate() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        isolated = true
        compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
    }
    @After fun cleanup() {
        if (isolated) compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().clear().commit()
    }
    private fun assertTheme(dark: Boolean) {
        compose.waitForIdle()
        compose.runOnIdle {
            val flags = compose.activity.window.insetsController!!.systemBarsAppearance
            assertEquals("Status bar must match the selected page theme", !dark,
                flags and WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS != 0)
            assertEquals("Navigation bar must match the selected page theme", !dark,
                flags and WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS != 0)
        }
    }
    @Test fun explicitThemesReachImmersiveRoutesAndSurviveRecreation() {
        for (theme in listOf("light", "dark")) {
            navigateReview(compose, "SETTINGS")
            compose.onNodeWithText("Appearance").performScrollTo().performClick()
            compose.onNodeWithTag("theme-$theme").performClick().assertIsSelected()
            assertTheme(theme == "dark")
            compose.activityRule.scenario.recreate()
            compose.onNodeWithTag("theme-$theme").assertIsSelected()
            assertTheme(theme == "dark")
            navigateReview(compose, "ACTIVITY")
            assertTheme(theme == "dark")
            captureReview(compose, "closure-$theme-activity")
            compose.activityRule.scenario.recreate()
            assertTheme(theme == "dark")
            navigateReview(compose, "OSCAR")
            compose.onNodeWithText("Voice").performClick()
            assertTheme(theme == "dark")
            captureReview(compose, "closure-$theme-voice")
            navigateReview(compose, "SETTINGS")
            compose.onNodeWithText("Awareness").performScrollTo().performClick()
            assertTheme(theme == "dark")
            captureReview(compose, "closure-$theme-awareness")
        }
    }
    @Test fun systemRetainsApprovedImmersiveCompositionsAndPersists() {
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText("Appearance").performScrollTo().performClick()
        compose.onNodeWithTag("theme-system").performClick().assertIsSelected()
        compose.activityRule.scenario.recreate()
        compose.onNodeWithTag("theme-system").assertIsSelected()
        val systemDark = compose.activity.resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK == android.content.res.Configuration.UI_MODE_NIGHT_YES
        assertTheme(systemDark)
        navigateReview(compose, "ACTIVITY")
        assertTheme(true)
        navigateReview(compose, "OSCAR")
        assertTheme(systemDark)
        compose.onNodeWithText("Voice").performClick()
        assertTheme(true)
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText("Awareness").performScrollTo().performClick()
        assertTheme(true)
    }
    @Test fun systemFollowsBothConfigurationsWithDocumentedImmersiveException() {
        compose.runOnIdle { compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("theme", "system").commit() }
        val configuration = mutableStateOf(android.content.res.Configuration(compose.activity.resources.configuration))
        val immersive = mutableStateOf(false)
        compose.runOnIdle { compose.activity.setContent {
            CompositionLocalProvider(LocalConfiguration provides configuration.value) {
                OscarTheme(preferDark = immersive.value) {
                    Text("Dark palette: ${MaterialTheme.colorScheme.background.luminance() < 0.5f}")
                }
            }
        } }
        for (night in listOf(false, true)) for (preferred in listOf(false, true)) {
            compose.runOnIdle {
                configuration.value = android.content.res.Configuration(configuration.value).apply {
                    uiMode = (uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK.inv()) or
                        if (night) android.content.res.Configuration.UI_MODE_NIGHT_YES else android.content.res.Configuration.UI_MODE_NIGHT_NO
                }
                immersive.value = preferred
            }
            compose.onNodeWithText("Dark palette: ${night || preferred}").assertExists()
        }
    }
}
