package io.dawnlight.oscar.expression

import android.graphics.BlurMaskFilter
import android.graphics.Paint as AndroidPaint
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.MotionDurationScale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.repeatOnLifecycle
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.collect
import kotlin.math.*

private val red = Color(0xFFE74A49)

/** Native vector drawing only. No WebView, private content, audio or app-layout coupling. */
@Composable fun ExpressionOrb(snapshot: ExpressionSnapshot, size: Dp = 64.dp, modifier: Modifier = Modifier) {
    val prefix = if (snapshot.source.kind == SourceKind.CORE) "" else "SIMULATED — "
    Canvas(modifier.size(size).semantics {
        contentDescription = "OSCAR expression"
        stateDescription = "$prefix${snapshot.resolved.label}. ${snapshot.resolved.delivery} delivery."
    }) { scale(this.size.width/582f, this.size.height/582f, Offset.Zero) { drawOrb(snapshot.pose) } }
}

@Composable fun ExpressionPresence(event: String, source: Source, size: Dp = 64.dp, reducedMotion: Boolean = false,
    modifier: Modifier = Modifier, onAnimationRecord: (AnimationRecord) -> Unit = {}, clock: () -> Long = System::currentTimeMillis) {
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val controller = remember(source) { ExpressionController(source, MotionData(context.assets.open("motion-v1.json").bufferedReader().use { it.readText() })) }
    val latest = rememberUpdatedState(event); val reduce = rememberUpdatedState(reducedMotion); val callback = rememberUpdatedState(onAnimationRecord)
    val time = rememberUpdatedState(clock)
    val state = remember(controller) { mutableStateOf(controller.snapshot(clock())) }
    LaunchedEffect(controller, owner) {
        val scale = coroutineContext[MotionDurationScale]
        owner.lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            try {
                coroutineScope {
                    launch {
                        var previous: String? = null
                        snapshotFlow { Triple(latest.value, reduce.value, scale?.scaleFactor == 0f) }.collect { (raw, requested, system) ->
                            val now = time.value(); controller.setReducedMotion(requested || system, now)
                            if (raw != previous) { controller.receive(raw, now); previous = raw }
                            state.value = controller.snapshot(now)
                            controller.takeAnimationRecords().forEach(callback.value)
                        }
                    }
                    launch {
                        snapshotFlow { state.value.moving to state.value.expiresAt }.collectLatest { (moving, expires) ->
                            if (moving) while (currentCoroutineContext().isActive) {
                                withFrameNanos { state.value = controller.snapshot(time.value()); controller.takeAnimationRecords().forEach(callback.value) }
                            } else if (expires != null) {
                                delay(max(1L, expires-time.value())); state.value = controller.snapshot(time.value())
                            }
                        }
                    }
                }
            } finally { controller.suspend(); state.value = controller.snapshot(time.value()) }
        }
    }
    ExpressionOrb(state.value, size, modifier)
}

private fun DrawScope.drawOrb(p: Pose) {
    rotate(p.body.toFloat(), Offset(288f,292f)) {
        drawCircle(Brush.radialGradient(0f to Color(0xFF4A93C9), .42f to Color(0xFF3786C5), 1f to Color(0xFF3282C1), center=Offset(214.08f,117.76f),radius=443.52f),264f,Offset(288f,292f))
        withTransform({ translate(p.x.toFloat(),p.y.toFloat()); rotate(p.tilt.toFloat(),Offset(374f,289f)) }) {
            // Native blur approximates the SVG drop-shadow; raster parity is not claimed.
            drawIntoCanvas { canvas ->
                val paint=AndroidPaint(AndroidPaint.ANTI_ALIAS_FLAG).apply { color=android.graphics.Color.argb(148,23,102,159);maskFilter=BlurMaskFilter(7f,BlurMaskFilter.Blur.NORMAL) }
                canvas.nativeCanvas.drawCircle(367f,304f,187f,paint)
            }
            drawCircle(Brush.linearGradient(0f to Color(0xFFEEB035),.55f to Color(0xFFE9AC2D),1f to Color(0xFFDFAE42),start=Offset(187f,102f),end=Offset(516.12f,476f)),187f,Offset(374f,289f))
            drawCircle(Brush.radialGradient(0f to Color(0xFFFACA43),.7f to Color(0xFFF9C840),1f to Color(0xFFF8C441),center=Offset(352.68f,225.28f),radius=269.04f),177f,Offset(381f,289f))
            translate(p.gx.toFloat(),p.gy.toFloat()) { drawMarks(p) }
        }
    }
}
private fun DrawScope.drawMarks(p: Pose) {
    val lid=233+(1-min(1.0,p.eye))*42;val bottom=317-(1-min(1.0,p.eye))*42;val closed=max(0.0,1-p.eye/.15).toFloat()
    val clip=Path().apply { moveTo(240f,(lid-p.lid).toFloat());lineTo(360f,(lid+p.lid).toFloat());lineTo(360f,bottom.toFloat());lineTo(240f,bottom.toFloat());close() }
    if(p.eye>=1)drawCircle(red, (42*p.width).toFloat(),Offset(299f,275f),alpha=1-closed)
    else clipPath(clip) { drawCircle(red,(42*p.width).toFloat(),Offset(299f,275f),alpha=1-closed) }
    drawPath(Path().apply { moveTo(274f,275f);cubicTo(288f,281f,310f,281f,324f,274f) },red,alpha=closed,style=Stroke(16f,cap=StrokeCap.Round))
    val left=426+(1-p.span)*29.5;val right=485-(1-p.span)*29.5;val open=p.opening.coerceIn(0.0,1.0)
    val a=listOf(left,276.0);val b=listOf(left+18*p.span,261+p.arc+16);val c=listOf(right-20*p.span,258+p.arc+16+(p.slant+4)/2);val d=listOf(right,272+p.slant+4)
    fun mid(u:List<Double>,v:List<Double>)=u.zip(v).map { (x,y)->(x+y)/2 }
    val ab=mid(a,b);val bc=mid(b,c);val cd=mid(c,d);val abc=mid(ab,bc);val bcd=mid(bc,cd);val tip=mid(abc,bcd)
    val original=listOf(a,ab,abc,tip,bcd,cd,d,cd,bcd,tip,abc,ab,a)
    val cx=(left+right)/2;val rx=(right-left)/2*.9;val cy=274.0;val ry=29.0;val k=.55228475
    val ellipse=listOf(listOf(cx-rx,cy),listOf(cx-rx,cy-k*ry),listOf(cx-k*rx,cy-ry),listOf(cx,cy-ry),listOf(cx+k*rx,cy-ry),listOf(cx+rx,cy-k*ry),listOf(cx+rx,cy),listOf(cx+rx,cy+k*ry),listOf(cx+k*rx,cy+ry),listOf(cx,cy+ry),listOf(cx-k*rx,cy+ry),listOf(cx-rx,cy+k*ry),listOf(cx-rx,cy))
    val path=Path()
    if(open==0.0) { path.moveTo(a[0].toFloat(),a[1].toFloat());path.cubicTo(b[0].toFloat(),b[1].toFloat(),c[0].toFloat(),c[1].toFloat(),d[0].toFloat(),d[1].toFloat()) }
    else {
        val points=original.mapIndexed { i,row->row.mapIndexed { j,value->(value+(ellipse[i][j]-value)*open).toFloat() } }
        path.moveTo(points[0][0],points[0][1]);for(i in listOf(1,4,7,10))path.cubicTo(points[i][0],points[i][1],points[i+1][0],points[i+1][1],points[i+2][0],points[i+2][1]);path.close()
        drawPath(path,red)
    }
    if(open<1)drawPath(path,red,style=Stroke((21*(1-open)).toFloat(),cap=StrokeCap.Round,join=StrokeJoin.Round))
}
