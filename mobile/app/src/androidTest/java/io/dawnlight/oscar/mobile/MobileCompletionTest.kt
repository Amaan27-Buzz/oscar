package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import androidx.activity.compose.setContent
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import java.io.File

/** Disposable native Compose/reference evidence. No owner data or permission commissioning. */
class MobileCompletionTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun capture(name: String) {
        compose.runOnIdle {
            assertTrue(compose.activity.window.attributes.flags and android.view.WindowManager.LayoutParams.FLAG_SECURE != 0)
            // Only disposable instrumentation content may be captured; production keeps FLAG_SECURE.
            compose.activity.window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE)
        }
        val bitmap = compose.onRoot().captureToImage().asAndroidBitmap()
        val resolver = compose.activity.contentResolver
        val uri = resolver.insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, android.content.ContentValues().apply {
            put(android.provider.MediaStore.Images.Media.DISPLAY_NAME, "$name.png")
            put(android.provider.MediaStore.Images.Media.MIME_TYPE, "image/png")
            put(android.provider.MediaStore.Images.Media.RELATIVE_PATH, "Pictures/OSCAR-Group02")
        })!!
        resolver.openOutputStream(uri)!!.use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
        compose.runOnIdle {
            compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE)
        }
    }
    @Test fun homeUnavailableAndSharedExpressionRender() {
        compose.onNodeWithTag("orb").assertExists()
        compose.onNodeWithText("OSCAR is not connected").assertExists()
        compose.onNodeWithText("Send").assertIsNotEnabled()
        capture("13-1-home-unavailable")
    }
    @Test fun verifyingIsDistinctAndDoesNotInventSpeech() {
        val task = CoreTask("fixture", "Check the reference outcome", "verifying", "reference-desktop", "online", 1, emptyList(), emptyList(), null, null)
        val state = MobileState(link = Link.CONNECTED, observedAt = System.currentTimeMillis(), snapshot = CoreSnapshot(listOf(task), emptyList(), System.currentTimeMillis()))
        compose.activity.runOnUiThread {
            compose.activity.setContentForTest {
                OscarTheme {
                    Column(Modifier.fillMaxSize().padding(24.dp)) {
                        OscarOrb(state, reduced = true)
                        PresenceScreen(state, "", {}, {}, {}, {}, {})
                    }
                }
            }
        }
        compose.onNodeWithText("Checking the outcome").assertIsDisplayed()
        compose.onNodeWithTag("orb").assert(SemanticsMatcher("Verifying semantics") {
            it.config[androidx.compose.ui.semantics.SemanticsProperties.StateDescription].contains("verifying", ignoreCase = true)
        })
        capture("13-1-verifying-simulated")
    }
}

private fun MainActivity.setContentForTest(content: @Composable () -> Unit) = setContent(content = content)
