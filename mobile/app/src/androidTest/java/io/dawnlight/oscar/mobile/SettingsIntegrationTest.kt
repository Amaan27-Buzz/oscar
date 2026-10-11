package io.dawnlight.oscar.mobile

import android.content.Context

import androidx.activity.compose.setContent

import androidx.compose.ui.test.*

import androidx.compose.ui.test.junit4.createAndroidComposeRule

import org.junit.Rule

import org.junit.Test

import org.junit.Assert.*

import org.junit.After

import androidx.compose.ui.graphics.asAndroidBitmap



class SettingsIntegrationTest {

    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    @After fun cleanup() { compose.activity.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().clear().commit() }

    private fun page(name: String) {

        compose.onNodeWithText("Settings").performClick()

        compose.onNodeWithText(name).performScrollTo().performClick()

    }

    private fun capture(name: String) {

        compose.runOnIdle { compose.activity.window.clearFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) }

        try {

            compose.waitForIdle()
            val bitmap = if (name.contains("ime")) androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().uiAutomation.takeScreenshot()!!
                else compose.onRoot().captureToImage().asAndroidBitmap()

            val uri = compose.activity.contentResolver.insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, android.content.ContentValues().apply {

                put(android.provider.MediaStore.Images.Media.DISPLAY_NAME, "$name.png")

                put(android.provider.MediaStore.Images.Media.MIME_TYPE,"image/png")

                put(android.provider.MediaStore.Images.Media.RELATIVE_PATH,"Pictures/OSCAR-Group02")

            })!!

            compose.activity.contentResolver.openOutputStream(uri)!!.use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,it) }

        } finally { compose.runOnIdle { compose.activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE) } }

    }

    @Test fun personaIsBoundedAndDoesNotChangeCorePolicy() {

        page("Persona")

        compose.onNodeWithText("SIMULATED · bounded expression preview.", substring=true).assertExists()

        compose.onNodeWithText("Amused").performScrollTo().performClick()

        compose.onAllNodesWithContentDescription("OSCAR expression").assertCountEquals(2)

        assertFalse(compose.activity.getSharedPreferences("appearance",Context.MODE_PRIVATE).contains("persona"))

        capture("13-7-persona-preview-simulated")

        compose.onNodeWithText("Back to Settings").performScrollTo().performClick()

        compose.onNodeWithText("Platform").performScrollTo().performClick()

        compose.onNodeWithText("Overlay · unavailable",substring=true).assertExists()

        capture("13-7-platform-reference")

    }

    @Test fun reducedMotionPersistsThroughActivityRecreation() {

        page("Accessibility")

        compose.onNodeWithContentDescription("Reduce OSCAR motion").performClick()

        compose.waitUntil(5000) { compose.activity.getSharedPreferences("appearance",Context.MODE_PRIVATE).getString("motion","") == "reduced" }

        compose.activityRule.scenario.recreate()

        compose.onNodeWithContentDescription("Reduce OSCAR motion").assertIsOn()

        capture("13-7-accessibility-reference")

    }

}

