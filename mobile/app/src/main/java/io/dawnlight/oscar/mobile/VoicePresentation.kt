package io.dawnlight.oscar.mobile
import android.content.Context
import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class VoicePhase { IDLE, STARTING, LISTENING, SPEAKING, MUTED, UNAVAILABLE, FAILED }
data class VoiceStatus(val epoch: Long = 0, val phase: VoicePhase = VoicePhase.IDLE, val detail: String = "Microphone off") {
    fun admitted(token: Long, next: VoicePhase, message: String) = if (token == epoch) copy(
        epoch = if (next in setOf(VoicePhase.IDLE, VoicePhase.MUTED, VoicePhase.UNAVAILABLE, VoicePhase.FAILED)) epoch + 1 else epoch,
        phase = next, detail = message) else this
    fun admitsCapture(token: Long, ownerStarted: Boolean, permitted: Boolean, bound: Boolean) =
        token == epoch && phase == VoicePhase.STARTING && ownerStarted && permitted && bound
}
/** Existing native adapter presentation; Core owns recognition and continuity. */
object VoicePresentation {
    private val mutable = MutableStateFlow(VoiceStatus())
    val state = mutable.asStateFlow()
    @JvmStatic @Synchronized fun begin(): Long {
        mutable.value = VoiceStatus(mutable.value.epoch + 1, VoicePhase.STARTING, "Waiting for Android audio service")
        return mutable.value.epoch
    }
    @JvmStatic @Synchronized fun report(token: Long, phase: VoicePhase, detail: String) {
        mutable.value = mutable.value.admitted(token, phase, detail)
    }
    @JvmStatic @Synchronized fun invalidate() { mutable.value = VoiceStatus(mutable.value.epoch + 1) }
    @JvmStatic @Synchronized fun admitsCapture(token: Long, ownerStarted: Boolean, permitted: Boolean, bound: Boolean) =
        mutable.value.admitsCapture(token, ownerStarted, permitted, bound)
    @JvmStatic @Synchronized fun current(token: Long) = token == mutable.value.epoch
    fun cancel(context: Context) {
        invalidate(); context.stopService(Intent(context, MicrophoneService::class.java))
    }
    fun start(context: Context) {
        cancel(context)
        val token = begin()
        if (!NativeVoice.permitted(context)) report(token, VoicePhase.MUTED, "Microphone permission or OSCAR perception grant is off")
        else if (MicrophoneService.binding == null) report(token, VoicePhase.UNAVAILABLE, "Android Voice Core binding is unavailable")
        else try {
            context.startForegroundService(Intent(context, MicrophoneService::class.java).putExtra("owner_started", true).putExtra("voice_epoch", token))
        } catch (_: Exception) { report(token, VoicePhase.FAILED, "Android could not start capture. Continue with text.") }
    }
}
@Composable fun VoiceExperience(state: MobileState, privacy: () -> Unit) {
    val context = LocalContext.current
    val status by VoicePresentation.state.collectAsStateWithLifecycle()
    val capturing = status.phase in setOf(VoicePhase.STARTING, VoicePhase.LISTENING, VoicePhase.SPEAKING)
    val microphoneActive = status.phase in setOf(VoicePhase.LISTENING, VoicePhase.SPEAKING)
    val phaseColor = when (status.phase) {
        VoicePhase.LISTENING, VoicePhase.SPEAKING -> Sage
        VoicePhase.STARTING -> Amber
        VoicePhase.MUTED, VoicePhase.UNAVAILABLE, VoicePhase.FAILED -> Clay
        VoicePhase.IDLE -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    Column(Modifier.fillMaxWidth().padding(top = 16.dp, bottom = 16.dp), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(20.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp, androidx.compose.ui.Alignment.CenterHorizontally),
            verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            Glyph(when (status.phase) { VoicePhase.STARTING -> "Clock"; VoicePhase.SPEAKING -> "Play"; else -> "Voice" }, color = phaseColor)
            Text(status.detail, style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.weight(1f, fill = false).testTag("voiceStatus").semantics { liveRegion = LiveRegionMode.Polite; stateDescription = status.phase.name })
        }
        Box(Modifier.fillMaxWidth().height(232.dp), contentAlignment = androidx.compose.ui.Alignment.Center) {
            OscarOrb(state, size = 200.dp)
        }
        Text(when (status.phase) {
            VoicePhase.LISTENING -> "I'm listening."
            VoicePhase.SPEAKING -> "A thought, aloud."
            VoicePhase.STARTING -> "One moment."
            VoicePhase.MUTED -> "On your terms."
            VoicePhase.UNAVAILABLE -> "Here when it's ready."
            VoicePhase.FAILED -> "Let's try another way."
            VoicePhase.IDLE -> "A little more present."
        }, style = MaterialTheme.typography.headlineLarge, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp, androidx.compose.ui.Alignment.CenterHorizontally),
            verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Surface(shape = androidx.compose.foundation.shape.RoundedCornerShape(20.dp), color = MaterialTheme.colorScheme.surfaceContainer,
                border = androidx.compose.foundation.BorderStroke(0.7.dp, phaseColor.copy(alpha = 0.45f))) {
                Row(Modifier.padding(horizontal = 14.dp, vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Glyph("Voice", color = phaseColor)
                    Text(if (microphoneActive) "Mic active" else if (status.phase == VoicePhase.STARTING) "Mic starting" else "Mic off",
                        style = MaterialTheme.typography.labelLarge)
                }
            }
            Surface(shape = androidx.compose.foundation.shape.RoundedCornerShape(20.dp), color = MaterialTheme.colorScheme.surfaceContainer,
                border = androidx.compose.foundation.BorderStroke(0.7.dp, MaterialTheme.colorScheme.outlineVariant)) {
                Row(Modifier.padding(horizontal = 14.dp, vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Glyph("Shield", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text("Raw audio not saved", style = MaterialTheme.typography.labelLarge)
                }
            }
        }
        if (!capturing) Text("Opening Voice does not record.", style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
    if (capturing) OscarButton(onClick = { VoicePresentation.cancel(context) }, modifier = Modifier.fillMaxWidth(), color = Clay) {
        Glyph("Close", color = androidx.compose.ui.graphics.Color.White); Text("Stop microphone and speech")
    } else OscarButton(onClick = { VoicePresentation.start(context) }, modifier = Modifier.fillMaxWidth()) {
        Glyph("Voice", color = androidx.compose.ui.graphics.Color.White); Text("Start listening")
    }
    TextButton(onClick = privacy) { Text("Microphone permissions") }
    SupportingDetails("Voice & enrollment details") {
        Text("Listening requires Android permission, your OSCAR grant and completed voice setup.", style = MaterialTheme.typography.bodySmall)
        Text("Playback and enrollment are unavailable. Voice recognition never authorizes an action.", style = MaterialTheme.typography.bodySmall)
    }
}
