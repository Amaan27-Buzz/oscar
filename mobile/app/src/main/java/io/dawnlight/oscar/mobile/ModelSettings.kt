package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.Box
import androidx.compose.material3.*
import androidx.compose.runtime.*

@Composable internal fun ModelSettings(session: CoreSession, state: MobileState) {
    val models = state.snapshot?.models
    var expanded by remember { mutableStateOf(false) }
    Text("How OSCAR thinks", style = MaterialTheme.typography.headlineMedium)
    Text("This selection is shared with Desktop through your Core.", style = MaterialTheme.typography.bodyMedium)
    if (state.link != Link.CONNECTED || models == null) {
        Text("Connect with an enrolled owner device to review current models.")
        return
    }
    PreferenceGroup("Model") {
        PreferenceValue("Current", models.selected.ifEmpty { "Automatic" }.replace("::", " · "))
        if (models.selected.isNotEmpty() && models.selected !in models.available)
            Text("The selected model is unavailable. Choose another model or Automatic.", style = MaterialTheme.typography.bodySmall)
        if (models.freeOnly) Text("Verified free cloud routes only.", style = MaterialTheme.typography.bodySmall)
        Box {
            OutlinedButton(onClick = { expanded = true }, enabled = !state.busy) { Text("Choose model") }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                if (models.freeOnly) DropdownMenuItem(text = { Text("Automatic") }, onClick = { expanded = false; session.selectModel("") })
                models.available.forEach { value ->
                    DropdownMenuItem(text = { Text(value.replace("::", " · ")) }, onClick = { expanded = false; session.selectModel(value) })
                }
                if (models.available.isEmpty()) DropdownMenuItem(text = { Text("No models currently available") }, onClick = {}, enabled = false)
            }
        }
    }
}
