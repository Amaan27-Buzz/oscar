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
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.CompositingStrategy
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.graphics.luminance
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
val Amber = Color(0xFFE4A338)

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
    val cutout = when (resource) {
        R.drawable.illustration_home -> R.drawable.illustration_home_cutout
        R.drawable.illustration_automations -> R.drawable.illustration_automations_cutout
        R.drawable.illustration_preferences -> R.drawable.illustration_preferences_cutout
        R.drawable.illustration_devices -> R.drawable.illustration_devices_cutout
        R.drawable.illustration_decision -> R.drawable.illustration_decision_cutout
        R.drawable.illustration_task -> R.drawable.illustration_task_cutout
        R.drawable.illustration_today -> R.drawable.illustration_today_cutout
        R.drawable.illustration_awareness -> R.drawable.illustration_awareness_cutout
        else -> resource
    }
    val light = MaterialTheme.colorScheme.background == Color(0xFFF5F1E7)
    Image(painterResource(cutout), contentDescription = null,
        modifier = modifier.fillMaxWidth().height(height).graphicsLayer {
            compositingStrategy = CompositingStrategy.Offscreen
            blendMode = if (light && cutout == resource) BlendMode.Multiply else BlendMode.SrcOver
        }.drawWithContent {
            drawContent()
            if (cutout == resource) {
                drawRect(Brush.horizontalGradient(0f to Color.Transparent, 0.07f to Color.Black, 0.93f to Color.Black, 1f to Color.Transparent), blendMode = BlendMode.DstIn)
                drawRect(Brush.verticalGradient(0f to Color.Transparent, 0.08f to Color.Black, 0.92f to Color.Black, 1f to Color.Transparent), blendMode = BlendMode.DstIn)
            }
        }, contentScale = ContentScale.Fit)
}

@Composable fun IllustratedIntro(title: String, subtitle: String? = null, artwork: Int, height: Dp = 124.dp) {
    val artWidth = if (androidx.compose.ui.platform.LocalDensity.current.fontScale > 1.3f) 80.dp else height * 1.15f
    Row(Modifier.fillMaxWidth().heightIn(min = height), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() })
            subtitle?.let { Text(it, style = MaterialTheme.typography.headlineLarge.copy(fontSize = 23.sp, lineHeight = 28.sp, fontStyle = FontStyle.Italic), color = MaterialTheme.colorScheme.onSurfaceVariant) }
        }
        Illustration(artwork, Modifier.width(artWidth), if (artWidth == 80.dp) 90.dp else height)
    }
}

@Composable fun IconBadge(icon: String, color: Color = Sage, size: Dp = 48.dp) {
    val ink = if (color.luminance() > 0.4f) Color(0xFF2D392F) else Color.White
    Box(Modifier.size(size).dropShadow(CircleShape, Shadow(3.dp, Color.Black.copy(alpha = 0.08f), offset = DpOffset(1.dp, 2.dp)))
        .background(Brush.linearGradient(listOf(lerp(color, Color.White, 0.13f), color)), CircleShape), contentAlignment = Alignment.Center) {
        Glyph(icon, Modifier.size(size * 0.52f), ink)
    }
}

@Composable fun StatusPill(text: String, color: Color = Sage) {
    val light = MaterialTheme.colorScheme.background == Color(0xFFF5F1E7)
    Row(Modifier.background(color.copy(alpha = if (light) 0.11f else 0.23f), RoundedCornerShape(10.dp)).padding(horizontal = 12.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(7.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(6.dp).background(if (light) color else lerp(color, Color.White, 0.45f), CircleShape))
        Text(text, style = MaterialTheme.typography.labelLarge,
            color = if (light && color.luminance() <= 0.25f) color else MaterialTheme.colorScheme.onSurface)
    }
}

@Composable fun TactileSurface(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    val shape = RoundedCornerShape(18.dp)
    Surface(modifier.dropShadow(shape, Shadow(8.dp, Color.Black.copy(alpha = 0.07f), offset = DpOffset(3.dp, 4.dp)))
        .dropShadow(shape, Shadow(5.dp, Color.White.copy(alpha = 0.14f), offset = DpOffset((-2).dp, (-2).dp))),
        shape = shape, color = MaterialTheme.colorScheme.surfaceContainer,
        border = androidx.compose.foundation.BorderStroke(0.5.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.65f))) {
        Column(Modifier.animateContentSize(if (LocalReducedMotion.current) snap() else spring(dampingRatio = 0.9f, stiffness = 500f)).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp), content = content)
    }
}

@Composable fun FeatureRow(title: String, subtitle: String, icon: String, color: Color = Sage, action: (() -> Unit)? = null, modifier: Modifier = Modifier, artwork: Int? = null) {
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val reduced = LocalReducedMotion.current
    val scale by animateFloatAsState(if (pressed && !reduced) 0.985f else 1f, if (reduced) snap() else spring(dampingRatio = 0.8f, stiffness = 700f), label = "rowPress")
    Row(modifier.fillMaxWidth().heightIn(min = 64.dp)
        .graphicsLayer { scaleX = scale; scaleY = scale }
        .then(if (action != null) Modifier.clickable(interactionSource = interaction, indication = androidx.compose.material3.ripple(), onClick = action, role = Role.Button) else Modifier)
        .padding(vertical = 8.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        if (artwork == null) IconBadge(icon, color) else Illustration(artwork, Modifier.width(54.dp), 54.dp)
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
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
    val angle by animateFloatAsState(if (open) 90f else 0f, if (LocalReducedMotion.current) snap() else spring(dampingRatio = 0.9f, stiffness = 500f), label = "disclosureTurn")
    Column(Modifier.fillMaxWidth().animateContentSize(if (LocalReducedMotion.current) snap() else spring(dampingRatio = 0.9f, stiffness = 500f))) {
        Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).clickable(role = Role.Button) { open = !open; if (open) onOpen() }
            .semantics { stateDescription = if (open) "Expanded" else "Collapsed" }.padding(vertical = 10.dp, horizontal = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(title, style = MaterialTheme.typography.labelLarge, modifier = Modifier.weight(1f))
            Glyph("Next", Modifier.size(16.dp).graphicsLayer { rotationZ = angle }, MaterialTheme.colorScheme.onSurfaceVariant)
        }
        if (open) Column(verticalArrangement = Arrangement.spacedBy(8.dp), content = content)
    }
}

@Composable fun Glyph(name: String, modifier: Modifier = Modifier, color: Color = LocalContentColor.current) {
    Canvas(modifier.size(22.dp)) {
        val s = size.width / 24f
        val stroke = Stroke(1.75f * s, cap = StrokeCap.Round, join = StrokeJoin.Round)
        fun line(x: Float, y: Float, xx: Float, yy: Float) = drawLine(color, androidx.compose.ui.geometry.Offset(x*s,y*s), androidx.compose.ui.geometry.Offset(xx*s,yy*s), strokeWidth = 1.75f*s, cap = StrokeCap.Round)
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
            "Phone" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(6*s,2*s),androidx.compose.ui.geometry.Size(12*s,20*s),androidx.compose.ui.geometry.CornerRadius(2*s),style=stroke); line(10f,18f,14f,18f) }
            "Privacy", "Shield" -> path(12f to 2f,21f to 6f,20f to 15f,12f to 22f,4f to 15f,3f to 6f,12f to 2f)
            "Access" -> { drawRoundRect(color, androidx.compose.ui.geometry.Offset(3*s,3*s), androidx.compose.ui.geometry.Size(18*s,14*s), androidx.compose.ui.geometry.CornerRadius(5*s), style=stroke); path(5f to 16f,4f to 22f,11f to 17f) }
            "Memory", "Book" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(4*s,3*s),androidx.compose.ui.geometry.Size(16*s,18*s),androidx.compose.ui.geometry.CornerRadius(2*s),style=stroke); line(8f,3f,8f,21f); line(11f,8f,17f,8f); line(11f,12f,17f,12f) }
            "Notifications" -> { path(4f to 17f,6f to 14f,6f to 8f,9f to 4f,15f to 4f,18f to 8f,18f to 14f,20f to 17f,4f to 17f); path(9f to 20f,12f to 22f,15f to 20f) }
            "Appearance", "Palette" -> {
                drawPath(Path().apply { moveTo(21*s,11*s); cubicTo(21*s,3*s,10*s,0*s,4*s,6*s); cubicTo(-1*s,12*s,4*s,22*s,12*s,22*s); cubicTo(18*s,22*s,9*s,15*s,16*s,15*s); cubicTo(20*s,16*s,22*s,14*s,21*s,11*s) },color,style=stroke)
                listOf(7f to 8f, 12f to 5f, 17f to 8f, 6f to 14f).forEach { drawCircle(color,1.1f*s,androidx.compose.ui.geometry.Offset(it.first*s,it.second*s)) }
            }
            "Persona", "Person" -> { drawCircle(color,4*s,androidx.compose.ui.geometry.Offset(12*s,7*s),style=stroke); drawPath(Path().apply { moveTo(4*s,21*s); cubicTo(4*s,12*s,20*s,12*s,20*s,21*s); close() },color,style=stroke) }
            "Awareness" -> { path(2f to 12f,7f to 6f,17f to 6f,22f to 12f,17f to 18f,7f to 18f,2f to 12f); drawCircle(color,3*s,style=stroke) }
            "About" -> { drawCircle(color,9*s,style=stroke); line(12f,11f,12f,17f); drawCircle(color,1*s,androidx.compose.ui.geometry.Offset(12*s,7*s)) }
            "Calendar" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(3*s,5*s),androidx.compose.ui.geometry.Size(18*s,16*s),androidx.compose.ui.geometry.CornerRadius(2*s),style=stroke); line(3f,10f,21f,10f); line(7f,2f,7f,7f); line(17f,2f,17f,7f); drawCircle(color,1.4f*s,androidx.compose.ui.geometry.Offset(8*s,15*s)); drawCircle(color,1.4f*s,androidx.compose.ui.geometry.Offset(15*s,15*s)) }
            "Clock" -> { drawCircle(color,9*s,style=stroke); path(12f to 6f,12f to 12f,17f to 15f) }
            "Document" -> { path(5f to 2f,15f to 2f,20f to 7f,20f to 22f,5f to 22f,5f to 2f); path(15f to 2f,15f to 8f,20f to 8f); line(8f,13f,16f,13f); line(8f,17f,15f,17f) }
            "Door" -> { path(5f to 3f,18f to 2f,18f to 22f,5f to 20f,5f to 3f); drawCircle(color,1*s,androidx.compose.ui.geometry.Offset(14*s,12*s)) }
            "Capture" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(2*s,6*s),androidx.compose.ui.geometry.Size(20*s,15*s),androidx.compose.ui.geometry.CornerRadius(3*s),style=stroke); path(6f to 6f,8f to 3f,16f to 3f,18f to 6f); drawCircle(color,4*s,androidx.compose.ui.geometry.Offset(12*s,13*s),style=stroke) }
            "Retain" -> { drawOval(color,androidx.compose.ui.geometry.Offset(4*s,3*s),androidx.compose.ui.geometry.Size(16*s,6*s),style=stroke); line(4f,6f,4f,19f); line(20f,6f,20f,19f); drawArc(color,0f,180f,false,androidx.compose.ui.geometry.Offset(4*s,15*s),androidx.compose.ui.geometry.Size(16*s,7*s),style=stroke); drawArc(color,0f,180f,false,androidx.compose.ui.geometry.Offset(4*s,8*s),androidx.compose.ui.geometry.Size(16*s,7*s),style=stroke) }
            "Leaf" -> { drawPath(Path().apply { moveTo(4*s,18*s); cubicTo(1*s,5*s,12*s,2*s,21*s,3*s); cubicTo(21*s,16*s,15*s,22*s,4*s,18*s) },color,style=stroke); path(3f to 22f,9f to 12f,15f to 9f) }
            "Sun" -> { drawCircle(color,4.5f*s,style=stroke); for (angle in 0..7) { val radians=angle*Math.PI/4; val x=kotlin.math.cos(radians).toFloat(); val y=kotlin.math.sin(radians).toFloat(); line(12+8*x,12+8*y,12+11*x,12+11*y) } }
            "Moon" -> drawPath(Path().apply { moveTo(17*s,3*s); cubicTo(2*s,-1*s,-1*s,18*s,11*s,22*s); cubicTo(18*s,24*s,23*s,17*s,22*s,13*s); cubicTo(14*s,20*s,7*s,10*s,17*s,3*s) },color,style=stroke)
            "Home" -> { path(2f to 11f,12f to 2f,22f to 11f); path(5f to 9f,5f to 22f,10f to 22f,10f to 15f,15f to 15f,15f to 22f,19f to 22f,19f to 9f) }
            "Goal" -> { drawCircle(color,9*s,style=stroke); drawCircle(color,5*s,style=stroke); path(12f to 12f,21f to 3f,16f to 3f); line(21f,3f,21f,8f) }
            "Edit" -> { path(4f to 16f,16f to 4f,21f to 9f,9f to 21f,3f to 22f,4f to 16f); line(13f,7f,18f,12f) }
            "Play" -> path(7f to 3f,21f to 12f,7f to 21f,7f to 3f)
            "Pause" -> { line(8f,4f,8f,20f); line(16f,4f,16f,20f) }
            "Check" -> path(4f to 12f,10f to 18f,21f to 5f)
            "Send" -> { path(13f to 5f,20f to 12f,13f to 19f); line(3f,12f,20f,12f) }
            "Close" -> { line(5f,5f,19f,19f); line(5f,19f,19f,5f) }
            "More" -> listOf(5f,12f,19f).forEach { drawCircle(color,1.5f*s,androidx.compose.ui.geometry.Offset(12*s,it*s)) }
            "Android" -> { drawRoundRect(color,androidx.compose.ui.geometry.Offset(5*s,7*s),androidx.compose.ui.geometry.Size(14*s,11*s),androidx.compose.ui.geometry.CornerRadius(3*s),style=stroke); line(7f,3f,9f,7f); line(17f,3f,15f,7f); line(8f,18f,8f,22f); line(16f,18f,16f,22f); line(2f,9f,2f,16f); line(22f,9f,22f,16f); drawCircle(color,0.9f*s,androidx.compose.ui.geometry.Offset(9*s,11*s)); drawCircle(color,0.9f*s,androidx.compose.ui.geometry.Offset(15*s,11*s)) }
            "Preferences" -> { drawCircle(color,4*s,style=stroke); for (angle in 0..7) { val radians=angle*Math.PI/4; val x=kotlin.math.cos(radians).toFloat(); val y=kotlin.math.sin(radians).toFloat(); line(12+7*x,12+7*y,12+10*x,12+10*y) } }
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
