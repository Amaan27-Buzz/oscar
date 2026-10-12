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
            "voice" -> { drawRoundRect(color, Offset(9 * unit, 3 * unit), androidx.compose.ui.geometry.Size(6 * unit, 12 * unit), androidx.compose.ui.geometry.CornerRadius(3 * unit), style = Stroke(1.7f * unit)); line(6f, 12f, 6f, 16f); line(18f, 12f, 18f, 16f); line(6f, 16f, 12f, 19f); line(18f, 16f, 12f, 19f); line(12f, 19f, 12f, 22f) }
            else -> { line(9f, 5f, 16f, 12f); line(16f, 12f, 9f, 19f) }
        }
    }
}

@Composable fun Disclosure(title: String, content: @Composable () -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    TextButton(onClick = { expanded = !expanded }, contentPadding = PaddingValues(0.dp), modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
        Text(title, modifier = Modifier.weight(1f)); Text(if (expanded) "Hide" else "Details", style = MaterialTheme.typography.labelMedium)
    }
    if (expanded) content()
}
