package io.dawnlight.oscar.mobile

import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Actual native frame progression and immediate reduced-motion behavior, no runtime fixtures. */
class MotionProofTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun entryFramesProgressAndReducedMotionIsImmediate() {
        org.junit.Assume.assumeTrue(allowDisposableReview())
        compose.mainClock.autoAdvance = false
        val reduced = mutableStateOf(false)
        val page = mutableIntStateOf(0)
        compose.runOnIdle {
            compose.activity.window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE)
            compose.activity.setContent {
                CompositionLocalProvider(LocalReducedMotion provides reduced.value) {
                    Surface(color = Color.White) {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Box(Modifier.size(180.dp).then(pageEntrance(page.intValue)).background(Color.Blue).testTag("motionPanel"))
                        }
                    }
                }
            }
        }
        fun red(): Float {
            val map = compose.onNodeWithTag("motionPanel").captureToImage().toPixelMap()
            return map[map.width / 2, map.height / 2].red
        }
        try {
            compose.mainClock.advanceTimeBy(16)
            val early = red()
            compose.mainClock.advanceTimeBy(96)
            val middle = red()
            compose.mainClock.advanceTimeBy(200)
            val settled = red()
            assertTrue("Entry must have intermediate native frames", early > middle && middle > settled)
            assertTrue("Entry must settle", settled < 0.02f)
            compose.runOnIdle { reduced.value = true; page.intValue++ }
            compose.mainClock.advanceTimeByFrame()
            assertTrue("Reduced motion must render immediately", red() < 0.02f)
            captureReview(compose, "motion-reduced-frame", "motionPanel")
        } finally {
            compose.mainClock.autoAdvance = true
            compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) }
        }
    }
}
