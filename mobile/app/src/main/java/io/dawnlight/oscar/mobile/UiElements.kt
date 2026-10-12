package io.dawnlight.oscar.mobile

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp

@Composable fun OscarIcon(kind: String) {
    val color = LocalContentColor.current
    Canvas(Modifier.size(24.dp)) {
        val unit = size.width / 24
        fun line(x: Float, y: Float, xx: Float, yy: Float) = drawLine(color, Offset(x * unit, y * unit), Offset(xx * unit, yy * unit), 1.7f * unit)
        when (kind) {
            "menu" -> { line(4f, 7f, 20f, 7f); line(4f, 12f, 20f, 12f); line(4f, 17f, 20f, 17f) }
            "arrow" -> { line(4f, 12f, 20f, 12f); line(14f, 6f, 20f, 12f); line(14f, 18f, 20f, 12f) }
            "back" -> { line(20f, 12f, 4f, 12f); line(10f, 6f, 4f, 12f); line(10f, 18f, 4f, 12f) }
            "activity" -> { drawCircle(color, 8 * unit, Offset(12 * unit, 12 * unit), style = Stroke(1.7f * unit)); line(12f, 7f, 12f, 12f); line(12f, 12f, 17f, 14f) }
            "phone" -> { drawRoundRect(color, Offset(6 * unit, 2 * unit), androidx.compose.ui.geometry.Size(12 * unit, 20 * unit), androidx.compose.ui.geometry.CornerRadius(2 * unit), style = Stroke(1.7f * unit)); line(10f, 18f, 14f, 18f) }
            "desktop" -> { drawRoundRect(color, Offset(3 * unit, 4 * unit), androidx.compose.ui.geometry.Size(18 * unit, 12 * unit), androidx.compose.ui.geometry.CornerRadius(2 * unit), style = Stroke(1.7f * unit)); line(12f, 16f, 12f, 20f); line(7f, 20f, 17f, 20f) }
            "check" -> { line(5f, 12f, 10f, 17f); line(10f, 17f, 20f, 6f) }
            "type" -> { line(4f, 20f, 12f, 4f); line(12f, 4f, 20f, 20f); line(8f, 14f, 16f, 14f) }
            "info" -> { drawCircle(color, 8 * unit, Offset(12 * unit, 12 * unit), style = Stroke(1.7f * unit)); line(12f, 11f, 12f, 17f); drawCircle(color, unit, Offset(12 * unit, 7 * unit)) }
            "sliders" -> { line(4f, 7f, 20f, 7f); line(4f, 17f, 20f, 17f); drawCircle(color, 3 * unit, Offset(8 * unit, 7 * unit), style = Stroke(1.7f * unit)); drawCircle(color, 3 * unit, Offset(16 * unit, 17 * unit), style = Stroke(1.7f * unit)) }
            "stop" -> drawRect(color, Offset(6 * unit, 6 * unit), androidx.compose.ui.geometry.Size(12 * unit, 12 * unit), style = Stroke(1.7f * unit))
            "privacy" -> { val path = androidx.compose.ui.graphics.Path().apply { moveTo(12 * unit, 2 * unit); lineTo(20 * unit, 6 * unit); lineTo(19 * unit, 15 * unit); lineTo(12 * unit, 22 * unit); lineTo(5 * unit, 15 * unit); lineTo(4 * unit, 6 * unit); close() }; drawPath(path, color, style = Stroke(1.7f * unit)) }
            "voice" -> { drawRoundRect(color, Offset(9 * unit, 3 * unit), androidx.compose.ui.geometry.Size(6 * unit, 12 * unit), androidx.compose.ui.geometry.CornerRadius(3 * unit), style = Stroke(1.7f * unit)); line(6f, 12f, 6f, 16f); line(18f, 12f, 18f, 16f); line(6f, 16f, 12f, 19f); line(18f, 16f, 12f, 19f); line(12f, 19f, 12f, 22f) }
            else -> { line(9f, 5f, 16f, 12f); line(16f, 12f, 9f, 19f) }
        }
    }
}

@Composable fun Disclosure(title: String, content: @Composable () -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    TextButton(onClick = { expanded = !expanded }, shape = MaterialTheme.shapes.small, contentPadding = PaddingValues(horizontal = 8.dp, vertical = 8.dp), modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
        Text(title, modifier = Modifier.weight(1f)); Text(if (expanded) "Hide" else "Details", style = MaterialTheme.typography.labelMedium)
    }
    if (expanded) content()
}
