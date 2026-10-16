package io.dawnlight.oscar.mobile

import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

class NavigationMotionTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun prepare() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
        compose.mainClock.autoAdvance = false
    }
    @Test fun anchoredMarkerTravelsRetargetsAndSnapsForReducedMotion() {
        prepare()
        val selected = mutableStateOf(Destination.OSCAR)
        val reduced = mutableStateOf(false)
        val enlargedRtl = mutableStateOf(false)
        compose.runOnIdle {
            compose.activity.setContent {
                OscarTheme {
                    CompositionLocalProvider(LocalReducedMotion provides reduced.value,
                        LocalDensity provides Density(LocalDensity.current.density, if (enlargedRtl.value) 1.8f else 1f),
                        LocalLayoutDirection provides if (enlargedRtl.value) LayoutDirection.Rtl else LayoutDirection.Ltr) {
                        Surface {
                            Column(Modifier.fillMaxSize()) {
                                Spacer(Modifier.weight(1f))
                                PrimaryNavigation(selected.value) { selected.value = it }
                            }
                        }
                    }
                }
            }
        }
        fun marker() = compose.onNodeWithTag("navigation-marker").fetchSemanticsNode().boundsInRoot
        fun target(name: String) = compose.onNodeWithTag("destination-$name").fetchSemanticsNode().boundsInRoot.center.x
        try {
            compose.mainClock.advanceTimeBy(1000)
            val root = compose.onRoot().fetchSemanticsNode().boundsInRoot
            val bar = compose.onNodeWithTag("primary-navigation").fetchSemanticsNode().boundsInRoot
            assertEquals("Bar stays full-width", root.width, bar.width, 1f)
            assertEquals("Bar remains attached to the bottom", root.bottom, bar.bottom, 1f)
            val start = marker()
            captureReview(compose, "nav-motion-start", "primary-navigation")
            compose.onNodeWithTag("destination-ACTIVITY").performClick()
            for (frame in 1..3) {
                compose.mainClock.advanceTimeBy(32)
                captureReview(compose, "nav-frame-${frame * 32}", "primary-navigation")
            }
            val middle = marker()
            compose.onNodeWithTag("destination-ACTIVITY").assertIsSelected()
            assertTrue("Selection has intermediate positions", middle.center.x > start.center.x && middle.center.x < target("ACTIVITY"))
            assertTrue("Leading edge stretches the marker during travel", middle.width > start.width + 1f)
            captureReview(compose, "nav-motion-travel", "primary-navigation")
            for (frame in 4..10) {
                compose.mainClock.advanceTimeBy(32)
                captureReview(compose, "nav-frame-${frame * 32}", "primary-navigation")
            }
            compose.mainClock.advanceTimeBy(680)
            assertEquals(target("ACTIVITY"), marker().center.x, 1f)
            captureReview(compose, "nav-motion-end", "primary-navigation")
            compose.onNodeWithTag("destination-OSCAR").performClick()
            compose.mainClock.advanceTimeBy(64)
            compose.onNodeWithTag("destination-AUTOMATIONS").performClick()
            compose.mainClock.advanceTimeBy(1000)
            compose.onNodeWithTag("destination-AUTOMATIONS").assertIsSelected()
            assertEquals("Interrupted travel settles on the latest selection", target("AUTOMATIONS"), marker().center.x, 1f)
            captureReview(compose, "nav-motion-settled", "primary-navigation")
            compose.runOnIdle { reduced.value = true; selected.value = Destination.ACTIVITY }
            compose.mainClock.advanceTimeByFrame()
            assertEquals("Reduced motion snaps immediately", target("ACTIVITY"), marker().center.x, 1f)
            compose.runOnIdle { enlargedRtl.value = true }
            compose.mainClock.advanceTimeBy(64)
            assertEquals("Marker follows actual RTL layout bounds", target("ACTIVITY"), marker().center.x, 1f)
            for (label in listOf("Conversation", "Automations", "Activity")) {
                val layouts = mutableListOf<androidx.compose.ui.text.TextLayoutResult>()
                compose.onNodeWithText(label, useUnmergedTree = true).performSemanticsAction(androidx.compose.ui.semantics.SemanticsActions.GetTextLayoutResult) { it(layouts) }
                assertFalse("$label fits at 1.8x in RTL", layouts.single().isLineEllipsized(0))
            }
            captureReview(compose, "nav-large-rtl", "primary-navigation")
        } finally { compose.mainClock.autoAdvance = true }
    }

    @Test fun activityFilterMovesWithoutRetainingPreviousTaskContent() {
        prepare()
        val reduced = mutableStateOf(false)
        val tasks = listOf(
            CoreTask("active-motion", "Synthetic active request", "planned", "Core", "online", 1, emptyList(), emptyList(), null, null),
            CoreTask("finished-motion", "Synthetic finished request", "verified", "Core", "online", 1, emptyList(), listOf("fixture"), "5", null))
        compose.runOnIdle { compose.activity.setContent {
            OscarTheme(preferDark = true) {
                CompositionLocalProvider(LocalReducedMotion provides reduced.value) {
                    Surface { Column(Modifier.fillMaxSize().padding(24.dp)) {
                        ActivityScreen(MobileState(link = Link.CONNECTED, snapshot = CoreSnapshot(tasks, emptyList(), System.currentTimeMillis())), {}, { _, _ -> })
                    } }
                }
            }
        } }
        fun x() = compose.onNodeWithTag("activity-filter-marker").fetchSemanticsNode().boundsInRoot.center.x
        try {
            compose.mainClock.advanceTimeBy(1000)
            val start = x()
            compose.onNodeWithTag("activity-filter-Finished").performClick()
            compose.mainClock.advanceTimeBy(80)
            compose.onNodeWithTag("activity-filter-Finished").assertIsSelected()
            compose.onNodeWithTag("task-description-${tasks[0].id}").assertDoesNotExist()
            compose.onNodeWithTag("task-description-${tasks[1].id}").assertExists()
            val end = compose.onNodeWithTag("activity-filter-Finished").fetchSemanticsNode().boundsInRoot.center.x
            assertTrue("Filter marker has intermediate frames", x() > start && x() < end)
            captureReview(compose, "activity-filter-travel")
            compose.mainClock.advanceTimeBy(1000)
            assertEquals(end, x(), 1f)
            captureReview(compose, "activity-filter-settled")
            compose.runOnIdle { reduced.value = true }
            compose.onNodeWithTag("activity-filter-Active").performClick()
            compose.mainClock.advanceTimeByFrame()
            assertEquals(start, x(), 1f)
            compose.onNodeWithTag("task-description-${tasks[1].id}").assertDoesNotExist()
        } finally { compose.mainClock.autoAdvance = true }
    }
}
