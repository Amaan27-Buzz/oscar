package io.dawnlight.oscar.mobile

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp

internal val LocalPageArtwork = compositionLocalOf<Int?> { null }

/** Art belongs to the scrolling page canvas, outside the readable content gutter. */
@Composable internal fun PageArtwork(artwork: Int?, scroll: ScrollState, state: MobileState? = null) {
    if (artwork == null) return
    val largeText = LocalDensity.current.fontScale > 1.3f
    val dark = MaterialTheme.colorScheme.background.luminance() < 0.2f
    val paper = MaterialTheme.colorScheme.background
    BoxWithConstraints(Modifier.fillMaxSize().clipToBounds().testTag("page-artwork")) {
        val width = maxWidth.coerceAtMost(720.dp)
        val home = artwork == R.drawable.illustration_home
        val wide = artwork == R.drawable.illustration_automations
        val book = artwork == R.drawable.illustration_reading
        val presence = artwork == R.drawable.oscar_orb
        val artHeight = when {
            home -> 245.dp; wide -> 225.dp; book -> 208.dp
            artwork == R.drawable.illustration_awareness -> 335.dp
            artwork == R.drawable.illustration_today -> 330.dp
            artwork == R.drawable.illustration_preferences -> 250.dp
            else -> 270.dp
        }
        val artWidth = width * when {
            home || wide -> 1.16f; book -> 0.63f
            presence -> 0.72f
            artwork == R.drawable.illustration_decision -> 0.78f
            artwork == R.drawable.illustration_preferences -> 0.85f
            artwork == R.drawable.illustration_worker -> 0.77f
            else -> 0.98f
        }
        val top = when {
            home -> 168.dp; wide -> 100.dp; book -> (-5).dp
            artwork == R.drawable.illustration_awareness -> (-30).dp
            artwork == R.drawable.illustration_today -> (-38).dp
            else -> (-8).dp
        }
        val edge = when {
            home -> 18.dp; wide -> 38.dp; book -> 28.dp
            artwork == R.drawable.illustration_awareness -> 112.dp
            else -> 58.dp
        }
        Box(Modifier.fillMaxWidth().height(430.dp).graphicsLayer { translationY = -scroll.value.toFloat() }) {
            if (!home && !wide) Canvas(Modifier.fillMaxWidth().height(if (book) 235.dp else 325.dp)) {
                val tone = if (dark) Color(0xFF293126) else if (artwork == R.drawable.illustration_devices) Powder else Sage
                val contour = Path().apply {
                    moveTo(size.width * 0.78f, -size.height * 0.15f)
                    cubicTo(size.width * 0.46f, 0f, size.width * 0.68f, size.height * 0.15f, size.width * 0.40f, size.height * 0.30f)
                    cubicTo(size.width * 0.08f, size.height * 0.55f, size.width * 0.48f, size.height * 0.91f, size.width * 0.79f, size.height * 0.93f)
                    cubicTo(size.width, size.height * 0.95f, size.width * 1.20f, size.height * 1.18f, size.width * 1.15f, size.height * 0.72f)
                    lineTo(size.width * 1.15f, -size.height * 0.15f); close()
                }
                drawPath(contour, tone.copy(alpha = if (dark) 0.72f else if (tone == Powder) 0.72f else 0.10f))
            }
            if (presence && state != null) Box(Modifier.width(180.dp).offset(x = 22.dp, y = 62.dp).align(Alignment.TopEnd)) {
                OscarOrb(state, size = if (largeText) 132.dp else 164.dp, tag = "scene-orb")
            } else Illustration(artwork, Modifier.requiredWidth(artWidth).align(Alignment.TopEnd).offset(x = edge, y = top)
                .testTag("edge-illustration"), artHeight)
            if (dark) Box(Modifier.fillMaxWidth().height(112.dp).background(
                Brush.verticalGradient(listOf(paper.copy(alpha = 0.88f), Color.Transparent))))
        }
    }
}
