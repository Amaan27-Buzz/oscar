package io.dawnlight.oscar.mobile

import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.AndroidComposeTestRule
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File

/** Real-phone fixture runs require an explicit opt-in and an isolated app identity. */
internal fun allowDisposableReview() = android.os.Build.HARDWARE in setOf("ranchu", "goldfish") ||
    (BuildConfig.APPLICATION_ID == "io.dawnlight.oscar.mobile.review" &&
        InstrumentationRegistry.getArguments().getString("oscar_review_device") == "true")

internal fun captureReview(compose: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>, name: String, tag: String? = null) {
    compose.runOnIdle { compose.activity.window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) }
    try {
        compose.waitForIdle()
        val bitmap = (if (tag == null) compose.onRoot() else compose.onNodeWithTag(tag)).captureToImage().asAndroidBitmap()
        val directory = File(compose.activity.filesDir, "group25b").apply { mkdirs() }
        File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
    } finally {
        compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) }
    }
}
