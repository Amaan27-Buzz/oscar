package io.dawnlight.oscar.mobile

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.AbsoluteAlignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.boundsInParent
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import kotlin.math.roundToInt

/** Only the selection ornament travels; navigation and task readback change immediately. */
@Composable private fun fluidSelection(target: Rect): Rect {
    if (LocalReducedMotion.current) return target
    val movement = updateTransition(target, label = "selectionTravel")
    val left by movement.animateFloat(transitionSpec = {
        spring(dampingRatio = 0.88f, stiffness = if (targetState.left > initialState.left) 350f else 650f)
    }, label = "trailingEdge") { it.left }
    val right by movement.animateFloat(transitionSpec = {
        spring(dampingRatio = 0.88f, stiffness = if (targetState.left > initialState.left) 650f else 350f)
    }, label = "leadingEdge") { it.right }
    return Rect(left, target.top, right.coerceAtLeast(left + 1f), target.bottom)
}

@Composable private fun BoxScope.SelectionMark(target: Rect, color: Color, tag: String) {
    val bounds = fluidSelection(target)
    val density = LocalDensity.current
    Box(Modifier.align(AbsoluteAlignment.TopLeft).absoluteOffset { IntOffset(bounds.left.roundToInt(), bounds.top.roundToInt()) }
        .size(with(density) { bounds.width.toDp() }, with(density) { bounds.height.toDp() })
        .background(color, RoundedCornerShape(3.dp)).testTag(tag))
}

@Composable internal fun PrimaryNavigation(destination: Destination, navigate: (Destination) -> Unit) {
    val items = listOf(Destination.OSCAR, Destination.AUTOMATIONS, Destination.ACTIVITY)
    val bounds = remember { mutableStateMapOf<Destination, Rect>() }
    val density = LocalDensity.current
    val largeText = density.fontScale > 1.3f
    val ink = MaterialTheme.colorScheme.onSurface
    val accent = if (MaterialTheme.colorScheme.background == Color(0xFFF5F1E7)) Sage else Color(0xFFA8BDA8)
    Surface(color = MaterialTheme.colorScheme.surfaceContainer) {
        Box(Modifier.fillMaxWidth().testTag("primary-navigation").navigationBarsPadding()) {
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Box(Modifier.fillMaxWidth().padding(horizontal = if (largeText) 0.dp else 16.dp)) {
                bounds[destination]?.let { cell ->
                    val half = with(density) { 24.dp.toPx() }
                    SelectionMark(Rect(cell.center.x - half, 0f, cell.center.x + half, with(density) { 3.dp.toPx() }), accent, "navigation-marker")
                }
                Row(Modifier.fillMaxWidth().selectableGroup()) {
                    items.forEach { item ->
                        val chosen = item == destination
                        val tint by animateColorAsState(if (chosen) ink else MaterialTheme.colorScheme.onSurfaceVariant,
                            tween(if (LocalReducedMotion.current) 0 else 180), label = "navigationInk")
                        val lift by animateFloatAsState(if (chosen) -2f else 0f,
                            if (LocalReducedMotion.current) snap() else spring(dampingRatio = 0.85f, stiffness = 600f), label = "navigationLift")
                        Column(Modifier.weight(if (largeText) item.label.length.toFloat() else 1f).heightIn(min = 72.dp)
                            .onGloballyPositioned { bounds[item] = it.boundsInParent() }
                            .testTag("destination-${item.name}").selectable(chosen, role = Role.Tab, onClick = { navigate(item) })
                            .padding(vertical = 14.dp), horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Glyph(item.label, Modifier.graphicsLayer { translationY = lift * density.density }, if (chosen) accent else tint)
                            Text(item.label, style = MaterialTheme.typography.labelSmall,
                                color = tint, maxLines = 1, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                        }
                    }
                }
            }
        }
    }
}

@Composable internal fun ActivityFilters(selected: String, select: (String) -> Unit) {
    val bounds = remember { mutableStateMapOf<String, Rect>() }
    val density = LocalDensity.current
    Box(Modifier.fillMaxWidth()) {
        HorizontalDivider(Modifier.align(Alignment.BottomCenter), color = MaterialTheme.colorScheme.outlineVariant)
        bounds[selected]?.let { cell ->
            val inset = with(density) { 16.dp.toPx() }
            SelectionMark(Rect(cell.left + inset, cell.bottom - with(density) { 3.dp.toPx() }, cell.right - inset, cell.bottom),
                MaterialTheme.colorScheme.onSurface, "activity-filter-marker")
        }
        Row(Modifier.fillMaxWidth().selectableGroup()) {
            listOf("Active", "Finished").forEach { name ->
                val color by animateColorAsState(if (selected == name) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant,
                    tween(if (LocalReducedMotion.current) 0 else 180), label = "filterInk")
                Box(Modifier.weight(1f).heightIn(min = 52.dp).onGloballyPositioned { bounds[name] = it.boundsInParent() }
                    .testTag("activity-filter-$name").selectable(selected == name, role = Role.Tab, onClick = { select(name) }).padding(12.dp),
                    contentAlignment = Alignment.Center) { Text(name, style = MaterialTheme.typography.labelLarge, color = color) }
            }
        }
    }
}
