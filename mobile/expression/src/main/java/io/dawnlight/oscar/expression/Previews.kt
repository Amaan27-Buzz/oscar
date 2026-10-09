package io.dawnlight.oscar.expression

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

@Preview(showBackground = true, backgroundColor = 0xFFF7F7F3, widthDp = 240, heightDp = 240)
@Composable fun NeutralExpressionPreview() {
    val context = LocalContext.current
    val data = remember { MotionData(context.assets.open("motion-v1.json").bufferedReader().use { it.readText() }) }
    ExpressionOrb(ExpressionSnapshot(data.canonical, data.resolve(Scene("idle", "composed")), Source(SourceKind.FIXTURE,"preview"),0,AnimationPhase.HELD,false,null,EffectivePriority.DELIVERY),192.dp)
}
@Preview(showBackground = true, backgroundColor = 0xFFF7F7F3, widthDp = 240, heightDp = 240)
@Composable fun SpeakingExpressionPreview() {
    val context = LocalContext.current
    val data = remember { MotionData(context.assets.open("motion-v1.json").bufferedReader().use { it.readText() }) }
    val (pose,resolved) = data.sample(data.study(data.canonical,Scene("speaking","composed")),2300.0)
    ExpressionOrb(ExpressionSnapshot(pose,resolved,Source(SourceKind.FIXTURE,"preview"),0,AnimationPhase.HELD,false,null,EffectivePriority.ACTIVITY),192.dp)
}
