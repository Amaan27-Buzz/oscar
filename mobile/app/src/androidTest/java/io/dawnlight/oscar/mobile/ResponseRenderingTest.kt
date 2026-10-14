package io.dawnlight.oscar.mobile

import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import org.junit.Rule
import org.junit.Test

class ResponseRenderingTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun nativeMarkdownAndStructuredResponsesAreReadable() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        compose.runOnIdle { compose.activity.setContent {
            OscarTheme {
                Surface {
                    Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(24.dp)) {
                        SelectionContainer { ResponseText("# A little room to focus\n\n**One outcome** with *care*.\n\n- Prepare the proposal\n- Leave a return point\n\n> Keep the next step concrete.\n\n```kotlin\nval count = 2\n```\n\n[Source](https://example.com)\n\n| Day | Work |\n| --- | --- |\n| Monday | Read |") }
                        ResponseText("{\"status\":\"reported\",\"items\":[\"One\",\"Two\"]}")
                    }
                }
            }
        } }
        compose.onNodeWithText("A little room to focus", substring = true).assertIsDisplayed()
        compose.onNodeWithText("• Prepare the proposal", substring = true).assertExists()
        compose.onNodeWithText("val count = 2", substring = true).assertExists()
        compose.onNodeWithText("Day   ·   Work", substring = true).assertExists()
        compose.onNodeWithText("status: reported", substring = true).performScrollTo().assertIsDisplayed()
        compose.onNodeWithText("# A little room to focus", substring = true).assertDoesNotExist()
        captureReview(compose, "richtext-native-reference")
    }
}
