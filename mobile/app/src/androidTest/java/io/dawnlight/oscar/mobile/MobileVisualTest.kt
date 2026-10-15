package io.dawnlight.oscar.mobile

import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import java.io.File

/** Native visual evidence uses disposable fixtures, never owner data or synthetic authority. */
class MobileVisualTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Before fun isolatedEmulator() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        compose.runOnIdle { androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java].disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
        compose.runOnIdle { compose.activity.getSharedPreferences("appearance", android.content.Context.MODE_PRIVATE).edit().putString("theme", "light").putString("motion", "reduced").commit() }
    }
    private fun capture(name: String, tag: String? = null) = captureReview(compose, name, tag)
    private fun surface(dark: Boolean = false, content: @Composable () -> Unit) {
        compose.runOnIdle { compose.activity.setContent {
            OscarTheme(forceDark = dark) {
                androidx.compose.material3.Surface {
                    Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text("NATIVE REVIEW · disposable reference")
                        content()
                    }
                }
            }
        } }
    }
    @Test fun productionNavigationAndUnavailableControls() {
        capture("01-oscar-home")
        compose.onNodeWithTag("destination-AUTOMATIONS").performClick()
        compose.onNodeWithText("Persistent scheduling is unavailable").assertExists()
        capture("05-automations-overview")
        compose.onNodeWithText("Workers").performClick()
        compose.onNodeWithText("Run Worker · unavailable").assertIsNotEnabled()
        capture("06-worker-detail")
        compose.onNodeWithTag("automation-back").performClick()
        compose.onNodeWithText("New responsibility").performScrollTo().performClick()
        compose.onNodeWithTag("automationDraft").performTextInput("Prepare a brief")
        androidx.test.espresso.Espresso.closeSoftKeyboard()
        compose.waitUntil(5000) { !compose.activity.window.decorView.rootWindowInsets.isVisible(android.view.WindowInsets.Type.ime()) }
        compose.onNodeWithText("Create automation · unavailable").assertIsNotEnabled()
        capture("07-create-automation")
        compose.onNodeWithTag("destination-OSCAR").performClick()
        compose.onNodeWithText("Today").performScrollTo().performClick()
        compose.onNodeWithText("Not connected · no commitments retrieved").assertExists()
        capture("13-today-chief-of-staff")
        compose.onNodeWithTag("destination-DEVICES").performClick()
        compose.onNodeWithText("Connect Core to see your other devices.").assertExists()
        capture("11-devices")
        compose.onNodeWithTag("destination-SETTINGS").performClick()
        compose.onNodeWithText("Make OSCAR").assertIsDisplayed()
        capture("15-preferences")
        compose.onNodeWithText("Access").performScrollTo().performClick()
        compose.onNodeWithTag("delegationUnavailable").assertIsNotEnabled()
        capture("14-access-modes")
        compose.onNodeWithText("Back to Preferences").performScrollTo().performClick()
        compose.onNodeWithText("Awareness").performScrollTo().performClick()
        compose.onNodeWithText("Sentry").assertIsNotEnabled()
        capture("12-sentry-awareness")
        compose.onNodeWithTag("destination-ACTIVITY").performClick()
        capture("08-activity-feed")
        compose.onNodeWithTag("destination-OSCAR").performClick()
        compose.onNodeWithText("Voice").performClick()
        compose.onNodeWithTag("voiceStatus").assertTextContains("Microphone off")
        capture("04-voice-interaction")
        assertNull(MicrophoneService.binding)
    }
    @Test fun chronologicalConversationReadingAndTaskControls() {
        val task = CoreTask("visual-reference", "Review the proposal", "verifying", "Reference desktop", "online", 1,
            listOf("cancel"), emptyList(), null, null, "A quieter way to focus.\n\nOne outcome\nPrepare the proposal.\n\nA return point\nLeave the next step concrete.")
        val state = MobileState(link = Link.CONNECTED, snapshot = CoreSnapshot(listOf(task), emptyList(), System.currentTimeMillis()),
            interactions = listOf(Interaction("Help me plan.", "Core acknowledged."), Interaction("Review the proposal", "Reported", task.id)))
        surface {
            OscarOrb(state, size = 36.dp, reduced = true)
            PresenceScreen(state, "", {}, {}, {}, {}, {})
        }
        compose.onNodeWithText("Help me plan.").assertExists()
        compose.onNodeWithText("Core acknowledged.").assertExists()
        compose.onAllNodesWithText("Review the proposal", substring = true).assertCountEquals(2)
        capture("02-continuous-conversation")
        compose.onAllNodesWithText("Read response")[1].performScrollTo().performClick()
        compose.onNode(hasText(task.response!!) and hasAnyAncestor(hasTestTag("responseDialog"))).assertExists()
        capture("03-expanded-reading", "responseDialog")
        compose.onNodeWithText("Back").performScrollTo().performClick()
        surface { TaskInspector(task, {}) }
        compose.onNodeWithText("Review cancellation").assertDoesNotExist()
        capture("09-active-task", "taskInspector")
    }
    @Test fun expiredDecisionCannotGrantConsent() {
        val approval = Approval("reference-decision", "", 1, "approve", "Synthetic proposal review", "Reference desktop", "reference",
            "Review requested", "Write one proposed document", "Ask requires consent", "{}", "Write the reviewed document", "reference", "reference", "reference", 1)
        var confirmed = false
        surface { ApprovalDialog(approval, false, false, {}, { confirmed = true }) }
        compose.onNodeWithText("Confirm securely").assertIsNotEnabled()
        capture("10-approval-decision", "approvalDialog")
        assertFalse(confirmed)
    }
}
