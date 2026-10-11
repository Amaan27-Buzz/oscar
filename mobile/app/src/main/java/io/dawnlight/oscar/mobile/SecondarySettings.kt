package io.dawnlight.oscar.mobile
import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import io.dawnlight.oscar.expression.ExpressionPresence
import io.dawnlight.oscar.expression.Source
import io.dawnlight.oscar.expression.SourceKind
import org.json.JSONObject

val LocalReducedMotion = compositionLocalOf { false }
@Composable fun appearancePreference(key: String, fallback: String): String {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("appearance", Context.MODE_PRIVATE) }
    var value by remember { mutableStateOf(prefs.getString(key, fallback) ?: fallback) }
    DisposableEffect(prefs, key) {
        val changes = android.content.SharedPreferences.OnSharedPreferenceChangeListener { _, name -> if (name == key) value = prefs.getString(key, fallback) ?: fallback }
        prefs.registerOnSharedPreferenceChangeListener(changes)
        onDispose { prefs.unregisterOnSharedPreferenceChangeListener(changes) }
    }
    return value
}
@Composable fun AppearanceSettings() {
    val context = LocalContext.current
    val reduced = appearancePreference("motion", "system") == "reduced"
    Text("Appearance & accessibility", style = MaterialTheme.typography.titleLarge)
    val theme = appearancePreference("theme", "system")
    listOf("system", "light", "dark").forEach { option ->
        TextButton(onClick = { context.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("theme",option).apply() }) {
            Text("${option.replaceFirstChar { it.uppercase() }}${if (theme == option) " · selected" else ""}")
        }
    }
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("Reduce OSCAR motion", Modifier.weight(1f))
        Switch(reduced, { context.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("motion", if (it) "reduced" else "system").apply() }, modifier = Modifier.semantics { contentDescription = "Reduce OSCAR motion" })
    }
    Text("Uses held expressions and immediate state changes. Android's animation scale remains respected. Text follows your Android font size.")
}
@Composable fun PersonaPreview() {
    var delivery by remember { mutableStateOf("composed") }
    val source = remember { Source(SourceKind.FIXTURE, "persona-preview") }
    val event = remember(delivery) {
        val now = System.currentTimeMillis()
        JSONObject().put("version",1).put("source",JSONObject().put("kind","fixture").put("id",source.id))
            .put("generation",now).put("transitionId","preview-$now").put("eventTime",now).put("expiresAt",now+10000)
            .put("kind","state").put("priority","normal").put("operation","idle").put("delivery",delivery)
            .put("availability","available").put("muted",false).put("attention","none").put("reducedMotion",true).toString()
    }
    Text("Persona preview", style = MaterialTheme.typography.titleLarge)
    Text("SIMULATED · bounded expression preview. Core persona settings are unavailable through this Mobile API; this selection is not saved or applied to OSCAR.")
    Box(Modifier.fillMaxWidth(), contentAlignment = androidx.compose.ui.Alignment.Center) { ExpressionPresence(event,source,80.dp,true) }
    listOf("composed","curious","amused","subdued").forEach { cue -> TextButton(onClick = { delivery = cue }) { Text(cue.replaceFirstChar { it.uppercase() }) } }
    Text("Persona changes delivery, never evidence, safety or permission.")
}
@Composable fun DiagnosticsSettings(state: MobileState) {
    Text("Diagnostics", style = MaterialTheme.typography.titleLarge)
    Text("Core connection · ${state.link}")
    Text("Observation · ${if (state.observedAt > 0) "Foreground readback" else "Unavailable"}")
    Text("Task count · ${state.snapshot?.tasks?.size ?: 0}")
    Text("Android ${android.os.Build.VERSION.RELEASE} / API ${android.os.Build.VERSION.SDK_INT}")
    Text("OSCAR Mobile ${BuildConfig.VERSION_NAME}")
    Text("No tokens, private prompts, notification content or voice profiles are displayed or exported.")
    Text("Model routing and local/cloud execution preferences are controlled by Core. This API does not expose mutable routing policy.")
    Text("Grid preferences: only current advertised nodes/capabilities are shown; local disconnect is in Devices. Background push and full presence runtime belong to Slice 16.")
}
