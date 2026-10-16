package io.dawnlight.oscar.mobile

import androidx.compose.animation.core.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.interaction.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.dropShadow
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.shadow.Shadow
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.error
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.*

@Composable fun OscarButton(onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true,
    color: Color = Sage, outlined: Boolean = false, content: @Composable RowScope.() -> Unit) {
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val focused by interaction.collectIsFocusedAsState()
    val scale by animateFloatAsState(if (pressed && enabled && !LocalReducedMotion.current) 0.985f else 1f,
        if (LocalReducedMotion.current) snap() else spring(dampingRatio = 0.8f, stiffness = 700f), label = "actionPress")
    val shape = RoundedCornerShape(16.dp)
    val scheme = MaterialTheme.colorScheme
    val face = if (!enabled) scheme.surfaceContainerHighest else if (outlined) scheme.surfaceContainer else color
    val ink = if (!enabled) scheme.onSurface.copy(alpha = 0.42f) else if (outlined) scheme.onSurface else Color.White
    Surface(onClick = onClick, enabled = enabled, interactionSource = interaction,
        modifier = modifier.semantics { role = Role.Button }.graphicsLayer { scaleX = scale; scaleY = scale }
            .dropShadow(shape, Shadow(if (pressed) 2.dp else 6.dp, Color.Black.copy(alpha = if (enabled) 0.10f else 0.02f), offset = DpOffset(2.dp, 3.dp))),
        shape = shape, color = Color.Transparent, contentColor = ink,
        border = BorderStroke(if (focused) 2.dp else 0.7.dp,
            if (focused) scheme.secondary else if (outlined) scheme.outlineVariant else lerp(face, Color.White, 0.22f))) {
        Row(Modifier.heightIn(min = 52.dp).background(Brush.linearGradient(listOf(lerp(face, Color.White, if (outlined) 0.04f else 0.09f), face)))
            .padding(horizontal = 18.dp, vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(10.dp, Alignment.CenterHorizontally),
            verticalAlignment = Alignment.CenterVertically) {
            ProvideTextStyle(MaterialTheme.typography.labelLarge) { content() }
        }
    }
}

@Composable fun OscarField(value: String, onValueChange: (String) -> Unit, label: String, modifier: Modifier = Modifier,
    enabled: Boolean = true, minLines: Int = 1, maxLines: Int = 4, singleLine: Boolean = false,
    isError: Boolean = false, supportingText: String? = null, keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    keyboardActions: KeyboardActions = KeyboardActions.Default, visualTransformation: VisualTransformation = VisualTransformation.None) {
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val scheme = MaterialTheme.colorScheme
    val shape = RoundedCornerShape(14.dp)
    Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(7.dp)) {
        Text(label, style = MaterialTheme.typography.labelLarge, color = scheme.onSurfaceVariant, modifier = Modifier.padding(start = 4.dp))
        BasicTextField(value, onValueChange, enabled = enabled, minLines = minLines, maxLines = maxLines, singleLine = singleLine,
            interactionSource = interaction, keyboardOptions = keyboardOptions, keyboardActions = keyboardActions, visualTransformation = visualTransformation,
            textStyle = MaterialTheme.typography.bodyLarge.copy(color = scheme.onSurface.copy(alpha = if (enabled) 1f else 0.48f)),
            cursorBrush = SolidColor(Sage), modifier = modifier.fillMaxWidth().heightIn(min = 54.dp).clip(shape)
                .background(scheme.surfaceContainer).border(if (focused) 1.5.dp else 0.7.dp,
                    if (isError) scheme.error else if (focused) Sage else scheme.outlineVariant, shape)
                .padding(16.dp).semantics { contentDescription = label; if (isError) error("Check this field") })
        supportingText?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = if (isError) scheme.error else scheme.onSurfaceVariant) }
    }
}

@Composable fun OscarSwitch(checked: Boolean, onCheckedChange: ((Boolean) -> Unit)?, modifier: Modifier = Modifier, enabled: Boolean = true) {
    Switch(checked, onCheckedChange, modifier.heightIn(min = 48.dp), enabled = enabled,
        colors = SwitchDefaults.colors(checkedThumbColor = Color(0xFFFAF7EF), uncheckedThumbColor = Color(0xFFFAF7EF),
            checkedTrackColor = Sage, uncheckedTrackColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.30f),
            checkedBorderColor = Color.Transparent, uncheckedBorderColor = Color.Transparent))
}
