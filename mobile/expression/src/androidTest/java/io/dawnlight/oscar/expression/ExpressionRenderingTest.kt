package io.dawnlight.oscar.expression

import android.graphics.Bitmap
import androidx.activity.ComponentActivity
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.io.File
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test

/** Isolated emulated fixtures only. This activity never binds Core or owner capabilities. */
class ExpressionRenderingTest {
    @get:Rule val compose = createAndroidComposeRule<ComponentActivity>()
    private val source = Source(SourceKind.FIXTURE,"emulator-expression")
    private fun data() = MotionData(compose.activity.assets.open("motion-v1.json").bufferedReader().use { it.readText() })
    @Test fun nativeFixtureAtlasAndCompactSizes() {
        val data = data()
        val fixtures = JSONObject(javaClass.classLoader!!.getResourceAsStream("reference-v1.json")?.bufferedReader()?.use { it.readText() }
            ?: androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().context.assets.open("reference-v1.json").bufferedReader().use { it.readText() })
        val cases=fixtures.getJSONArray("poseCases")
        compose.setContent {
            Column(Modifier.background(Color(0xFFF7F7F3)).padding(12.dp).testTag("atlas")) {
                BasicText("OSCAR shared expression / EMULATED FIXTURES",style=TextStyle(fontSize=14.sp,color=Color(0xFF222923)))
                BasicText("SIMULATED VISUAL STATE — NO CORE EXECUTION",style=TextStyle(fontSize=10.sp,color=Color(0xFF59625B)))
                for(row in 0..7)Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceEvenly) {
                    for(column in 0..1) {
                        val fixture=cases.getJSONObject(row*2+column);val scene=fixture.getJSONObject("scene")
                        val (pose,r)=data.sample(data.study(data.canonical,Scene(scene.getString("operation"),scene.getString("delivery"))),fixture.getDouble("at"),reduced=fixture.getBoolean("reduced"))
                        Column(Modifier.padding(4.dp)) {
                            ExpressionOrb(ExpressionSnapshot(pose,r,source,0,AnimationPhase.HELD,false,null,EffectivePriority.DELIVERY),58.dp)
                            BasicText(fixture.getString("name"),style=TextStyle(fontSize=10.sp,color=Color(0xFF222923)))
                        }
                    }
                }
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                    for(size in listOf(32,48,64,96))ExpressionOrb(ExpressionSnapshot(data.canonical,data.resolve(Scene("idle","composed")),source,0,AnimationPhase.HELD,false,null,EffectivePriority.DELIVERY),size.dp)
                }
            }
        }
        compose.onAllNodesWithContentDescription("OSCAR expression").assertCountEquals(20)
        compose.waitUntil(timeoutMillis=10_000) { compose.activity.hasWindowFocus() }
        compose.waitForIdle()
        val image=compose.onNodeWithTag("atlas").captureToImage().asAndroidBitmap()
        val file=File(compose.activity.getExternalFilesDir(null),"expression-native-atlas.png")
        file.outputStream().use { assertTrue(image.compress(Bitmap.CompressFormat.PNG,100,it)) }
        androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().uiAutomation.executeShellCommand("cp ${file.absolutePath} /data/local/tmp/oscar-expression-atlas.png").use { descriptor ->
            android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).use { it.readBytes() }
        }
        assertTrue(image.width>100);assertTrue(image.height>100)
    }
    private fun event(generation:Long,operation:String="speaking",muted:Boolean=false):String {
        val now=System.currentTimeMillis()
        return JSONObject().put("version",1).put("source",JSONObject().put("kind","fixture").put("id",source.id)).put("generation",generation).put("transitionId","event-$generation")
            .put("eventTime",now).put("expiresAt",now+30000).put("kind","state").put("priority","normal").put("operation",operation).put("delivery","composed")
            .put("availability","available").put("muted",muted).put("attention","none").put("reducedMotion",true).toString()
    }
    @Test fun lifecycleAndNewMuteGenerationCannotResumeStaleSpeech() {
        var raw by mutableStateOf(event(1))
        compose.setContent { ExpressionPresence(raw,source,96.dp,reducedMotion=true,modifier=Modifier.testTag("live")) }
        compose.onNodeWithTag("live").assert(SemanticsMatcher.expectValue(SemanticsProperties.StateDescription,"SIMULATED — speaking. composed delivery."))
        compose.activityRule.scenario.moveToState(androidx.lifecycle.Lifecycle.State.CREATED)
        compose.activityRule.scenario.moveToState(androidx.lifecycle.Lifecycle.State.RESUMED)
        compose.onNodeWithTag("live").assert(SemanticsMatcher.expectValue(SemanticsProperties.StateDescription,"SIMULATED — unknown. hesitant delivery."))
        compose.runOnIdle { raw=event(2,"listening",true) }
        compose.onNodeWithTag("live").assert(SemanticsMatcher.expectValue(SemanticsProperties.StateDescription,"SIMULATED — muted. composed delivery."))
        assertEquals(android.content.pm.PackageManager.PERMISSION_DENIED,compose.activity.checkSelfPermission(android.Manifest.permission.RECORD_AUDIO))
    }
    @Test fun nativeJsonAdmissionRejectsLenientAndroidSyntax() {
        val encoded=event(1)
        for(raw in listOf(encoded+" trailing garbage",encoded.replace("\"version\":","version:"),encoded.replace('"','\'')))assertNull(Contract.validate(raw,System.currentTimeMillis()))
        assertNotNull(Contract.validate(encoded,System.currentTimeMillis()))
        val rawFixtures=androidx.test.platform.app.InstrumentationRegistry.getInstrumentation().context.assets.open("reference-v1.json").bufferedReader().use { it.readText() }
        val cases=JSONObject(rawFixtures).getJSONArray("malformedInputs")
        for(i in 0 until cases.length()) { val fixture=cases.getJSONObject(i);assertNull(fixture.getString("name"),Contract.validate(fixture.getString("raw"),1000000)) }
    }
}
