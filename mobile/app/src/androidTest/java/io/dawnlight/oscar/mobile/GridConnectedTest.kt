package io.dawnlight.oscar.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import java.security.KeyStore
import java.security.cert.CertificateFactory
import java.util.Base64
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManagerFactory

/** EMULATED only. Every operation requires a disposable emulator; never an owner phone. */
class GridConnectedTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val args get() = InstrumentationRegistry.getArguments()
    private fun emulator() { assumeTrue("Disposable emulator required", android.os.Build.HARDWARE in setOf("ranchu", "goldfish")) }
    private fun session() = ViewModelProvider(compose.activity)[CoreSession::class.java]
    private fun trustedFixture(work: () -> Unit) {
        val previous = HttpsURLConnection.getDefaultSSLSocketFactory()
        try {
            args.getString("grid_ca")?.let { encoded ->
                val certificate = CertificateFactory.getInstance("X.509").generateCertificate(Base64.getDecoder().decode(encoded).inputStream())
                val trust = KeyStore.getInstance(KeyStore.getDefaultType()).apply { load(null); setCertificateEntry("disposable-core-ca", certificate) }
                val managers = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply { init(trust) }
                val ssl = SSLContext.getInstance("TLS").apply { init(null, managers.trustManagers, null) }
                HttpsURLConnection.setDefaultSSLSocketFactory(ssl.socketFactory)
            }
            work()
        } finally { HttpsURLConnection.setDefaultSSLSocketFactory(previous) }
    }
    @Test fun connectedGrid() {
        emulator()
        val origin = args.getString("grid_origin")
        val encoded = args.getString("grid_invitation")
        assumeTrue("Actual disposable Core invitation required", origin != null && encoded != null)
        trustedFixture {
            val invitation = JSONObject(String(Base64.getDecoder().decode(encoded), Charsets.UTF_8))
            val model = session()
            compose.runOnIdle { model.enroll(origin!!, invitation, true) }
            compose.waitUntil(20_000) { model.state.value.link == Link.CONNECTED }
            assertTrue(model.state.value.remote)
            assertEquals(invitation.getString("node_id"), model.state.value.connectedNode)
            val vault = SessionVault(compose.activity)
            val saved = vault.load()!!
            assertEquals(2, saved.getInt("version"))
            val sealed = compose.activity.getSharedPreferences("session", 0).all.values.joinToString()
            assertFalse(sealed.contains(saved.getString("token")))
            assertNotNull(vault.loadHistory(CoreClient(saved).binding()))
            args.getString("grid_task")?.let { taskId ->
                compose.runOnIdle { model.inspect(taskId) }
                compose.waitUntil(10_000) { model.state.value.inspected?.id == taskId }
                val task = model.state.value.inspected!!
                assertEquals("verified", task.state); assertTrue(task.evidence.isNotEmpty())
                compose.runOnIdle { model.closeInspector() }
            }
            args.getString("grid_target")?.let { target ->
                compose.runOnIdle { assertTrue(model.submitRemote("Read disposable Android acceptance fixture", "file_read", target,
                    JSONObject().put("path", args.getString("grid_path", "fixture.txt")))) }
                compose.waitUntil(45_000) { model.state.value.snapshot?.tasks?.any { it.description == "Read disposable Android acceptance fixture" && it.state == "verified" } == true }
                val task = model.state.value.snapshot!!.tasks.first { it.description == "Read disposable Android acceptance fixture" }
                assertTrue(task.evidence.isNotEmpty()); assertNotNull(task.value)
            }
            compose.waitUntil(10_000) { !model.state.value.busy }
            val before = model.state.value.connectedNode
            compose.activityRule.scenario.recreate()
            compose.waitUntil(15_000) { model.state.value.link == Link.CONNECTED }
            assertEquals(before, model.state.value.connectedNode)
            assertNull(model.state.value.approval)
            navigateReview(compose, "DEVICES")
            compose.onNodeWithText("Connected to Core").assertExists()
            compose.onNodeWithText(before!!).assertExists()
        }
    }
    @Test fun processRestored() {
        emulator()
        assumeTrue("Previously enrolled isolated fixture required", args.getString("grid_origin") != null)
        trustedFixture {
            val saved = SessionVault(compose.activity).load()!!
            val model = session()
            compose.runOnIdle { model.start() }
            compose.waitUntil(20_000) { model.state.value.link == Link.CONNECTED }
            assertEquals(saved.getString("node_id"), model.state.value.connectedNode)
            assertNull(model.state.value.approval)
            val history = SessionVault(compose.activity).loadHistory(CoreClient(saved).binding())!!
            assertTrue(history.getLong("cursor") > 0)
            assertTrue(model.state.value.interactions.isNotEmpty())
        }
    }
    @Test fun connectionLostWithdrawsPrivateState() {
        emulator()
        assumeTrue("Explicit stopped Core fixture required", args.getString("grid_core_stopped") == "true")
        val model = session()
        compose.runOnIdle { model.refreshNow() }
        compose.waitUntil(20_000) { model.state.value.link == Link.DEGRADED }
        assertNull(model.state.value.snapshot); assertNull(model.state.value.approval)
        assertTrue(model.state.value.interactions.isEmpty())
    }
    @Test fun revokeAndLogout() {
        emulator()
        assumeTrue("Explicit disposable revoke fixture required", args.getString("grid_revoke") == "true")
        trustedFixture {
            val model = session()
            compose.runOnIdle { model.start() }
            compose.waitUntil(20_000) { model.state.value.link == Link.CONNECTED }
            compose.runOnIdle { model.revoke() }
            compose.waitUntil(10_000) { SessionVault(compose.activity).load() == null }
            val keys = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
            assertFalse(keys.containsAlias("oscar-device-v2")); assertFalse(keys.containsAlias("oscar-session-v1"))
            assertNull(model.state.value.snapshot); assertEquals(Link.DISCONNECTED, model.state.value.link)
        }
    }
}
