package io.dawnlight.oscar.mobile

import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.luminance
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class CraftControlsTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @Test fun designedControlsRetainNativeEditingAndDisabledButtonSemantics() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        var draft by mutableStateOf("")
        var enabled by mutableStateOf(false)
        var submitted = 0
        compose.runOnIdle {
            compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            compose.activity.setContent {
                OscarTheme {
                    Column(Modifier.fillMaxSize().safeDrawingPadding().padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                        OscarField(draft, { draft = it }, "Pairing token", Modifier.testTag("craft-token"),
                            singleLine = true, visualTransformation = PasswordVisualTransformation())
                        OscarButton({ submitted++ }, Modifier.testTag("craft-submit"), enabled) { Text("Connect securely") }
                        StatusPill("Connecting", Amber)
                    }
                }
            }
        }
        compose.onNodeWithTag("craft-token").performTextInput("synthetic-token")
        compose.onNodeWithTag("craft-token").assertIsFocused().assert(SemanticsMatcher.keyIsDefined(SemanticsProperties.Password))
        compose.runOnIdle { assertEquals("synthetic-token", draft) }
        compose.onNodeWithTag("craft-submit").assertIsNotEnabled()
            .assert(SemanticsMatcher.expectValue(SemanticsProperties.Role, Role.Button)).performTouchInput { click() }
        compose.runOnIdle { assertEquals(0, submitted); enabled = true }
        androidx.test.espresso.Espresso.closeSoftKeyboard()
        compose.onNodeWithTag("craft-submit").assertIsEnabled().performClick()
        compose.runOnIdle { assertEquals(1, submitted) }
        captureReview(compose, "craft-controls")
    }

    @Test fun artworkUsesScreenEdgesScrollsWithContentAndKeepsDarkHeadingsReadable() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        compose.runOnIdle {
            compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            compose.activity.getSharedPreferences("appearance", android.content.Context.MODE_PRIVATE).edit()
                .putString("theme", "light").putString("motion", "reduced").commit()
        }
        navigateReview(compose, "DEVICES")
        val art = compose.onNodeWithTag("edge-illustration").getUnclippedBoundsInRoot()
        val root = compose.onRoot().getUnclippedBoundsInRoot()
        val toolbar = compose.onNodeWithTag("app-toolbar").getUnclippedBoundsInRoot()
        assertTrue("Artwork bleeds beyond the screen edge", art.right > root.right)
        assertTrue("Artwork extends behind the app bar", art.top < toolbar.top)
        captureReview(compose, "canvas-edge-devices")
        navigateReview(compose, "SETTINGS")
        val initialTop = compose.onNodeWithTag("edge-illustration").getUnclippedBoundsInRoot().top
        compose.onNodeWithText("About").performScrollTo().assertIsDisplayed()
        assertTrue("Artwork leaves with its content rather than floating behind settings",
            compose.onNodeWithTag("edge-illustration").getUnclippedBoundsInRoot().top < initialTop)
        compose.onNodeWithText("Awareness").performScrollTo().performClick()
        val layouts = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
        compose.onNodeWithText("Awareness is off").performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult) { it(layouts) }
        assertTrue("Explicit Light keeps dark heading ink", layouts.single().layoutInput.style.color.luminance() < 0.5f)
        compose.runOnIdle { compose.activity.getSharedPreferences("appearance", android.content.Context.MODE_PRIVATE).edit().putString("theme", "dark").commit() }
        layouts.clear()
        compose.onNodeWithText("Awareness is off").performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult) { it(layouts) }
        assertTrue("Dark canvas keeps light heading ink", layouts.single().layoutInput.style.color.luminance() > 0.5f)
        compose.onAllNodesWithTag("app-toolbar").assertCountEquals(1)
        compose.onNodeWithTag("primary-navigation").assertDoesNotExist()
        captureReview(compose, "canvas-edge-awareness")
    }
}
