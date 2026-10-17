package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class AdaptiveContractsTest {
    private fun descriptor() = JSONObject("""{"version":1,"view_id":"v","task_id":"t","revision":1,"observed_at_ms":100,"expires_at_ms":200,"fallback":"Task reported","components":[{"type":"task_progress","text":"Working","source_ids":[]}],"actions":[{"type":"inspect_task","task_id":"t"}]}""")
    @Test fun onlyTypedBoundedViewsAreAdmitted() {
        assertNotNull(parseAdaptive(descriptor()))
        assertNull(parseAdaptive(descriptor().put("version", 2)))
        assertNull(parseAdaptive(descriptor().put("script", "execute()")))
        assertNull(parseAdaptive(descriptor().put("expires_at_ms", 99_000)))
        val changed = descriptor(); changed.getJSONArray("actions").getJSONObject(0).put("type", "approve")
        assertNull(parseAdaptive(changed))
        val component = descriptor(); component.getJSONArray("components").getJSONObject(0).put("type", "webview")
        assertNull(parseAdaptive(component))
    }
    @Test fun overlayCannotStartWithoutAnExplicitInProcessRequest() {
        assertFalse(CompanionOverlay.consume(null))
        assertFalse(CompanionOverlay.consume("unrequested-token"))
    }
}
