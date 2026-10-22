package io.dawnlight.oscar.mobile

import android.content.Context
import android.os.SystemClock
import android.widget.EditText
import android.widget.TextView
import androidx.test.core.app.ActivityScenario
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.security.KeyStore
import java.security.cert.CertificateFactory
import java.util.Base64
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManagerFactory

/** Actual native outbound Grid service and separate host Core, synthetic emulator identity only. */
class NativeGridExecutionTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private fun stage(value: String) { context.openFileOutput("software-native-stage.txt", Context.MODE_PRIVATE).use { it.write(value.toByteArray()) } }
    private fun waitFor(message: String, milliseconds: Long = 45_000, check: () -> Boolean) {
        val until = SystemClock.elapsedRealtime() + milliseconds
        while (SystemClock.elapsedRealtime() < until) { if (check()) return; SystemClock.sleep(50) }
        fail(message)
    }
    @Test fun actualGridExecutesThenWithdrawsAndRevokes() {
        assumeTrue("Disposable emulator required", android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        val args = InstrumentationRegistry.getArguments()
        assumeTrue("Actual isolated Core fixture required", args.getString("grid_invitation") != null)
        instrumentation.getUiAutomation(android.app.UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES)
        val previous = HttpsURLConnection.getDefaultSSLSocketFactory()
        var media: android.media.session.MediaSession? = null
        try {
            stage("Installing disposable TLS trust")
            val certificate = CertificateFactory.getInstance("X.509").generateCertificate(Base64.getDecoder().decode(args.getString("grid_ca")).inputStream())
            val trust = KeyStore.getInstance(KeyStore.getDefaultType()).apply { load(null); setCertificateEntry("disposable-core-ca", certificate) }
            val managers = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply { init(trust) }
            HttpsURLConnection.setDefaultSSLSocketFactory(SSLContext.getInstance("TLS").apply { init(null, managers.trustManagers, null) }.socketFactory)
            val invitation = JSONObject(String(Base64.getDecoder().decode(args.getString("grid_invitation")), Charsets.UTF_8))
            val vault = SessionVault(context)
            val pending = CoreClient(JSONObject().put("url", args.getString("grid_origin")))
            val saved = pending.enroll(invitation, vault.deviceIdentity(), vault::signDevice).put("retain_conversation", true)
            stage("Core enrollment accepted")
            vault.save(saved)
            stage("Native session saved")
            val prefs = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
            assertTrue(prefs.edit().putBoolean("app_actions", true).putBoolean("accessibility_perception", true)
                .putBoolean("accessibility_actions", true).putBoolean("media_perception", true).putBoolean("media_actions", true)
                .putString("native_action_packages", context.packageName).commit())
            ActivityScenario.launch(MainActivity::class.java).use { source ->
                stage("MainActivity resumed")
                source.onActivity {
                    val session = android.media.session.MediaSession(it, "OSCAR synthetic metadata only")
                    fun playback(value: Int) = session.setPlaybackState(android.media.session.PlaybackState.Builder()
                        .setActions(android.media.session.PlaybackState.ACTION_PLAY or android.media.session.PlaybackState.ACTION_PAUSE)
                        .setState(value, 0, if (value == android.media.session.PlaybackState.STATE_PLAYING) 1f else 0f).build())
                    session.setCallback(object : android.media.session.MediaSession.Callback() {
                        override fun onPause() { playback(android.media.session.PlaybackState.STATE_PAUSED) }
                        override fun onPlay() { playback(android.media.session.PlaybackState.STATE_PLAYING) }
                    })
                    playback(android.media.session.PlaybackState.STATE_PLAYING)
                    session.isActive = true; media = session
                }
                source.onActivity { NativeWorker.start(it) }
                stage("Worker start requested")
                waitFor("Real AccessibilityService was not connected") { AppControlService.connected != null }
                waitFor("Native Worker did not connect: ${NativeWorker.status}") { NativeWorker.running }
                stage("Worker advertisement accepted")
                val connection = CoreClient(saved, vault::signDevice)
                fun currentSnapshot() = parseGridSnapshot(connection.call("snapshot", JSONObject()), saved.getString("core_id"), saved.getString("node_id"))
                val snapshot = currentSnapshot()
                val snapshotElapsed = SystemClock.elapsedRealtime()
                val management = requireNotNull(snapshot.management)
                val connections = requireNotNull(snapshot.connections)
                assertEquals("ask", management.mode)
                assertTrue(management.capabilities.any { it.node == saved.getString("node_id") })
                val proposal = delegationRequest(management, connections, "secure", 120)
                val review = Approval.management(connection.call("authority_challenge", proposal), "authority", proposal,
                    snapshot.managementStamp(), snapshot.observedAt + SystemClock.elapsedRealtime() - snapshotElapsed)
                assertTrue(connection.matches(review))
                assertEquals("authority_complete", review.completion)
                val routine = connection.call("submit", JSONObject().put("text", "every day for 3 runs: 2 + 3")
                    .put("kind", "text").put("target", saved.getString("core_id"))
                    .put("parameters", JSONObject()).put("retain", true)).getJSONObject("assistance_proposal")
                assertEquals("create_natural", routine.getString("operation"))
                assertEquals(3, routine.getJSONObject("value").getInt("max_runs"))
                val routineReview = Approval.management(connection.call("assistance_challenge", routine), "assistance", routine,
                    snapshot.managementStamp(), snapshot.observedAt + SystemClock.elapsedRealtime() - snapshotElapsed)
                assertEquals("assistance_complete", routineReview.completion)
                assertEquals("create", routineReview.material().getJSONObject("review").getJSONObject("proposal").getString("operation"))
                lateinit var product: CoreSession
                source.onActivity { product = androidx.lifecycle.ViewModelProvider(it)[CoreSession::class.java] }
                waitFor("Native conversation session did not restore management") {
                    product.state.value.snapshot?.management != null && !product.state.value.busy
                }
                source.onActivity { assertTrue(product.send("every day for 3 runs: 2 + 3")) }
                waitFor("Native conversation did not open the exact automation review") {
                    product.state.value.approval?.completion == "assistance_complete" && !product.state.value.busy
                }
                assertEquals("create", product.state.value.approval!!.material().getJSONObject("review").getJSONObject("proposal").getString("operation"))
                source.onActivity { product.dismissApproval() }
                kotlinx.coroutines.runBlocking { kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.Main) { product.refresh() } }
                assertNull("Refresh restored a dismissed automation review", product.state.value.approval)
                instrumentation.waitForIdleSync()
                assertEquals(0, parseDayBrief(connection.call("day_brief", JSONObject()).getJSONObject("day_brief")).sources.size)
                // Parsing a review cannot activate authority; native owner authentication is separate.
                assertEquals("ask", requireNotNull(currentSnapshot().management).mode)
                stage("Actual Core management projection and exact unsigned review accepted")
                assertTrue(prefs.edit().putBoolean("clipboard_perception", true).putBoolean("clipboard_actions", true).commit())
                waitFor("OSCAR did not regain clipboard focus; approval=${product.state.value.approval?.completion}, link=${product.state.value.link}") {
                    var focused = false
                    source.onActivity { focused = it.hasWindowFocus() }
                    focused
                }
                context.openFileOutput("software-native-ready.json", Context.MODE_PRIVATE).use { it.write("{}".toByteArray()) }
                waitFor("Core clipboard task did not reach the real Android clipboard") {
                    var value = ""
                    source.onActivity { value = it.getSystemService(android.content.ClipboardManager::class.java).primaryClip?.getItemAt(0)?.text?.toString().orEmpty() }
                    value == "Grid synthetic clipboard"
                }
                waitFor("Host did not verify independent clipboard readback") { context.getFileStreamPath("software-native-clipboard-verified").exists() }
                waitFor("Core media task did not pause synthetic media metadata") { media?.controller?.playbackState?.state == android.media.session.PlaybackState.STATE_PAUSED }
                waitFor("Host did not verify independent media readback") { context.getFileStreamPath("software-native-media-verified").exists() }
                source.onActivity { it.getSystemService(android.content.ClipboardManager::class.java).clearPrimaryClip() }
                assertTrue(prefs.edit().putBoolean("clipboard_perception", false).putBoolean("clipboard_actions", false).commit())
                ActivityScenario.launch(CapabilityFixtureActivity::class.java).use { target ->
                    context.openFileOutput("software-native-target-ready", Context.MODE_PRIVATE).close()
                    waitFor("Core task did not set the real target text") {
                        var text = ""; target.onActivity { text = it.findViewById<EditText>(R.id.capability_fixture_input).text.toString() }; text == "Grid synthetic agenda"
                    }
                    waitFor("Core task did not click the real target button") {
                        var text = ""; target.onActivity { text = it.findViewById<TextView>(R.id.capability_fixture_result).text.toString() }; text == "Reviewed: Grid synthetic agenda"
                    }
                    // Let Core's separate UI readback complete before withdrawing local observation.
                    waitFor("Host did not confirm independent Core readback") { context.getFileStreamPath("software-native-verified").exists() }
                    assertTrue(prefs.edit().putBoolean("accessibility_actions", false).commit())
                    context.openFileOutput("software-native-withdrawn", Context.MODE_PRIVATE).close()
                    waitFor("Host did not verify withdrawn advertisement") { context.getFileStreamPath("software-native-withdrawal-verified").exists() }
                    assertTrue(prefs.edit().putBoolean("accessibility_actions", true).commit())
                    assertEquals("revoked", connection.call("revoke", JSONObject()).getString("state"))
                    waitFor("Revoked native Worker kept running", 15_000) { !NativeWorker.running }
                    val claims = context.getSharedPreferences("native-execution-claims", Context.MODE_PRIVATE).all.size
                    assertTrue("No durable pre-effect execution claim", claims >= 3)
                    context.openFileOutput("software-native-result.json", Context.MODE_PRIVATE).use { it.write(JSONObject()
                        .put("text", "Grid synthetic agenda").put("result", "Reviewed: Grid synthetic agenda")
                        .put("claims", claims).put("clipboard", true).put("media", true).put("revoked", true).put("management_review", true).put("owner_activation", false).toString().toByteArray()) }
                }
            }
        } finally {
            NativeWorker.stop(context)
            instrumentation.runOnMainSync { media?.release() }
            context.getSharedPreferences("permissions", Context.MODE_PRIVATE).edit().putBoolean("app_actions", false)
                .putBoolean("accessibility_perception", false).putBoolean("accessibility_actions", false)
                .putBoolean("clipboard_perception", false).putBoolean("clipboard_actions", false)
                .putBoolean("media_perception", false).putBoolean("media_actions", false).putString("native_action_packages", "").commit()
            HttpsURLConnection.setDefaultSSLSocketFactory(previous)
        }
    }
    @Test fun processRestorationDoesNotReplayOrStartWorker() {
        assumeTrue("Disposable emulator required", android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        assumeTrue("Prior exact Grid acceptance required", context.getFileStreamPath("software-native-result.json").exists())
        val result = JSONObject(context.openFileInput("software-native-result.json").bufferedReader().use { it.readText() })
        assertTrue(result.getBoolean("revoked"))
        assertFalse(NativeWorker.running)
        assertEquals(result.getInt("claims"), context.getSharedPreferences("native-execution-claims", Context.MODE_PRIVATE).all.size)
        assertNotNull(SessionVault(context).load())
    }
}
