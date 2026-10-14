package io.dawnlight.oscar.mobile

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.animation.animateContentSize
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.dropShadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.shadow.Shadow
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties

val Sage = Color(0xFF526C56)
val Clay = Color(0xFFB65D40)
val Powder = Color(0xFFDCEAF7)
val Lilac = Color(0xFFD9D3E6)

/** Entry-only motion renders current content; never retains an outgoing private screen. */
@Composable fun pageEntrance(page: Any): Modifier {
    val reduced = LocalReducedMotion.current
    val progress = remember(page, reduced) { Animatable(if (reduced) 1f else 0f) }
    LaunchedEffect(progress) {
        if (!reduced) progress.animateTo(1f, tween(220, easing = FastOutSlowInEasing))
    }
    return Modifier.graphicsLayer {
        alpha = progress.value
        translationY = (1f - progress.value) * 8.dp.toPx()
    }
}

// Bundled typography is resolved locally; no font provider receives interaction data.
private val Manrope = FontFamily(Font(R.font.manrope_400), Font(R.font.manrope_600, FontWeight.SemiBold), Font(R.font.manrope_700, FontWeight.Bold))
private val Fraunces = FontFamily(Font(R.font.fraunces), Font(R.font.fraunces_italic, style = FontStyle.Italic))
val OscarTypography = Typography(
    displaySmall = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.Bold, fontSize = 32.sp, lineHeight = 36.sp, letterSpacing = (-1).sp),
    headlineLarge = TextStyle(fontFamily = Fraunces, fontSize = 30.sp, lineHeight = 34.sp, letterSpacing = (-0.6).sp),
    headlineSmall = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.Bold, fontSize = 24.sp, lineHeight = 28.sp),
    titleLarge = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 20.sp, lineHeight = 26.sp),
    titleMedium = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 22.sp),
    bodyLarge = TextStyle(fontFamily = Manrope, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = Manrope, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontFamily = Manrope, fontSize = 12.sp, lineHeight = 17.sp),
    labelLarge = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    labelSmall = TextStyle(fontFamily = Manrope, fontSize = 11.sp, lineHeight = 15.sp),
)

@Composable fun EditorialHeading(title: String, accent: String? = null) {
    Text(title, style = MaterialTheme.typography.displaySmall, modifier = Modifier.semantics { heading() })
    accent?.let { Text(it, style = MaterialTheme.typography.headlineLarge.copy(fontSize = 24.sp, lineHeight = 28.sp, fontStyle = FontStyle.Italic)) }
}

@Composable fun Illustration(resource: Int, modifier: Modifier = Modifier, height: Dp = 180.dp) {
    Image(painterResource(resource), contentDescription = null,
        modifier = modifier.fillMaxWidth().height(height), contentScale = ContentScale.Fit)
}

@Composable fun TactileSurface(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    val shape = RoundedCornerShape(12.dp)
    Surface(modifier.dropShadow(shape, Shadow(8.dp, Color.Black.copy(alpha = 0.07f), offset = DpOffset(3.dp, 4.dp)))
        .dropShadow(shape, Shadow(5.dp, Color.White.copy(alpha = 0.14f), offset = DpOffset((-2).dp, (-2).dp))),
        shape = shape, color = MaterialTheme.colorScheme.surfaceContainer,
        border = androidx.compose.foundation.BorderStroke(0.5.dp, MaterialTheme.colorScheme.outlineVariant)) {
        Column(Modifier.animateContentSize(tween(if (LocalReducedMotion.current) 0 else 180)).padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp), content = content)
    }
}

@Composable fun FeatureRow(title: String, subtitle: String, icon: String, color: Color = Sage, action: (() -> Unit)? = null, modifier: Modifier = Modifier) {
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val reduced = LocalReducedMotion.current
    val scale by animateFloatAsState(if (pressed && !reduced) 0.985f else 1f, tween(if (reduced) 0 else 120), label = "rowPress")
    Row(modifier.fillMaxWidth().heightIn(min = 64.dp)
        .graphicsLayer { scaleX = scale; scaleY = scale }
        .then(if (action != null) Modifier.clickable(interactionSource = interaction, indication = androidx.compose.material3.ripple(), onClick = action, role = Role.Button) else Modifier)
        .padding(vertical = 8.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Box(Modifier.size(36.dp).background(color.copy(alpha = 0.15f), CircleShape), contentAlignment = Alignment.Center) {
            Glyph(icon, color = if (MaterialTheme.colorScheme.background == Color(0xFFF5F1E7)) color else MaterialTheme.colorScheme.onSurface)
        }
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(subtitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        if (action != null) Glyph("Next")
    }
}

@Composable fun StatusLabel(text: String) {
    Text(text, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
}

@Composable fun SupportingDetails(title: String, onOpen: () -> Unit = {}, content: @Composable ColumnScope.() -> Unit) {
    var open by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxWidth().animateContentSize(tween(if (LocalReducedMotion.current) 0 else 180))) {
        TextButton(onClick = { open = !open; if (open) onOpen() }, modifier = Modifier.semantics { stateDescription = if (open) "Expanded" else "Collapsed" }) {
            Text(title); Text(if (open) " −" else " +")
        }
        if (open) Column(verticalArrangement = Arrangement.spacedBy(8.dp), content = content)
    }
}

@Composable fun Glyph(name: String, modifier: Modifier = Modifier, color: Color = MaterialTheme.colorScheme.onSurface) {
    Canvas(modifier.size(22.dp)) {
        val s = size.width / 24f
        val stroke = Stroke(1.7f * s)
        fun line(x: Float, y: Float, xx: Float, yy: Float) = drawLine(color, androidx.compose.ui.geometry.Offset(x*s,y*s), androidx.compose.ui.geometry.Offset(xx*s,yy*s), strokeWidth = 1.7f*s)
        fun path(vararg points: Pair<Float, Float>) {
            drawPath(Path().apply { points.forEachIndexed { i, p -> if (i == 0) moveTo(p.first*s,p.second*s) else lineTo(p.first*s,p.second*s) } },color,style=stroke)
        }
        when (name) {
            "Conversation" -> { drawRoundRect(color, androidx.compose.ui.geometry.Offset(3*s,3*s), androidx.compose.ui.geometry.Size(18*s,14*s), androidx.compose.ui.geometry.CornerRadius(3*s), style=stroke); path(3f to 13f,3f to 21f,8f to 17f) }
            "Automations" -> path(14f to 2f,5f to 13f,11f to 13f,9f to 22f,19f to 10f,13f to 10f,14f to 2f)
            "Activity" -> { line(5f,13f,5f,21f); line(12f,3f,12f,21f); line(19f,8f,19f,21f) }
            "Back" -> { path(11f to 5f,4f to 12f,11f to 19f); line(4f,12f,21f,12f) }
            "Next" -> path(9f to 6f,15f to 12f,9f to 18f)
            "Voice" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(9*s,3*s),androidx.compose.ui.geometry.Size(6*s,12*s),androidx.compose.ui.geometry.CornerRadius(3*s),style=stroke); path(5f to 11f,5f to 16f,12f to 19f,19f to 16f,19f to 11f); line(12f,19f,12f,23f) }
            "Add" -> { line(12f,4f,12f,20f); line(4f,12f,20f,12f) }
            "Devices" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(2*s,4*s),androidx.compose.ui.geometry.Size(20*s,13*s),androidx.compose.ui.geometry.CornerRadius(2*s),style=stroke); line(12f,17f,12f,21f); line(7f,21f,17f,21f) }
            else -> { for (y in listOf(6f,12f,18f)) { line(3f,y,21f,y); drawCircle(color,2.5f*s,androidx.compose.ui.geometry.Offset((if(y==12f) 16f else 8f)*s,y*s)) } }
        }
    }
}

@Composable fun DetailPage(title: String, close: () -> Unit, tag: String, content: @Composable ColumnScope.() -> Unit) {
    Dialog(onDismissRequest = close, properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false)) {
        Surface(Modifier.fillMaxSize().testTagCompat(tag), color = MaterialTheme.colorScheme.background) {
            Column(Modifier.safeDrawingPadding().imePadding()) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = close, modifier = Modifier.semantics { contentDescription = "Back" }) { Glyph("Back") }
                    Text(title, style = MaterialTheme.typography.bodyMedium)
                }
                Column(Modifier.weight(1f).widthIn(max = 720.dp).fillMaxWidth().align(Alignment.CenterHorizontally).then(pageEntrance(tag))
                    .verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp), content = content)
            }
        }
    }
}

private fun Modifier.testTagCompat(tag: String) = this.then(Modifier.semantics { testTag = tag })
