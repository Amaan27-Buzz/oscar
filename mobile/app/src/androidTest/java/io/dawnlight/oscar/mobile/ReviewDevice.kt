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
        val target = if (tag != null) compose.onNodeWithTag(tag)
            else if (compose.onAllNodes(isDialog()).fetchSemanticsNodes().size == 1) compose.onNode(isDialog())
            else compose.onRoot()
        val bitmap = target.captureToImage().asAndroidBitmap()
        val directory = File(compose.activity.filesDir, "group25b").apply { mkdirs() }
        File(directory, "$name.png").outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, it) }
    } finally {
        compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) }
    }
}

/** Follow the same single-Back navigation available to a person using the app. */
internal fun navigateReview(compose: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>, destination: String) {
    repeat(4) {
        if (compose.onAllNodesWithTag("destination-$destination").fetchSemanticsNodes().isNotEmpty()) {
            compose.onNodeWithTag("destination-$destination").performClick()
            return
        }
        compose.onNodeWithTag("page-back").performClick()
    }
    error("Destination not reachable: $destination")
}
internal fun closeReviewDetail(compose: AndroidComposeTestRule<ActivityScenarioRule<MainActivity>, MainActivity>, tag: String) {
    compose.onNode(hasContentDescription("Back") and hasAnyAncestor(hasTestTag(tag))).performClick()
}
