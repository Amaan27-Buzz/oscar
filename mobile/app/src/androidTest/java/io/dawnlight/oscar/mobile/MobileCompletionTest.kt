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
import org.junit.Before
import org.junit.After
import java.io.File

/** Disposable native Compose/reference evidence. No owner data or permission commissioning. */
class MobileCompletionTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private var isolated = false
    @Before fun isolateLocalFixture() {
        org.junit.Assume.assumeTrue(android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        isolated = true
        compose.runOnIdle { androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java].disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
    }
    @After fun removeLocalFixture() {
        if (!isolated) return
        compose.runOnIdle { androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java].disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
    }
    private fun control(operation: String, task: String = "") {
        val arguments = androidx.test.platform.app.InstrumentationRegistry.getArguments()
        val connection = java.net.URI(arguments.getString("group02_control")!!).toURL().openConnection() as java.net.HttpURLConnection
        try {
            connection.requestMethod = "POST"; connection.doOutput = true; connection.connectTimeout = 5000; connection.readTimeout = 8000
            connection.setRequestProperty("X-Reference-Token", arguments.getString("group02_control_token"))
            val data = org.json.JSONObject().put("operation", operation).put("task_id", task).toString().toByteArray()
            connection.setFixedLengthStreamingMode(data.size); connection.outputStream.use { it.write(data) }
            assertEquals(200, connection.responseCode)
            connection.inputStream.close()
        } finally { connection.disconnect() }
    }
    private fun capture(name: String, tag: String? = null) {
        compose.runOnIdle {
            assertTrue(compose.activity.window.attributes.flags and android.view.WindowManager.LayoutParams.FLAG_SECURE != 0)
            // Only disposable instrumentation content may be captured; production keeps FLAG_SECURE.
            compose.activity.window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE)
        }
        val bitmap = (if (tag == null) compose.onRoot() else compose.onNodeWithTag(tag)).captureToImage().asAndroidBitmap()
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
    @Test fun voiceInvocationCancellationPreservesTextWithoutCapture() {
        compose.onNodeWithTag("interactionInput").performTextInput("Synthetic voice continuation")
        compose.onNodeWithText("Voice").performClick()
        compose.onNodeWithTag("voiceStatus").assertTextContains("Microphone off")
        assertEquals(null, MicrophoneService.binding)
        compose.onNodeWithText("Start listening").performClick()
        compose.waitUntil(5000) { VoicePresentation.state.value.phase == VoicePhase.MUTED }
        compose.waitUntil(5000) { compose.onAllNodesWithText("Microphone permission or OSCAR perception grant is off").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithTag("voiceStatus").assertTextEquals("Microphone permission or OSCAR perception grant is off")
        capture("13-5-voice-denied-reference")
        compose.onNodeWithText("Cancel voice").performClick()
        compose.onNodeWithTag("interactionInput").assertTextContains("Synthetic voice continuation")
        assertEquals(VoicePhase.IDLE, VoicePresentation.state.value.phase)
    }
    @Test fun homeUnavailableAndSharedExpressionRender() {
        compose.onNodeWithTag("orb").assertExists()
        compose.onNodeWithText("Let’s reconnect.").assertExists()
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
    @Test fun draftRecreationAndEncryptedRecoveryKeepPrivateDataOutOfBundles() {
        val text = "Synthetic unsent draft"
        compose.onNodeWithTag("interactionInput").performTextInput(text)
        compose.waitUntil(5000) { compose.activity.getSharedPreferences("session", android.content.Context.MODE_PRIVATE).contains("draft") }
        val vault = SessionVault(compose.activity)
        assertEquals(text, vault.loadDraft("unpaired"))
        assertFalse(compose.activity.getSharedPreferences("session", android.content.Context.MODE_PRIVATE).getString("draft", "")!!.contains(text))
        compose.activityRule.scenario.recreate()
        compose.waitUntil(5000) { androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java].state.value.draft == text }
        compose.onNodeWithTag("interactionInput").assertTextContains(text)
        compose.openDestination("Activity")
        compose.openDestination("OSCAR")
        compose.onNodeWithTag("interactionInput").assertTextContains(text)
        compose.onNodeWithText("Discard private interaction").performScrollTo().performClick()
        compose.waitUntil(5000) { !compose.activity.getSharedPreferences("session", android.content.Context.MODE_PRIVATE).contains("draft") }
        compose.onNodeWithTag("interactionInput").assertTextContains("Write to OSCAR")
        assertTrue(vault.suppressed("unpaired"))
        val restored = CoreSession(compose.activity.application)
        compose.runOnIdle { restored.start() }
        compose.waitUntil(5000) { restored.state.value.privateSuppressed }
        assertTrue(restored.state.value.draft.isEmpty())
        compose.runOnIdle { restored.disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
        vault.forget()
    }
    @Test fun replacementPairingAndDisconnectCannotRestoreOldSecrets() {
        val session = androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java]
        fun fixture(id: String) = org.json.JSONObject().put("url", "http://127.0.0.1:9").put("node_id", "reference-node")
            .put("session_id", id).put("token", "synthetic-reference-token-only")
        compose.runOnIdle { session.connect(fixture("first")); session.connect(fixture("replacement")) }
        compose.waitUntil(5000) { try { SessionVault(compose.activity).load()?.getString("session_id") == "replacement" } catch (_: Exception) { false } }
        val binding = CoreClient(fixture("replacement")).binding()
        SessionVault(compose.activity).saveDraft("private source draft", binding)
        try { SessionVault(compose.activity).loadDraft("foreign-source"); fail("Cross-source recovery accepted") } catch (_: javax.crypto.AEADBadTagException) { }
        compose.runOnIdle { session.disconnect(); session.connect(fixture("last-source")) }
        compose.waitUntil(5000) { try { SessionVault(compose.activity).load()?.getString("session_id") == "last-source" } catch (_: Exception) { false } }
        assertEquals("", SessionVault(compose.activity).loadDraft(CoreClient(fixture("last-source")).binding()))
        assertTrue(session.state.value.interactions.isEmpty())
        compose.waitUntil(5000) { !session.state.value.busy }
        compose.runOnIdle { session.connect(fixture("saved-while-stopped")); session.stop() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load()?.getString("session_id") == "saved-while-stopped" }
        compose.runOnIdle { session.start() }
        compose.waitUntil(5000) { session.sourceBinding() == CoreClient(fixture("saved-while-stopped")).binding() }
        compose.runOnIdle { session.disconnect() }
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
    }
    @Test fun nativeReferenceHomeTextTaskAndPrivacyDiscardReadBack() {
        val arguments = androidx.test.platform.app.InstrumentationRegistry.getArguments()
        val origin = arguments.getString("group02_origin")
        org.junit.Assume.assumeTrue("Explicit isolated Core fixture only", origin != null)
        require(origin!!.startsWith("http://127.0.0.1:"))
        val fixture = org.json.JSONObject().put("url", origin).put("node_id", "reference-mobile-software")
            .put("session_id", arguments.getString("group02_session")).put("token", arguments.getString("group02_token"))
        val session = androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java]
        compose.runOnIdle { session.connect(fixture) }
        compose.waitUntil(10_000) { session.state.value.link == Link.CONNECTED }
        assertTrue(session.state.value.snapshot!!.tasks.any { it.state == "verified" && it.value == "5" })
        compose.onNodeWithTag("interactionInput").performTextInput("3 + 4")
        compose.onNodeWithText("Send").performClick()
        compose.waitUntil(10_000) { session.state.value.interactions.lastOrNull()?.text == "3 + 4" && !session.state.value.busy }
        compose.onNodeWithText("Read response").performScrollTo().performClick()
        compose.onNode(hasText("Needs approval") and hasAnyAncestor(hasTestTag("responseDialog"))).assertExists()
        compose.onNodeWithText("Back").performClick()
        capture("13-2-reference-home-response")
        compose.openDestination("Activity")
        compose.onNodeWithTag("task-description-${session.state.value.interactions.last().taskId}").assertTextContains("3 + 4")
        compose.openDestination("OSCAR")
        compose.onNodeWithText("Discard private interaction").performScrollTo().performClick()
        compose.waitUntil(10_000) { !session.state.value.busy && !session.state.value.privateSuppressed }
        assertTrue(session.state.value.snapshot!!.tasks.none { it.description == "3 + 4" })
        compose.runOnIdle { session.stop() }
        assertNull(session.state.value.snapshot); assertTrue(session.state.value.interactions.isEmpty())
        compose.runOnIdle { session.start() }
        compose.waitUntil(10_000) { session.state.value.link == Link.CONNECTED }
        assertTrue(session.state.value.snapshot!!.tasks.none { it.description == "3 + 4" })
        compose.runOnIdle { session.disconnect() }
    }
    @Test fun longReportedResponseHasCompleteReadingSurface() {
        val response = "Reported reference paragraph. ".repeat(180) + "END OF REPORTED FIXTURE"
        val task = CoreTask("reading-fixture", "Synthetic reading request", "verified", "reference", "online", 1,
            emptyList(), listOf("reference-evidence"), null, null, response)
        val state = MobileState(link = Link.CONNECTED, observedAt = System.currentTimeMillis(),
            snapshot = CoreSnapshot(listOf(task), emptyList(), System.currentTimeMillis()),
            interactions = listOf(Interaction("Synthetic reading request", "REPORTED", task.id)))
        compose.activity.runOnUiThread { compose.activity.setContentForTest {
            OscarTheme { Column(Modifier.fillMaxSize().padding(24.dp)) { PresenceScreen(state, "", {}, {}, {}, {}, {}) } }
        } }
        compose.onNodeWithText("Read response").performClick()
        compose.onNodeWithText(response).assertExists()
        compose.onNodeWithText("REPORTED · a response is testimony, not independent verification.").assertExists()
        capture("13-2-long-reported-simulated", "responseDialog")
        compose.onNodeWithText("Back").performClick()
    }
    @Test fun nativeApprovalInspectionExpiryAndReferenceDenialNeverFabricateConsent() {
        val arguments = androidx.test.platform.app.InstrumentationRegistry.getArguments()
        val origin = arguments.getString("group02_origin")
        org.junit.Assume.assumeTrue("Explicit disposable Core fixture", origin != null)
        require(origin!!.startsWith("http://127.0.0.1:"))
        val fixture = org.json.JSONObject().put("url", origin).put("node_id", "reference-mobile-software")
            .put("session_id", arguments.getString("group02_session")).put("token", arguments.getString("group02_token"))
        val session = androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java]
        compose.runOnIdle { session.connect(fixture) }
        compose.waitUntil(10_000) { session.state.value.link == Link.CONNECTED }
        compose.onNodeWithTag("interactionInput").performTextInput("what is four plus five")
        compose.onNodeWithText("Send").performClick()
        compose.waitUntil(10_000) { session.state.value.interactions.isNotEmpty() && !session.state.value.busy }
        val id = session.state.value.interactions.last().taskId!!
        val task = session.state.value.snapshot!!.tasks.single { it.id == id }
        val decoded = Approval.parse(CoreClient(fixture).call("challenge", org.json.JSONObject().put("operation", "approve").put("task_id", id)), session.state.value.coreNow(System.currentTimeMillis()))
        assertEquals(task.generation, decoded.generation)
        compose.runOnIdle { session.review(task, "approve") }
        compose.waitUntil(10_000) { session.state.value.approval != null || session.state.value.link != Link.CONNECTED }
        assertNotNull("Review failed: ${session.state.value.message}", session.state.value.approval)
        val approval = session.state.value.approval!!
        assertEquals("what is four plus five", approval.exactRequest)
        compose.onNode(hasText(approval.review) and hasAnyAncestor(hasTestTag("approvalDialog"))).assertExists()
        compose.onNodeWithText("Confirm securely").assertIsEnabled()
        capture("13-3-reference-approval", "approvalDialog")
        assertEquals("planned", parseTask(CoreClient(fixture).call("inspect", org.json.JSONObject().put("task_id", id))).state)
        compose.waitUntil(35_000) { session.state.value.coreNow(System.currentTimeMillis()) >= approval.expiresAt }
        compose.runOnIdle { session.refreshNow() }
        compose.waitUntil(10_000) { session.state.value.observedAt > approval.expiresAt - 30_000 }
        compose.mainClock.advanceTimeBy(30_500)
        compose.onNodeWithText("Confirm securely").assertIsNotEnabled()
        compose.onNodeWithText("Back").performClick()
        assertNull(session.state.value.approval)
        compose.runOnIdle { session.inspect(id) }
        compose.waitUntil(10_000) { session.state.value.inspected != null }
        compose.onNodeWithTag("taskInspector").assertExists()
        compose.onNodeWithText("Back").performClick()
        compose.runOnIdle { session.review(task, "deny") }
        compose.waitUntil(10_000) { session.state.value.approval != null }
        // Genuine Android handoff on an uncommissioned emulator must fail closed.
        assertFalse(compose.activity.getSystemService(android.app.KeyguardManager::class.java).isDeviceSecure)
        compose.onNodeWithText("Confirm denial").performClick()
        compose.waitUntil(5000) { session.state.value.approval == null }
        assertEquals("planned", parseTask(CoreClient(fixture).call("inspect", org.json.JSONObject().put("task_id", id))).state)
        val connection = java.net.URI(arguments.getString("group02_control")!!).toURL().openConnection() as java.net.HttpURLConnection
        try {
            connection.requestMethod = "POST"; connection.doOutput = true; connection.connectTimeout = 5000; connection.readTimeout = 8000
            connection.setRequestProperty("X-Reference-Token", arguments.getString("group02_control_token"))
            val data = org.json.JSONObject().put("operation", "deny").put("task_id", id).toString().toByteArray()
            connection.setFixedLengthStreamingMode(data.size); connection.outputStream.use { it.write(data) }
            assertEquals(200, connection.responseCode)
            val denied = parseTask(org.json.JSONObject(connection.inputStream.bufferedReader().use { it.readText() }))
            assertEquals("cancelled", denied.state)
        } finally { connection.disconnect() }
        compose.runOnIdle { session.refreshNow() }
        compose.waitUntil(10_000) { session.state.value.snapshot?.tasks?.any { it.id == id && it.state == "cancelled" } == true }
        assertNull(session.state.value.approval)
        capture("13-3-reference-denied-readback")
    }
    @Test fun referenceGridShowsDesktopOriginAndRecoversActualNetworkLoss() {
        val arguments = androidx.test.platform.app.InstrumentationRegistry.getArguments()
        val origin = arguments.getString("group02_origin")
        org.junit.Assume.assumeTrue("Explicit disposable Grid/Core fixture", origin != null)
        val fixture = org.json.JSONObject().put("url", origin).put("node_id", "reference-mobile-software")
            .put("session_id", arguments.getString("group02_session")).put("token", arguments.getString("group02_token"))
        val session = androidx.lifecycle.ViewModelProvider(compose.activity)[CoreSession::class.java]
        compose.runOnIdle { session.connect(fixture) }
        compose.waitUntil(10_000) { session.state.value.link == Link.CONNECTED }
        val desktop = session.state.value.snapshot!!.tasks.single { it.id == arguments.getString("group02_desktop_task") }
        assertEquals("Desktop", desktop.origin); assertEquals("group02-reference-desktop", desktop.originNode)
        assertFalse(desktop.description.contains("8 + 9")); assertFalse("approve" in desktop.actions)
        compose.openDestination("Devices")
        compose.onNodeWithTag("device-group02-reference-desktop").performScrollTo().performClick()
        compose.onNodeWithText("No currently advertised executor capabilities").assertExists()
        capture("13-4-reference-grid")
        compose.openDestination("Activity")
        compose.onNodeWithTag("task-description-${desktop.id}").assertExists()
        control("network_off")
        try {
            compose.runOnIdle { session.refreshNow() }
            compose.waitUntil(15_000) { session.state.value.link == Link.DEGRADED }
            assertNull(session.state.value.snapshot); assertNull(session.state.value.approval)
            compose.openDestination("Devices")
            compose.onNodeWithText("No current Grid snapshot is available.").assertExists()
        } finally { control("network_on") }
        compose.runOnIdle { session.refreshNow() }
        compose.waitUntil(10_000) { session.state.value.link == Link.CONNECTED }
        assertTrue(session.state.value.snapshot!!.tasks.any { it.id == desktop.id })
        compose.onNodeWithText("Disconnect and remove local credentials").performScrollTo().performClick()
        compose.waitUntil(5000) { SessionVault(compose.activity).load() == null }
        assertNull(session.state.value.snapshot)
    }
}

private fun MainActivity.setContentForTest(content: @Composable () -> Unit) = setContent(content = content)
