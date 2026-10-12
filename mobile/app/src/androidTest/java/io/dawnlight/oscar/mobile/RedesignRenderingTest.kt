package io.dawnlight.oscar.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.platform.app.InstrumentationRegistry
import androidx.lifecycle.ViewModelProvider
import org.junit.*
import org.junit.Assert.*

/** Actual native emulator pixels over disposable Core; never owner/device acceptance. */
class RedesignRenderingTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val session get() = ViewModelProvider(compose.activity)[CoreSession::class.java]
    private val folder = InstrumentationRegistry.getArguments().getString("redesign_capture", "OSCAR-Rebuild-${System.currentTimeMillis()}")!!
    private var isolated = false
    @Before fun isolate() {
        Assume.assumeTrue(android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        isolated = true
        compose.runOnIdle { session.disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
    }
    @After fun clearFixture() { if (isolated) compose.runOnIdle { VoicePresentation.cancel(compose.activity); session.disconnect() } }
    private fun shot(name: String) {
        compose.waitForIdle()
        compose.runOnIdle { compose.activity.window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) }
        try {
            Thread.sleep(400) // Wait for the native compositor to commit the test-only secure-flag change.
            val bitmap = InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot()!!
            assertTrue(bitmap.width > 0 && bitmap.height > 0)
            val resolver = compose.activity.contentResolver
            val uri = resolver.insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, android.content.ContentValues().apply {
                put(android.provider.MediaStore.Images.Media.DISPLAY_NAME, "$name.png")
                put(android.provider.MediaStore.Images.Media.MIME_TYPE, "image/png")
                put(android.provider.MediaStore.Images.Media.RELATIVE_PATH, "Pictures/$folder")
            })!!
            resolver.openOutputStream(uri)!!.use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
            bitmap.recycle()
        } finally { compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) } }
    }
    @Test fun nativePrimaryScreenMatrixAndOrbCancel() {
        shot("unavailable")
        val args = InstrumentationRegistry.getArguments()
        val origin = args.getString("group02_origin")
        Assume.assumeTrue("Disposable loopback reference only", origin != null)
        require(origin!!.startsWith("http://127.0.0.1:"))
        val fixture = org.json.JSONObject().put("url", origin).put("node_id", "reference-mobile-software")
            .put("session_id", args.getString("group02_session")).put("token", args.getString("group02_token"))
        compose.runOnIdle { session.connect(fixture) }
        compose.waitUntil(10000) { session.state.value.link == Link.CONNECTED }
        shot("home-reference")
        compose.onNodeWithTag("interactionInput").performClick().performTextInput("A private reference draft")
        compose.waitUntil(10000) { compose.activity.window.decorView.rootWindowInsets.isVisible(android.view.WindowInsets.Type.ime()) }
        shot("text-ime-reference")
        compose.onNodeWithContentDescription("Open voice interaction").performClick()
        compose.onNodeWithTag("voiceStatus").assertTextContains("Microphone off")
        shot("voice-reference")
        compose.onNodeWithContentDescription("Close voice interaction").performClick()
        assertEquals(VoicePhase.IDLE, VoicePresentation.state.value.phase)
        compose.onNodeWithTag("interactionInput").assertTextContains("A private reference draft")
        compose.openDestination("Activity"); shot("activity-reference")
        compose.openDestination("Devices"); shot("devices-reference")
        compose.openDestination("Settings"); shot("settings-reference")
        compose.onNodeWithText("Privacy").performClick(); shot("privacy-reference")
        compose.openDestination("OSCAR")
        compose.onNodeWithTag("interactionInput").assertTextContains("A private reference draft")
        compose.onNodeWithTag("navigation").performClick()
        InstrumentationRegistry.getInstrumentation().uiAutomation.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_BACK)
        compose.waitForIdle()
        compose.onNodeWithTag("interactionInput").assertTextContains("A private reference draft")
        assertNull(MicrophoneService.binding)
    }
}
