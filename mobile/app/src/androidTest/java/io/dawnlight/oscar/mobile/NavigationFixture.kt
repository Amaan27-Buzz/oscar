package io.dawnlight.oscar.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeContentTestRule

/** Native contextual navigation; destination selection is no longer always on screen. */
internal fun ComposeContentTestRule.openDestination(name: String) {
    onNodeWithTag("navigation").performClick()
    onNodeWithTag("destination-${name.uppercase()}").performClick()
}
