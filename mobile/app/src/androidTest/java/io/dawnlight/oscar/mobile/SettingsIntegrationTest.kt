package io.dawnlight.oscar.mobile
import android.content.Context
import androidx.activity.compose.setContent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.*
import org.junit.After
import org.junit.Before
import androidx.compose.ui.graphics.asAndroidBitmap
class SettingsIntegrationTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private var isolated = false
    @Before fun isolate() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        isolated = true
        val session = androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java]
        compose.waitUntil(5000) { !session.state.value.restoring }
        compose.runOnIdle { androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java].disconnect() }
        compose.waitUntil(5000) { session.state.value.message == "Local credentials removed. Revoke this node from Core separately." }
    }
    @After fun cleanup() { if (!isolated) return; compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().clear().commit() }
    private fun page(name: String) {
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText(name).performScrollTo().performClick()
    }
    private fun capture(name: String) = captureReview(compose, name)
    @Test fun androidDisabledAnimationsPropagateToSharedTheme() {
        org.junit.Assume.assumeTrue(android.provider.Settings.Global.getFloat(compose.activity.contentResolver, "animator_duration_scale", 1f) == 0f)
        compose.activity.getSharedPreferences("appearance",Context.MODE_PRIVATE).edit().clear().commit()
        compose.runOnIdle { compose.activity.setContent { OscarTheme { androidx.compose.material3.Text("System reduced motion: ${LocalReducedMotion.current}") } } }
        compose.onNodeWithText("System reduced motion: true").assertExists()
    }
    @Test fun clearProcessDeathFixture() {
        org.junit.Assume.assumeTrue(androidx.test.platform.app.InstrumentationRegistry.getArguments().getString("group02_process_prepare") == "true")
        compose.runOnIdle { androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java].disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).loadDraft("unpaired").isEmpty() }
    }
    @Test fun prepareProcessDeathRecovery() {
        org.junit.Assume.assumeTrue(androidx.test.platform.app.InstrumentationRegistry.getArguments().getString("group02_process_prepare") == "true")
        navigateReview(compose, "OSCAR")
        compose.onNodeWithTag("interactionInput").performTextClearance()
        compose.onNodeWithTag("interactionInput").performTextReplacement("Group02 synthetic process recovery")
        compose.waitUntil(5000) { SessionVault(compose.activity).loadDraft("unpaired") == "Group02 synthetic process recovery" }
    }
    @Test fun personaIsBoundedAndDoesNotChangeCorePolicy() {
        page("Persona")
        compose.onNodeWithText("Preview only · not applied to OSCAR").assertExists()
        compose.onNodeWithText("Amused").performScrollTo().performClick()
        compose.onAllNodesWithContentDescription("OSCAR expression").assertCountEquals(1)
        assertFalse(compose.activity.getSharedPreferences("appearance",Context.MODE_PRIVATE).contains("persona"))
        capture("13-7-persona-preview-simulated")
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithText("Android permissions").performScrollTo().performClick()
        compose.onNodeWithText("Other Android features").performScrollTo().performClick()
        val overlayGranted = android.provider.Settings.canDrawOverlays(compose.activity)
        compose.onNodeWithText(if (overlayGranted) "Overlay permission granted" else "Overlay permission not granted").assertExists()
        val show = compose.onNodeWithText("Show Companion Orb").performScrollTo()
        if (CompanionOverlay.permitted(compose.activity)) show.assertIsEnabled() else show.assertIsNotEnabled()
        compose.onNodeWithText("Requires separately authorized Core presence.", substring = true).assertExists()
        compose.onNodeWithText("Disable Companion overlay").performScrollTo().performClick()
        assertFalse(CompanionOverlay.enabled(compose.activity))
        assertNull(SessionVault(compose.activity).load())
        capture("13-7-platform-reference")
    }
    @Test fun darkLargeTextAndImeRemainUsable() {
        compose.activity.getSharedPreferences("appearance",Context.MODE_PRIVATE).edit().putString("theme","dark").putString("motion","reduced").commit()
        compose.runOnIdle {
            compose.activity.setContent {
                androidx.compose.runtime.CompositionLocalProvider(androidx.compose.ui.platform.LocalDensity provides androidx.compose.ui.unit.Density(androidx.compose.ui.platform.LocalDensity.current.density, 1.8f)) {
                    OscarApp(androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java], OwnerConfirmation(compose.activity))
                }
            }
        }
        navigateReview(compose, "SETTINGS")
        compose.onNodeWithText("Diagnostics").performScrollTo().performClick()
        compose.onNodeWithText("Runtime information").performScrollTo().performClick()
        compose.onNodeWithText("No tokens, private prompts",substring=true).performScrollTo().assertIsDisplayed()
        capture("13-8-dark-large-text-reference")
        navigateReview(compose, "OSCAR")
        capture("13-8-large-text-navigation-reference")
        for (label in listOf("Conversation", "Automations", "Activity")) {
            val layouts = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
            compose.onNodeWithText(label, useUnmergedTree = true).performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult) { it(layouts) }
            val layout = layouts.single()
            assertEquals("Navigation label must stay on one line", 1, layout.lineCount)
            assertFalse("$label must remain complete at 1.8x text: ${layout.layoutInput.constraints}", layout.isLineEllipsized(0))
            assertEquals("Every navigation character must be visible", label.length, layout.getLineEnd(0))
            assertTrue("$label glyphs must fit the pixel bounds", layout.getBoundingBox(label.lastIndex).right <= layout.size.width + 1f)
        }
        compose.onNodeWithTag("interactionInput").performClick()
        compose.waitUntil(10000) { compose.activity.window.decorView.rootWindowInsets.isVisible(android.view.WindowInsets.Type.ime()) }
        compose.onNodeWithTag("interactionInput").performTextReplacement("Large text draft")
        compose.waitUntil(5000) {
            val bottom = compose.onNodeWithTag("interactionInput").fetchSemanticsNode().boundsInWindow.bottom
            val top = compose.activity.window.decorView.height - compose.activity.window.decorView.rootWindowInsets.getInsets(android.view.WindowInsets.Type.ime()).bottom
            bottom <= top
        }
        val fieldBottom = compose.onNodeWithTag("interactionInput").fetchSemanticsNode().boundsInWindow.bottom
        val imeTop = compose.activity.window.decorView.height - compose.activity.window.decorView.rootWindowInsets.getInsets(android.view.WindowInsets.Type.ime()).bottom
        assertTrue("Input must remain above actual keyboard", fieldBottom <= imeTop)
        compose.onNodeWithTag("interactionInput").assertTextContains("Large text draft")
        capture("13-8-ime-large-text-reference")
        compose.onNodeWithText("Voice").performClick()
        compose.onNodeWithText("Start listening").performScrollTo().performClick()
        compose.waitUntil(5000) { VoicePresentation.state.value.phase == VoicePhase.MUTED }
        compose.onNodeWithTag("page-back").assertIsDisplayed()
        capture("13-8-voice-large-text-reference")
        compose.onNodeWithTag("page-back").performClick()
        compose.onNodeWithTag("interactionInput").assertTextContains("Large text draft")
    }
    @Test fun landscapeKeepsComposerAndPreferencesReachable() {
        val original = compose.activity.requestedOrientation
        try {
            compose.runOnIdle { compose.activity.requestedOrientation = android.content.pm.ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE }
            compose.waitUntil(5000) { compose.activity.resources.configuration.orientation == android.content.res.Configuration.ORIENTATION_LANDSCAPE }
            compose.onNodeWithTag("interactionInput").assertIsDisplayed()
            compose.onNodeWithText("Send").assertIsDisplayed()
            page("Memory")
            compose.onNodeWithText("History & recall").performScrollTo().assertIsDisplayed()
            capture("13-8-landscape-reference")
        } finally {
            compose.runOnIdle { compose.activity.requestedOrientation = original }
        }
    }
    @Test fun reducedMotionPersistsThroughActivityRecreation() {
        page("Appearance")
        compose.onNodeWithContentDescription("Reduce OSCAR motion").performScrollTo().performClick()
        compose.waitUntil(5000) { compose.activity.getSharedPreferences("appearance",Context.MODE_PRIVATE).getString("motion","") == "reduced" }
        compose.activityRule.scenario.recreate()
        compose.onNodeWithContentDescription("Reduce OSCAR motion").assertIsOn()
        capture("13-7-accessibility-reference")
    }
}
