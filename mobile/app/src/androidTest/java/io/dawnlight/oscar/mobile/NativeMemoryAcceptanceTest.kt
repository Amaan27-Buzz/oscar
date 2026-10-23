package io.dawnlight.oscar.mobile

import android.content.Context
import android.os.SystemClock
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

/** Rendered production controls and real TLS transport; the host signs only synthetic owner reviews. */
class NativeMemoryAcceptanceTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val original = "The synthetic project is named Copper"
    private val correction = "The synthetic project is named Silver"

    private fun write(name: String, value: String) = context.openFileOutput("software-memory-$name", Context.MODE_PRIVATE).use { it.write(value.toByteArray()) }
    private fun stage(value: String) = write("stage", value)
    private fun hostFile(name: String): String {
        val file = context.getFileStreamPath("software-memory-$name")
        val until = SystemClock.elapsedRealtime() + 20_000
        while (SystemClock.elapsedRealtime() < until) {
            if (file.exists() && file.length() > 0) return file.readText()
            SystemClock.sleep(50)
        }
        error("Synthetic host did not acknowledge $name")
    }

    @Test fun renderedCorrectionForgetRefreshAndConsumedReviewRejection() {
        assumeTrue(android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        val args = InstrumentationRegistry.getArguments()
        check(args.getString("memory_disposable") == "true")
        val previous = HttpsURLConnection.getDefaultSSLSocketFactory()
        try {
            val certificate = CertificateFactory.getInstance("X.509").generateCertificate(Base64.getDecoder().decode(args.getString("grid_ca")).inputStream())
            val trust = KeyStore.getInstance(KeyStore.getDefaultType()).apply { load(null); setCertificateEntry("disposable-core-ca", certificate) }
            val managers = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm()).apply { init(trust) }
            HttpsURLConnection.setDefaultSSLSocketFactory(SSLContext.getInstance("TLS").apply { init(null, managers.trustManagers, null) }.socketFactory)
            val invitation = JSONObject(String(Base64.getDecoder().decode(args.getString("grid_invitation")), Charsets.UTF_8))
            val model = ViewModelProvider(compose.activity)[CoreSession::class.java]
            compose.runOnIdle { model.enroll(args.getString("grid_origin")!!, invitation, true) }
            compose.waitUntil(20_000) { model.state.value.link == Link.CONNECTED && !model.state.value.busy }
            val vault = SessionVault(context)
            val saved = requireNotNull(vault.load())
            val connection = CoreClient(saved, vault::signDevice)
            fun memory() = parseMemory(JSONObject(requireNotNull(model.state.value.snapshot?.management).source).getJSONObject("memory"))
            assertTrue(memory().records.single { it.content == original }.canCorrect)
            assertTrue(model.state.value.interactions.any { it.text == original })

            compose.onNodeWithTag("destination-SETTINGS").performClick()
            compose.onNodeWithText("Memory", substring = false).performScrollTo().performClick()
            compose.onNodeWithText(original).performScrollTo().performClick()
            compose.onNodeWithText("Review forgetting this memory").performScrollTo().performClick()
            compose.waitUntil(10_000) { model.state.value.approval != null && !model.state.value.busy }
            val declined = requireNotNull(model.state.value.approval)
            assertEquals("memory_forget", declined.material().getJSONObject("change").getString("operation"))
            compose.onNodeWithTag("approvalDialog").assertIsDisplayed()
            compose.onNode(hasContentDescription("Back") and hasAnyAncestor(hasTestTag("approvalDialog"))).performClick()
            compose.waitUntil(5000) { model.state.value.approval == null }
            stage("declined")
            assertEquals("verified", hostFile("declined.ack"))
            assertEquals(1, memory().records.count { it.content == original })

            compose.onNode(hasSetTextAction()).performScrollTo().performTextInput(correction)
            compose.onAllNodes(isToggleable())[1].performScrollTo().performClick()
            compose.onNodeWithText("Review memory correction").performScrollTo().performClick()
            compose.waitUntil(10_000) { model.state.value.approval != null && !model.state.value.busy }

            fun completeSynthetic(phase: String, operation: String) {
                val review = requireNotNull(model.state.value.approval)
                assertEquals("assistance_complete", review.completion)
                assertEquals(operation, review.material().getJSONObject("change").getString("operation"))
                compose.onNodeWithTag("approvalDialog").assertIsDisplayed()
                compose.onNodeWithText("Plan & permission details").performScrollTo().performClick()
                compose.onNodeWithText("Confirm securely").performScrollTo().assertIsEnabled()
                write("$phase.json", JSONObject().put("challenge_id", review.id).put("signing_payload", review.signingPayload)
                    .put("completion", review.completion).toString())
                stage("${phase}_review")
                val signature = hostFile("$phase.signature").trim()
                // No Android biometric is simulated or bypassed; this signature belongs to the disposable host owner.
                compose.runOnIdle { model.dismissApproval() }
                val request = JSONObject().put("challenge_id", review.id).put("signature", signature)
                val result = connection.call(review.completion, request)
                assertEquals("verified", result.getString("status"))
                assertTrue(result.getBoolean("memory_changed"))
                var replayRejected = false
                try { connection.call(review.completion, request) } catch (_: SecurityException) { replayRejected = true }
                assertTrue("Consumed signed review accepted twice", replayRejected)
                stage("${phase}_completed")
                assertEquals("verified", hostFile("$phase.ack"))
                compose.onNodeWithText("Refresh saved memory").performScrollTo().performClick()
            }

            completeSynthetic("correction", "memory_correct")
            compose.waitUntil(10_000) { model.state.value.link == Link.CONNECTED && memory().records.any { it.content == correction } && memory().records.none { it.content == original } }
            navigateReview(compose, "OSCAR")
            val query = "Recall the synthetic project name"
            compose.onNodeWithTag("interactionInput").assertIsDisplayed().performTextInput(query)
            compose.onNodeWithText("Send", substring = false).performClick()
            compose.waitUntil(15_000) { model.state.value.snapshot?.tasks?.any { it.description == query && it.response?.contains(correction) == true } == true }
            val recall = model.state.value.snapshot!!.tasks.single { it.description == query }
            assertEquals("RECALLED", recall.responseStatus)
            assertTrue(recall.sourceEventIds.isNotEmpty())
            assertNull(recall.value)
            compose.onAllNodesWithText("Read response").onLast().performScrollTo().performClick()
            compose.onNode(hasText("Earlier retained evidence") and hasAnyAncestor(hasTestTag("responseDialog"))).assertIsDisplayed()
            compose.onNode(hasText("From ${recall.sourceEventIds.size} retained sources. Current facts may differ.") and hasAnyAncestor(hasTestTag("responseDialog"))).assertIsDisplayed()
            compose.onNode(hasContentDescription("Back") and hasAnyAncestor(hasTestTag("responseDialog"))).performClick()
            navigateReview(compose, "SETTINGS")
            compose.onNodeWithText("Memory", substring = false).performScrollTo().performClick()
            compose.onNodeWithText(correction).performScrollTo().performClick()
            compose.onAllNodes(isToggleable())[0].performScrollTo().performClick()
            compose.onNodeWithText("Review forgetting this memory").performScrollTo().performClick()
            compose.waitUntil(10_000) { model.state.value.approval != null && !model.state.value.busy }
            assertTrue(model.state.value.approval!!.material().getJSONObject("change").getJSONObject("value").getBoolean("forget_sources"))
            completeSynthetic("forget", "memory_forget")
            compose.waitUntil(10_000) {
                model.state.value.link == Link.CONNECTED && memory().records.none { it.content == correction || it.content == original } &&
                    model.state.value.interactions.none { it.text == correction }
            }
            compose.onAllNodesWithText(correction).assertCountEquals(0)
            val cache = requireNotNull(vault.loadHistory(connection.binding()))
            assertFalse(cache.toString().contains(correction))
            assertNull(model.state.value.approval)
            val withdrawnRecall = model.state.value.snapshot!!.tasks.single { it.id == recall.id }
            assertNull(withdrawnRecall.response); assertTrue(withdrawnRecall.sourceEventIds.isEmpty())
            compose.activityRule.scenario.recreate()
            compose.waitUntil(15_000) { model.state.value.link == Link.CONNECTED }
            assertTrue(memory().records.none { it.content == correction || it.content == original })
            assertNull(model.state.value.approval)
            assertFalse(requireNotNull(vault.loadHistory(connection.binding())).toString().contains(correction))
            val notifications = context.getSystemService(android.app.NotificationManager::class.java)
            notifications.createNotificationChannel(android.app.NotificationChannel("awareness", "Synthetic awareness", android.app.NotificationManager.IMPORTANCE_LOW))
            notifications.notify("sentry:synthetic-revocation", 2, android.app.Notification.Builder(context, "awareness")
                .setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("Synthetic awareness").build())
            compose.waitUntil(5000) { notifications.activeNotifications.any { it.tag == "sentry:synthetic-revocation" } }
            assertEquals("revoked", connection.call("revoke", JSONObject()).getString("state"))
            compose.runOnIdle { if (model.state.value.link == Link.CONNECTED) model.send("2 + 3") }
            compose.waitUntil(10_000) { model.state.value.link != Link.CONNECTED && notifications.activeNotifications.none { it.tag == "sentry:synthetic-revocation" } }
            write("result.json", JSONObject().put("rendered_controls", true).put("decline_without_mutation", true)
                .put("signed_correction", true).put("signed_forget_sources", true).put("consumed_review_rejected", true)
                .put("canonical_refresh", true).put("encrypted_history_refreshed", true).put("activity_recreation_no_replay", true)
                .put("rendered_conversation_recall", true).put("recall_withdrawn_after_forget", true)
                .put("notice_withdrawal_after_revocation", true)
                .put("android_owner_biometrics", "NOT_RUN").toString())
            stage("passed")
        } finally { HttpsURLConnection.setDefaultSSLSocketFactory(previous) }
    }
}
