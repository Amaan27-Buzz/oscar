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
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.selection.selectable
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.selected
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
    val theme = appearancePreference("theme", "system")
    PreferenceGroup("Theme") {
        BoxWithConstraints(Modifier.fillMaxWidth()) {
            val tileWidth = if (LocalDensity.current.fontScale > 1.3f) maxWidth else (maxWidth - 20.dp) / 3
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("system", "light", "dark").forEach { option ->
                    Surface(onClick = { context.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("theme",option).apply() },
                        modifier = Modifier.width(tileWidth).testTag("theme-$option").semantics { selected = theme == option; role = Role.RadioButton },
                        shape = RoundedCornerShape(18.dp), color = MaterialTheme.colorScheme.surface,
                        border = BorderStroke(if (theme == option) 2.dp else 1.dp, if (theme == option) Sage else MaterialTheme.colorScheme.outlineVariant)) {
                        Column(Modifier.padding(10.dp), horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Canvas(Modifier.fillMaxWidth().height(86.dp).clip(RoundedCornerShape(12.dp))) {
                                val paper = Color(0xFFF5F1E7); val graphite = Color(0xFF242723)
                                drawRoundRect(if (option == "dark") graphite else paper, cornerRadius = androidx.compose.ui.geometry.CornerRadius(8.dp.toPx()))
                                if (option == "system") drawRect(graphite, topLeft = androidx.compose.ui.geometry.Offset(size.width / 2, 0f), size = androidx.compose.ui.geometry.Size(size.width / 2, size.height))
                                val stroke = if (option == "dark") paper else Color(0xFF526C56)
                                val inset = 8.dp.toPx()
                                drawCircle(Clay, 5.dp.toPx(), androidx.compose.ui.geometry.Offset(inset + 5.dp.toPx(), size.height * 0.2f))
                                drawLine(stroke, androidx.compose.ui.geometry.Offset(inset, size.height * 0.39f), androidx.compose.ui.geometry.Offset(size.width * 0.72f, size.height * 0.39f), 3.dp.toPx())
                                drawRoundRect(Powder.copy(alpha = 0.65f), androidx.compose.ui.geometry.Offset(inset, size.height * 0.5f),
                                    androidx.compose.ui.geometry.Size((size.width - inset * 2).coerceAtLeast(0f), size.height * 0.18f), androidx.compose.ui.geometry.CornerRadius(4.dp.toPx()))
                                drawRoundRect(Sage, androidx.compose.ui.geometry.Offset(inset, size.height * 0.8f),
                                    androidx.compose.ui.geometry.Size(size.width * 0.25f, 4.dp.toPx()), androidx.compose.ui.geometry.CornerRadius(2.dp.toPx()))
                            }
                            Text(option.replaceFirstChar { it.uppercase() }, style = MaterialTheme.typography.labelLarge)
                        }
                    }
                }
            }
        }
    }
    PreferenceGroup("Comfort") {
        PreferenceControl("Reduce OSCAR motion", "Calmer movement and transitions.", "Leaf") {
            OscarSwitch(reduced, { context.getSharedPreferences("appearance", Context.MODE_PRIVATE).edit().putString("motion", if (it) "reduced" else "system").apply() }, modifier = Modifier.semantics { contentDescription = "Reduce OSCAR motion" })
        }
        HorizontalDivider()
        PreferenceValue("Text size", "Follows Android")
    }
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
    PreferenceGroup("Expression preview") {
        Box(Modifier.fillMaxWidth().height(164.dp), contentAlignment = androidx.compose.ui.Alignment.Center) {
            Box(Modifier.size(144.dp).background(Powder.copy(alpha = 0.45f), CircleShape))
            ExpressionPresence(event,source,120.dp,true)
        }
        StatusLabel("Preview only · not applied to OSCAR")
    }
    PreferenceGroup("Delivery") {
        listOf("composed" to "Steady and considered", "curious" to "Attentive and interested", "amused" to "A lighter touch", "subdued" to "Quiet and reserved").forEachIndexed { index, (cue, detail) ->
            if (index > 0) HorizontalDivider()
            Row(Modifier.fillMaxWidth().heightIn(min = 64.dp).selectable(selected = delivery == cue, role = Role.RadioButton, onClick = { delivery = cue }), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                IconBadge(when (cue) { "curious" -> "Sun"; "amused" -> "Persona"; "subdued" -> "Moon"; else -> "Leaf" },
                    when (cue) { "curious" -> Color(0xFFE7AD3B); "amused" -> Clay; "subdued" -> Lilac; else -> Sage }, 40.dp)
                Column(Modifier.weight(1f)) { Text(cue.replaceFirstChar { it.uppercase() }, style = MaterialTheme.typography.titleMedium); Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                RadioButton(selected = delivery == cue, onClick = null, colors = RadioButtonDefaults.colors(selectedColor = Sage))
            }
        }
    }
    SupportingDetails("About this preview") { Text("These expressions are temporary. Persona settings are managed by Core and cannot change facts, safety or permissions.", style = MaterialTheme.typography.bodySmall) }
}
@Composable fun DiagnosticsSettings(state: MobileState) {
    PreferenceGroup("Connection") {
        PreferenceValue("Core", state.link.name.lowercase().replaceFirstChar { it.uppercase() })
        HorizontalDivider()
        PreferenceValue("Observation", if (state.observedAt > 0) "Foreground readback" else "Unavailable")
        HorizontalDivider()
        PreferenceValue("Tasks", state.snapshot?.tasks?.size?.toString() ?: "Unavailable")
    }
    PreferenceGroup("App & device") {
        PreferenceValue("OSCAR", BuildConfig.VERSION_NAME)
        HorizontalDivider()
        PreferenceValue("Android", "${android.os.Build.VERSION.RELEASE} · API ${android.os.Build.VERSION.SDK_INT}")
    }
    SupportingDetails("Runtime information") {
        Text("Model routing is managed by Core. Device capabilities reflect the current connection. Background push is unavailable.", style = MaterialTheme.typography.bodySmall)
        Text("No tokens, private prompts, notification content or voice profiles are displayed or exported.", style = MaterialTheme.typography.bodySmall)
    }
}
