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
    Text("Theme", style = MaterialTheme.typography.titleMedium)
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
    Text("Reduces movement and transitions. Text follows your Android font size.")
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
    StatusLabel("Preview only · not applied to OSCAR")
    Box(Modifier.fillMaxWidth(), contentAlignment = androidx.compose.ui.Alignment.Center) { ExpressionPresence(event,source,80.dp,true) }
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf("composed","curious","amused","subdued").forEach { cue -> FilterChip(selected = delivery == cue, onClick = { delivery = cue }, label = { Text(cue.replaceFirstChar { it.uppercase() }) }) }
    }
    SupportingDetails("About this preview") { Text("These expressions are temporary. Persona settings are managed by Core and cannot change facts, safety or permissions.", style = MaterialTheme.typography.bodySmall) }
}
@Composable fun DiagnosticsSettings(state: MobileState) {
    Text("Core connection · ${state.link}")
    Text("Observation · ${if (state.observedAt > 0) "Foreground readback" else "Unavailable"}")
    Text("Task count · ${state.snapshot?.tasks?.size?.toString() ?: "Unavailable"}")
    Text("Android ${android.os.Build.VERSION.RELEASE} / API ${android.os.Build.VERSION.SDK_INT}")
    Text("OSCAR Mobile ${BuildConfig.VERSION_NAME}")
    Text("No tokens, private prompts, notification content or voice profiles are displayed or exported.")
    SupportingDetails("Runtime information") {
        Text("Model routing is managed by Core. Device capabilities reflect the current connection. Background push is unavailable.", style = MaterialTheme.typography.bodySmall)
    }
}
