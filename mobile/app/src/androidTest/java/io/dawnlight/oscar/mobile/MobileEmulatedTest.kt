package io.dawnlight.oscar.mobile

import android.content.Context
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** EMULATED software evidence only. No owner grants or physical capability acceptance. */
class MobileEmulatedTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun navigationAndRestorationKeepOneRelationship() {
        compose.onNodeWithText("Activity").performClick()
        compose.onNodeWithText("Ongoing work").assertIsDisplayed()
        compose.onNodeWithText("Devices").performClick()
        compose.onNodeWithText("Connection Grid").assertIsDisplayed()
        compose.activityRule.scenario.recreate()
        compose.onNodeWithText("Connection Grid").assertIsDisplayed()
        compose.onNodeWithText("Settings").performClick()
        compose.onNodeWithText("Privacy").performClick()
        compose.onNodeWithText("Permissions & privacy").assertIsDisplayed()
        compose.onNodeWithText("OSCAR").performClick()
        compose.onNodeWithTag("orb").assertExists()
        compose.runOnIdle {
            val image = android.graphics.BitmapFactory.decodeResource(compose.activity.resources, R.drawable.oscar_orb)
            assertEquals(1164, image.width); assertEquals(1164, image.height)
            assertNotEquals(0, android.graphics.Color.alpha(image.getPixel(576, 584)))
            assertNotEquals(image.getPixel(576, 584), image.getPixel(50, 50))
            image.recycle()
        }
    }
    @Test fun disconnectedAndVoiceUnavailableNeverAdvertiseSuccess() {
        compose.onNodeWithTag("interactionInput").performTextInput("2 + 3")
        compose.onNodeWithText("Send").assertIsNotEnabled()
        compose.onNodeWithText("Voice").performScrollTo().performClick()
        compose.onNodeWithText("Android voice binding is not commissioned. Listening, playback, Voice Match and Voice Map are unavailable.").assertExists()
        val context = compose.activity
        assertFalse(context.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("microphone_perception", false))
        assertNull(MicrophoneService.binding)
    }
    @Test fun privateCredentialsAreSealedAndReloaded() {
        compose.runOnIdle {
            val vault = SessionVault(compose.activity)
            val token = "synthetic-emulator-session-only"
            val session = org.json.JSONObject().put("url", "https://example.com").put("node_id", "fixture-node")
                .put("session_id", "fixture-session").put("token", token)
            vault.save(session)
            val sealed = compose.activity.getSharedPreferences("session", Context.MODE_PRIVATE).getString("sealed", "")!!
            assertFalse(sealed.contains(token)); assertFalse(sealed.contains("example.com"))
            assertEquals(token, vault.load().getString("token"))
            vault.forget()
            assertNull(vault.load())
        }
    }
    @Test fun notificationAndBiometricBoundariesFailClosed() {
        compose.runOnIdle {
            val context = compose.activity
            assertTrue(NotificationBoundary.exposed().isEmpty())
            val pending = android.app.PendingIntent.getBroadcast(context, 10, android.content.Intent(context, MainActivity::class.java), android.app.PendingIntent.FLAG_IMMUTABLE)
            val action = android.app.Notification.Action.Builder(null, "Reply", pending)
                .setSemanticAction(android.app.Notification.Action.SEMANTIC_ACTION_REPLY)
                .addRemoteInput(android.app.RemoteInput.Builder("reply").setAllowFreeFormInput(true).build()).build()
            val notification = android.app.Notification.Builder(context, "fixture").addAction(action).build()
            val source = android.service.notification.StatusBarNotification(context.packageName, context.packageName, 1, null, 0, 0, 0, notification,
                android.os.Process.myUserHandle(), System.currentTimeMillis())
            assertNull(NotificationBoundary.replyAction(source))
            val keyguard = context.getSystemService(android.app.KeyguardManager::class.java)
            if (!keyguard.isDeviceSecure) {
                try { SessionVault(context).publicIdentity(); fail("Insecure emulator enrolled owner") }
                catch (_: SecurityException) { }
            }
        }
    }
    @Test fun privacyGrantDoesNotEnableCaptureOrAction() {
        compose.onNodeWithText("Settings").performClick()
        compose.onNodeWithText("Privacy").performClick()
        val grant = compose.onNodeWithContentDescription("Allow microphone perception")
        grant.performScrollTo().performClick()
        compose.waitUntil(5000) { compose.activity.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("microphone_perception", false) }
        compose.runOnIdle {
            assertNull(MicrophoneService.binding)
            assertFalse(compose.activity.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("notification_reply", false))
            assertEquals(android.content.pm.PackageManager.PERMISSION_DENIED, compose.activity.checkSelfPermission(android.Manifest.permission.RECORD_AUDIO))
        }
        grant.performClick()
        compose.waitUntil(5000) { !compose.activity.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("microphone_perception", false) }
    }
    @Test fun corruptedSessionRestartFailsClosed() {
        compose.runOnIdle {
            compose.activity.getSharedPreferences("session", Context.MODE_PRIVATE).edit().putString("sealed", "invalid-fixture").commit()
        }
        compose.activityRule.scenario.recreate()
        compose.waitUntil(5000) { compose.onAllNodesWithText("Saved connection unavailable. Reconnect from trusted Core.").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Send").assertIsNotEnabled()
        compose.runOnIdle { SessionVault(compose.activity).forget() }
    }
    @Test fun explicitLoopbackFixtureReadback() {
        val arguments = androidx.test.platform.app.InstrumentationRegistry.getArguments()
        val origin = arguments.getString("reference_fixture_url")
        org.junit.Assume.assumeTrue("Opt-in disposable emulator/Core fixture only", origin != null)
        require(origin!!.startsWith("http://127.0.0.1:"))
        val stored = SessionVault(compose.activity).load()
        assertNotNull("Pair the disposable reference session through the app first", stored)
        assertEquals(origin, stored.getString("url"))
        assertEquals("reference-mobile-software", stored.getString("node_id"))
        assertEquals(arguments.getString("reference_session_id"), stored.getString("session_id"))
        assertEquals(arguments.getString("reference_token_digest"), NotificationBoundary.hash(stored.getString("token")))
        val snapshot = parseSnapshot(CoreClient(stored).call("snapshot", org.json.JSONObject()))
        assertTrue(snapshot.nodes.any { it.role == "OSCAR Mobile" })
        assertTrue(snapshot.tasks.any { it.state == "verified" && it.value == "5" })
    }
}
