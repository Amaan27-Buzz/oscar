package io.dawnlight.oscar.mobile

import android.app.Activity
import android.app.Instrumentation
import android.content.Context
import android.content.Intent
import android.os.SystemClock
import android.widget.EditText
import android.widget.TextView
import androidx.test.core.app.ActivityScenario
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.After
import org.junit.Test

/** EMULATED synthetic target only. Test authorization is not an owner/Core signature. */
class NativeCapabilitiesTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private var adapter: NativeCapabilities? = null
    private var approved: NativeAction? = null
    @Before fun disposableOnly() {
        assumeTrue("Disposable emulator required", android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        context.getSharedPreferences("permissions", Context.MODE_PRIVATE).edit()
            .putBoolean("app_actions", true).putString("native_action_packages", context.packageName).commit()
    }
    @After fun removeSyntheticGrants() {
        adapter?.close()
        context.getSharedPreferences("permissions", Context.MODE_PRIVATE).edit()
            .putBoolean("app_actions", false).putBoolean("accessibility_perception", false)
            .putBoolean("accessibility_actions", false).putString("native_action_packages", "").commit()
    }
    private fun request(native: NativeCapabilities, capability: String = "android.app.launch", value: String = "") = NativeAction(
        "emulated-${System.nanoTime()}", "synthetic-native-task", "emulated-native-node", "synthetic-session", 1, 1,
        native.gate.generation, SystemClock.elapsedRealtime() + 30_000, capability, context.packageName,
        CapabilityFixtureActivity::class.java.name, value)

    private fun awaitFocus(activity: Activity) {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        var focused = false
        while (!focused && SystemClock.elapsedRealtime() < deadline) {
            instrumentation.runOnMainSync { focused = activity.hasWindowFocus() }
            if (!focused) SystemClock.sleep(25)
        }
        assertTrue("Synthetic target did not gain focus", focused)
    }

    @Test fun actualIntentSharePopulatesFormAndIndependentReadbackInspectsResult() {
        var launched: Activity? = null
        val monitor = Instrumentation.ActivityMonitor(CapabilityFixtureActivity::class.java.name, null, false)
        instrumentation.addMonitor(monitor)
        try {
            ActivityScenario.launch(MainActivity::class.java).use { source ->
                source.onActivity { activity ->
                    val native = NativeCapabilities(context) { it == approved }.also { adapter = it; it.gate.foreground(true) }
                    val action = request(native, "android.share.text", "Synthetic preparation agenda")
                    approved = action
                    val result = native.execute(activity, action)
                    assertEquals("reported", result.state)
                    assertTrue(result.observations.isEmpty())
                }
                launched = instrumentation.waitForMonitorWithTimeout(monitor, 10_000)
                assertNotNull("Native Intent did not launch the synthetic target", launched)
                instrumentation.waitForIdleSync()
                instrumentation.runOnMainSync {
                    assertEquals("Synthetic preparation agenda", launched!!.findViewById<EditText>(R.id.capability_fixture_input).text.toString())
                }
                onView(withId(R.id.capability_fixture_submit)).perform(click())
                instrumentation.runOnMainSync {
                    assertEquals("Reviewed: Synthetic preparation agenda", launched!!.findViewById<TextView>(R.id.capability_fixture_result).text.toString())
                }
            }
        } finally {
            launched?.let { activity -> instrumentation.runOnMainSync { activity.finish() } }
            instrumentation.removeMonitor(monitor)
        }
    }

    @Test fun recreationKeepsNativeFormAndResultWithoutCreatingAuthority() {
        val intent = Intent(context, CapabilityFixtureActivity::class.java).putExtra(Intent.EXTRA_TEXT, "Recreation agenda")
        ActivityScenario.launch<CapabilityFixtureActivity>(intent).use { scenario ->
            onView(withId(R.id.capability_fixture_submit)).perform(click())
            scenario.recreate()
            scenario.onActivity {
                assertEquals("Recreation agenda", it.findViewById<EditText>(R.id.capability_fixture_input).text.toString())
                assertEquals("Reviewed: Recreation agenda", it.findViewById<TextView>(R.id.capability_fixture_result).text.toString())
                val native = NativeCapabilities(context).also { native -> adapter = native; native.gate.foreground(true) }
                assertEquals("blocked", native.execute(it, request(native)).state)
            }
        }
    }

    @Test fun explicitLaunchAndHttpsLinkReachTheExactSyntheticActivity() {
        val launched = mutableListOf<Activity>()
        var monitor = Instrumentation.ActivityMonitor(CapabilityFixtureActivity::class.java.name, null, false)
        instrumentation.addMonitor(monitor)
        try {
            ActivityScenario.launch(MainActivity::class.java).use { source ->
                instrumentation.waitForIdleSync()
                var sourceActivity: Activity? = null
                source.onActivity { sourceActivity = it }
                awaitFocus(sourceActivity!!)
                source.onActivity { activity ->
                    val native = NativeCapabilities(context) { it == approved }.also { adapter = it; it.gate.foreground(true) }
                    val action = request(native); approved = action
                    assertEquals("reported", native.execute(activity, action).state)
                }
                val first = instrumentation.waitForMonitorWithTimeout(monitor, 10_000)
                assertNotNull(first); launched.add(first!!)
                awaitFocus(first)
                monitor = Instrumentation.ActivityMonitor(CapabilityFixtureActivity::class.java.name, null, false)
                instrumentation.addMonitor(monitor)
                instrumentation.waitForIdleSync()
                instrumentation.runOnMainSync {
                    assertEquals(context.packageName, first.componentName.packageName)
                    val native = adapter!!
                    val link = request(native, "android.link.open", "https://example.invalid/synthetic-agenda"); approved = link
                    assertEquals("reported", native.execute(first, link).state)
                }
                val second = instrumentation.waitForMonitorWithTimeout(monitor, 10_000)
                assertNotNull(second); launched.add(second!!)
                instrumentation.runOnMainSync { assertEquals("https://example.invalid/synthetic-agenda", second.intent.dataString) }
            }
        } finally {
            launched.reversed().forEach { activity -> instrumentation.runOnMainSync { activity.finish() } }
            instrumentation.removeMonitor(monitor)
        }
    }

    @Test fun revocationBackgroundCancellationAndReplayDenyNativeDispatch() {
        ActivityScenario.launch(CapabilityFixtureActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                val native = NativeCapabilities(context) { it == approved }.also { adapter = it; it.gate.foreground(true) }
                val action = request(native); approved = action
                native.cancel(action.requestId)
                assertEquals("blocked", native.execute(activity, action).state)
                val next = request(native); approved = next
                native.gate.foreground(false); native.gate.foreground(true)
                assertEquals("blocked", native.execute(activity, next).state)
                val revoked = request(native); approved = revoked
                context.getSharedPreferences("permissions", Context.MODE_PRIVATE).edit().putBoolean("app_actions", false).commit()
                assertEquals("blocked", native.execute(activity, revoked).state)
                context.getSharedPreferences("permissions", Context.MODE_PRIVATE).edit().putBoolean("app_actions", true).commit()
                assertEquals("blocked", native.execute(activity, revoked).state)
            }
        }
    }

    @Test fun privilegedInterfacesStayUnavailableWithoutAndroidAndCoreGrants() {
        ActivityScenario.launch(CapabilityFixtureActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                val native = NativeCapabilities(context).also { adapter = it; it.gate.foreground(true) }
                assertEquals(6, native.status().size)
                assertTrue(native.status().all { it.availability == "blocked" && it.version == 1 })
                assertTrue(MainActivity::class.java.name in native.discover(context.packageName))
                assertTrue(native.discover("example.unselected").isEmpty())
                val action = request(native, "android.ui.inspect")
                assertEquals("blocked", native.execute(activity, action).state)
                assertNull(AppControlService.connected)
            }
        }
    }

    @Test fun unsafeLinksInvisibleActivitiesAndCrossAppTargetsCannotDispatch() {
        ActivityScenario.launch(CapabilityFixtureActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                val native = NativeCapabilities(context) { it == approved }.also { adapter = it; it.gate.foreground(true) }
                listOf(request(native, "android.link.open", "file:///private"),
                    request(native, "android.link.open", "https://user:secret@example.com/"),
                    request(native).copy(packageName = "example.unlisted"),
                    request(native).copy(target = "example.missing.Activity")).forEach { action ->
                    approved = action
                    assertEquals("blocked", native.execute(activity, action).state)
                }
            }
        }
    }

    @Test fun incomingSharesBecomeDraftsAndNeverSubmitOrEnableControl() {
        ActivityScenario.launch<MainActivity>(Intent(context, MainActivity::class.java).setAction(Intent.ACTION_SEND)
            .setType("text/plain").putExtra(Intent.EXTRA_TEXT, "Synthetic shared draft")).use { scenario ->
            instrumentation.waitForIdleSync()
            scenario.onActivity { activity ->
                val session = androidx.lifecycle.ViewModelProvider(activity)[CoreSession::class.java]
                assertEquals("Synthetic shared draft", session.state.value.draft)
                assertFalse(session.state.value.busy)
                assertTrue(session.state.value.interactions.isEmpty())
                session.acceptSharedText("x".repeat(1001))
                assertEquals("Synthetic shared draft", session.state.value.draft)
                session.acceptSharedText("Another share")
                assertEquals("Synthetic shared draft", session.state.value.draft)
                session.writeDraft("Edited shared draft")
            }
            scenario.recreate()
            instrumentation.waitForIdleSync()
            scenario.onActivity { activity ->
                val session = androidx.lifecycle.ViewModelProvider(activity)[CoreSession::class.java]
                assertEquals("Edited shared draft", session.state.value.draft)
                val generation = session.nativeCapabilities.gate.generation
                session.disconnect()
                assertNotEquals(generation, session.nativeCapabilities.gate.generation)
            }
        }
    }
}
