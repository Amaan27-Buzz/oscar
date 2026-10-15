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
}
