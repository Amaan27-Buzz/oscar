package io.dawnlight.oscar.mobile

import android.app.UiAutomation
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.os.SystemClock
import android.provider.DocumentsContract
import android.view.accessibility.AccessibilityNodeInfo
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.dp
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test

/** Actual Android consent on a disposable AVD; synthetic adapter authority is not signed Grid acceptance. */
class NativePlatformConsentTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val prefs get() = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
    private val automation get() = instrumentation.getUiAutomation(UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES)
    private var approved: NativeAction? = null

    @Before fun disposableOnly() {
        assumeTrue(android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        check(InstrumentationRegistry.getArguments().getString("platform_disposable") == "true")
        compose.runOnIdle { compose.activity.setContent { OscarTheme { Surface {
            Column(Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(16.dp)) { NativePlatformSettings() }
        } } } }
    }
    private fun waitFor(message: String, condition: () -> Boolean) {
        val end = SystemClock.elapsedRealtime() + 15_000
        while (SystemClock.elapsedRealtime() < end) {
            if (condition()) return
            SystemClock.sleep(100)
        }
        error(message + "\n" + nodes().joinToString("\n") { "${it.viewIdResourceName}: ${it.text} / ${it.contentDescription}" })
    }
    private fun nodes(): List<AccessibilityNodeInfo> {
        val result = mutableListOf<AccessibilityNodeInfo>()
        val queue = java.util.ArrayDeque<AccessibilityNodeInfo>()
        automation.rootInActiveWindow?.let(queue::add)
        while (queue.isNotEmpty() && result.size < 300) {
            val node = queue.removeFirst(); result.add(node)
            for (index in 0 until node.childCount) node.getChild(index)?.let(queue::add)
        }
        return result
    }
    private fun systemClick(vararg labels: String) {
        waitFor("System control unavailable: ${labels.joinToString()}") {
            val node = nodes().firstOrNull { it.isVisibleToUser && (it.text?.toString() in labels || it.contentDescription?.toString() in labels) }
            var clickable = node
            while (clickable != null && !clickable.isClickable) clickable = clickable.parent
            clickable?.performAction(AccessibilityNodeInfo.ACTION_CLICK) == true
        }
    }
    private fun action(native: NativeCapabilities, capability: String, target: String = "", value: String = "") = NativeAction(
        "platform-${System.nanoTime()}", "synthetic-platform-task", "synthetic-node", "synthetic-session", 1, 1,
        native.gate.generation, SystemClock.elapsedRealtime() + 30_000, capability, context.packageName, target, value)
    private fun shell(command: String) = automation.executeShellCommand(command).use { descriptor ->
        android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).use { it.readBytes() }
    }

    @Test fun systemFolderSelectionScopesWriteReadAndWithdrawal() {
        assertTrue(context.contentResolver.persistedUriPermissions.isEmpty())
        compose.onNodeWithText("Choose document folder").performScrollTo().performClick()
        waitFor("Document picker directory not loaded") { nodes().any { it.viewIdResourceName?.endsWith(":id/header_title") == true && !it.text.isNullOrBlank() } }
        if (nodes().none { it.text?.toString() == "Files in selected" }) {
            systemClick("Documents")
            systemClick("oscar-platform-acceptance")
            systemClick("selected")
        }
        systemClick("Use this folder", "USE THIS FOLDER")
        systemClick("Allow", "ALLOW")
        waitFor("No persisted OS folder grant") { prefs.contains("document_tree") }
        val uri = android.net.Uri.parse(prefs.getString("document_tree", null))
        assertEquals("primary:Documents/oscar-platform-acceptance/selected", DocumentsContract.getTreeDocumentId(uri))
        assertTrue(context.contentResolver.persistedUriPermissions.single().let { it.uri == uri && it.isReadPermission && it.isWritePermission })
        NativeCapabilities(context, true) { it == approved }.use { native ->
            native.gate.foreground(true)
            assertEquals("blocked", native.execute(context, action(native, "android.files.write", "proof.txt", "Synthetic selected folder proof")).state)
            compose.runOnIdle { prefs.edit().putBoolean("file_perception", true).putBoolean("file_actions", true).putString("native_action_packages", context.packageName).commit() }
            val outside = DocumentsContract.buildDocumentUriUsingTree(uri, "primary:Documents/oscar-platform-acceptance/outside.txt")
            try { context.contentResolver.openInputStream(outside)?.close(); fail("Android permitted read outside selected tree") }
            catch (_: SecurityException) { /* Actual document provider enforces tree scope. */ }
            val write = action(native, "android.files.write", "proof.txt", "Synthetic selected folder proof"); approved = write
            assertEquals("reported", native.execute(context, write).state)
            val document = DocumentsContract.buildDocumentUriUsingTree(uri, DocumentsContract.getTreeDocumentId(uri) + "/proof.txt")
            assertEquals("Synthetic selected folder proof", context.contentResolver.openInputStream(document)!!.bufferedReader().use { it.readText() })
            val read = action(native, "android.files.read", "proof.txt"); approved = read
            assertEquals("Synthetic selected folder proof", native.execute(context, read).observations.single().text)
            val escape = action(native, "android.files.write", "../outside.txt", "Escape must not run"); approved = escape
            assertEquals("blocked", native.execute(context, escape).state)
            compose.runOnIdle { prefs.edit().putBoolean("file_actions", false).commit() }
            val deniedWrite = action(native, "android.files.write", "proof.txt", "Must not replace"); approved = deniedWrite
            assertEquals("blocked", native.execute(context, deniedWrite).state)
            val stillRead = action(native, "android.files.read", "proof.txt"); approved = stillRead
            assertEquals("Synthetic selected folder proof", native.execute(context, stillRead).observations.single().text)
            compose.onNodeWithText("Remove folder access").performScrollTo().performClick()
            waitFor("Folder grant survived withdrawal") { context.contentResolver.persistedUriPermissions.isEmpty() && !prefs.contains("document_tree") }
            assertFalse(NativePlatform(context).available("android.files.read"))
            val removed = action(native, "android.files.read", "proof.txt"); approved = removed
            assertEquals("blocked", native.execute(context, removed).state)
        }
    }

    private fun consentScreen() {
        compose.onNodeWithText("Review screen-sharing consent").performScrollTo().performClick()
        systemClick("Start", "Start now", "Start recording")
        systemClick("OSCAR")
        waitFor("MediaProjection did not start") { NativeScreenService.current != null }
    }

    @Test fun systemSingleAppConsentRequiresAuthorityAndStopsOnStopAndLock() {
        assertNull(NativeScreenService.current)
        compose.onNodeWithText("Review screen-sharing consent").performScrollTo().performClick()
        systemClick("Cancel", "CANCEL")
        assertNull(NativeScreenService.current)
        compose.runOnIdle { prefs.edit().putBoolean("screen_perception", true).putBoolean("accessibility_perception", true)
            .putString("native_action_packages", context.packageName).commit() }
        // Instrumentation process restart does not rebind an already enabled service.
        val services = String(shell("settings get secure enabled_accessibility_services")).trim()
        require(services.matches(Regex("[A-Za-z0-9_./:$-]+")))
        val other = services.split(':').filterNot { it == "null" || it == context.packageName + "/.AppControlService" || it == context.packageName + "/" + AppControlService::class.java.name }.joinToString(":")
        shell("settings put secure enabled_accessibility_services '$other'")
        shell("settings put secure enabled_accessibility_services '${listOf(other, context.packageName + "/.AppControlService").filter(String::isNotEmpty).joinToString(":")}'")
        shell("settings put secure accessibility_enabled 1")
        waitFor("Real accessibility service not connected") { AppControlService.connected != null }
        consentScreen()
        val fixtureMonitor = android.app.Instrumentation.ActivityMonitor(CapabilityFixtureActivity::class.java.name, null, false)
        instrumentation.addMonitor(fixtureMonitor)
        var fixture: android.app.Activity? = null
        try {
            compose.runOnIdle { compose.activity.startActivity(Intent(compose.activity, CapabilityFixtureActivity::class.java)) }
            fixture = instrumentation.waitForMonitorWithTimeout(fixtureMonitor, 10_000)
            assertNotNull(fixture)
            instrumentation.runOnMainSync { requireNotNull(fixture).window.decorView.setBackgroundColor(android.graphics.Color.rgb(30, 140, 60)) }
            waitFor("Selected synthetic app not foreground") { AppControlService.connected?.selectedPackage() == context.packageName }
            val handler = android.os.Handler(android.os.Looper.getMainLooper())
            val animate = object : Runnable { override fun run() {
                fixture?.findViewById<android.widget.TextView>(R.id.capability_fixture_result)?.text = "Synthetic frame ${SystemClock.elapsedRealtime()}"
                handler.postDelayed(this, 40)
            } }
            handler.post(animate)
            try {
                NativeCapabilities(context, true) { it == approved }.use { native ->
                    native.gate.foreground(true)
                    assertEquals("blocked", native.execute(context, action(native, "android.screen.capture")).state)
                    var frame: NativeResult? = null
                    waitFor("No fresh authorized selected-app frame") {
                        val capture = action(native, "android.screen.capture"); approved = capture
                        frame = native.execute(context, capture)
                        frame!!.observations.isNotEmpty()
                    }
                    assertEquals("reported", frame!!.state)
                    val image = JSONObject(frame!!.observations.single().text)
                    assertEquals("image/jpeg", image.getString("mime"))
                    val bytes = android.util.Base64.decode(image.getString("base64"), android.util.Base64.DEFAULT)
                    val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                    assertNotNull(bitmap); assertEquals(256, bitmap.width)
                    val pixel = bitmap.getPixel(bitmap.width / 2, bitmap.height / 2)
                    assertTrue("Captured frame did not contain the selected synthetic app", android.graphics.Color.green(pixel) > 100 && android.graphics.Color.red(pixel) < 60 && android.graphics.Color.blue(pixel) < 90)
                    bitmap.recycle()
                    val cancelled = action(native, "android.screen.capture"); approved = cancelled; native.cancel(cancelled.requestId)
                    assertEquals("blocked", native.execute(context, cancelled).state)
                    compose.activity.stopService(Intent(context, NativeScreenService::class.java))
                    waitFor("Screen service survived stop") { NativeScreenService.current == null }
                    val stopped = action(native, "android.screen.capture"); approved = stopped
                    assertEquals("blocked", native.execute(context, stopped).state)
                }
            } finally { handler.removeCallbacks(animate) }
            instrumentation.runOnMainSync { requireNotNull(fixture).finish() }; fixture = null
            consentScreen()
            shell("input keyevent KEYCODE_SLEEP")
            waitFor("Screen sharing survived OS screen-off") { NativeScreenService.current == null }
            assertFalse(NativePlatform(context).available("android.screen.capture"))
        } finally {
            shell("input keyevent KEYCODE_WAKEUP"); shell("wm dismiss-keyguard")
            context.stopService(Intent(context, NativeScreenService::class.java))
            fixture?.let { activity -> instrumentation.runOnMainSync { activity.finish() } }
            instrumentation.removeMonitor(fixtureMonitor)
            prefs.edit().putBoolean("screen_perception", false).putBoolean("accessibility_perception", false).putString("native_action_packages", "").commit()
        }
    }
}
