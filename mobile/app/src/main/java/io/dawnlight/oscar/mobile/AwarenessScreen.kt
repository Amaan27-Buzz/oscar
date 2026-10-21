package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject

@Composable fun AwarenessScreen(session: CoreSession, state: MobileState, privacy: () -> Unit) {
    val source = state.snapshot?.management?.source
    val current = source?.let { JSONObject(it).getJSONObject("sentry") }
    IllustratedIntro("Awareness", "On your terms.", R.drawable.illustration_awareness, height = 144.dp)
    if (current == null) {
        StatusLabel("Awareness readback unavailable")
        Text("Connect to Core to review the current mode and each source's permissions.", style = MaterialTheme.typography.bodySmall)
        TextButton(onClick = privacy) { Text("Android capture permissions") }
        return
    }
    StatusLabel("${current.getString("mode").replace('_', ' ')} · ${current.getString("state")}")
    CurrentBrief(session, state)
    AddContextSource(session, state)
    val sources = current.objects("sources", 64)
    var mode by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getString("mode")) }
    var attention by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getString("state")) }
    var selected by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getJSONArray("source_ids").texts(32).toSet()) }
    var interrupts by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getBoolean("allow_interrupt")) }
    PreferenceGroup("Source permissions", flat = true) {
        if (sources.isEmpty()) Text("No awareness sources are connected.")
        sources.forEach { item -> key(item.getString("id"), item.getInt("epoch")) {
            TactileSurface(Modifier.fillMaxWidth()) {
                Text(item.getString("id") + if (item.getBoolean("simulated")) " · simulated" else "", style = MaterialTheme.typography.titleMedium)
                listOf("perceive" to "Observe current context", "retain" to "Retain authorized observations", "act" to "Allow policy-checked responses").forEach { (key, label) ->
                    Row { Checkbox(item.getBoolean(key), enabled = state.canManage(), onCheckedChange = { value ->
                        val grants = JSONObject().put("perceive", item.getBoolean("perceive")).put("retain", item.getBoolean("retain")).put("act", item.getBoolean("act")).put(key, value)
                        reviewChange(session, "assistance", change("source", item.getString("id"), grants))
                    }); Text(label, Modifier.weight(1f).padding(top = 12.dp)) }
                }
            }
        } }
    }
    PreferenceGroup("Awareness mode", flat = true) {
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("manual" to "Manual", "trigger_only" to "Selected triggers", "sentry" to "Sentry").forEach { (value, label) ->
                FilterChip(selected = mode == value, onClick = { mode = value }, enabled = state.canManage(), label = { Text(label) })
            }
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("passive", "aware", "guard", "away", "sleep").forEach { value ->
                FilterChip(selected = attention == value, onClick = { attention = value }, enabled = state.canManage(), label = { Text(value.replaceFirstChar { it.uppercase() }) })
            }
        }
        sources.forEach { item ->
            val id = item.getString("id")
            Row { Checkbox(id in selected, enabled = state.canManage() && item.getBoolean("perceive"), onCheckedChange = { checked -> selected = if (checked) selected + id else selected - id }); Text(id, Modifier.padding(top = 12.dp)) }
        }
        Row { Checkbox(interrupts, { interrupts = it }, enabled = state.canManage()); Text("Allow policy-checked interruptions", Modifier.weight(1f).padding(top = 12.dp)) }
        OscarButton(onClick = { reviewChange(session, "assistance", change("sentry", "awareness", JSONObject().put("mode", mode).put("state", attention)
            .put("source_ids", JSONArray(selected.sorted())).put("trigger_keys", current.getJSONArray("trigger_keys")).put("allow_interrupt", interrupts))) },
            enabled = state.canManage(), modifier = Modifier.fillMaxWidth()) { Text("Review awareness change") }
    }
    SupportingDetails("Awareness & privacy") {
        Text("Perception, durable retention and action are separate signed grants. These controls configure connected sources. Capture still requires Android or provider permission, and source readiness remains separate from configuration. This screen never starts microphone or camera capture.", style = MaterialTheme.typography.bodySmall)
        TextButton(onClick = privacy) { Text("Android capture permissions") }
    }
}

@Composable internal fun CurrentBrief(session: CoreSession, state: MobileState) {
    var now by remember(state.epoch) { mutableLongStateOf(0) }
    LaunchedEffect(state.epoch, state.dayBrief) {
        while (state.dayBrief != null) {
            now = state.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime())
            kotlinx.coroutines.delay(1000)
        }
    }
    PreferenceGroup("Your day", flat = true) {
        OscarButton(onClick = { session.dayBrief() }, enabled = state.canManage(), outlined = true,
            modifier = Modifier.fillMaxWidth()) { Text("Refresh current context") }
        state.dayBrief?.takeUnless { state.privateSuppressed }?.let { brief ->
            Text("Observed ${java.time.Instant.ofEpochMilli((brief.observedAt * 1000).toLong()).atZone(java.time.ZoneId.systemDefault()).toLocalTime().withNano(0)} · read-only", style = MaterialTheme.typography.bodySmall)
            if (brief.sources.isEmpty()) Text("No authorized current context is available.")
            brief.sources.forEach { source ->
                val grant = state.snapshot?.management?.source?.let { JSONObject(it).getJSONObject("sentry").objects("sources", 64) }?.find { it.getString("id") == source.id }
                val account = state.snapshot?.connections?.accounts()?.find { it.getString("id") == source.accountId }
                val authorized = grant?.getBoolean("perceive") == true && grant.getInt("epoch") == source.epoch &&
                    (source.accountId == null || account?.getString("status") == "connected" && account.getInt("generation") == source.accountGeneration)
                val current = authorized && source.state == "current" && source.freshUntil?.let { now > 0 && now < it * 1000 } == true
                Text("${source.id} · ${if (current) source.epistemic.lowercase() else "Needs refresh"}", style = MaterialTheme.typography.titleSmall)
                val value = source.value?.let { runCatching { JSONObject(it) }.getOrNull() }
                if (current && value != null) {
                    if (source.adapter == "time") Text(value.optString("datetime", "Time unavailable"))
                    else if (source.adapter == "calendar") {
                        val events = runCatching { value.objects("events", 8) }.getOrDefault(emptyList())
                        Text("${events.size} observed events")
                        events.forEach { event -> Text(event.optString("summary", event.optString("subject", "Calendar event")).take(200), style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
            Text("${brief.overlaps} overlapping intervals in this observation${if (brief.incomplete) " · incomplete calendar coverage" else ""}.", style = MaterialTheme.typography.bodySmall)
            Text("Refreshing context grants no authority to change your schedule.", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable private fun AddContextSource(session: CoreSession, state: MobileState) {
    var id by remember(state.epoch) { mutableStateOf("") }
    var calendar by remember(state.epoch) { mutableStateOf(false) }
    var timezone by remember(state.epoch) { mutableStateOf(java.time.ZoneId.systemDefault().id) }
    var accountId by remember(state.epoch) { mutableStateOf("") }
    var calendarId by remember(state.epoch) { mutableStateOf("primary") }
    var retain by remember(state.epoch) { mutableStateOf(false) }
    val accounts = state.snapshot?.connections?.accounts().orEmpty().filter { account ->
        account.getString("status") == "connected" && account.objects("services", 64).any { service ->
            val scopes = service.getJSONArray("scopes").texts(128)
            service.getString("id") == "google.calendar" && "https://www.googleapis.com/auth/calendar.readonly" in scopes ||
                service.getString("id") == "microsoft.graph" && "Calendars.Read" in scopes
        }
    }
    SupportingDetails("Connect current context") {
        OscarField(id, { id = it.take(80) }, label = "Source name", modifier = Modifier.fillMaxWidth())
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = !calendar, onClick = { calendar = false }, label = { Text("Time and date") })
            FilterChip(selected = calendar, onClick = { calendar = true }, label = { Text("Connected calendar") })
        }
        if (!calendar) OscarField(timezone, { timezone = it.take(100) }, label = "Timezone", modifier = Modifier.fillMaxWidth())
        else {
            if (accounts.isEmpty()) Text("Connect an account with calendar read permission first.")
            accounts.forEach { account -> FilterChip(selected = accountId == account.getString("id"), onClick = { accountId = account.getString("id") }, label = { Text(account.getString("alias")) }) }
            OscarField(calendarId, { calendarId = it.take(160) }, label = "Calendar ID", modifier = Modifier.fillMaxWidth())
        }
        Row { Checkbox(retain, { retain = it }); Text("Retain selected observations for one hour", Modifier.weight(1f).padding(top = 12.dp)) }
        Text("Updates every 30 seconds after you select the source in Sentry. Calendar reads cover the next 24 hours, up to eight events; additional pages remain incomplete. No action authority is granted.", style = MaterialTheme.typography.bodySmall)
        val account = accounts.find { it.getString("id") == accountId }
        OscarButton(onClick = {
            val value = JSONObject().put("id", id).put("adapter", if (calendar) "calendar" else "time")
                .put("entity_id", if (calendar) "calendar:$id" else "core").put("interval_seconds", 30).put("retain", retain).put("retention_seconds", 3600)
            if (calendar) value.put("account_id", accountId).put("account_generation", account!!.getInt("generation")).put("calendar_id", calendarId).put("horizon_seconds", 86400)
            else value.put("timezone", timezone)
            reviewChange(session, "assistance", change("source_create", id, value))
        }, enabled = state.canManage() && id.matches(Regex("[A-Za-z0-9_.:/-]{1,80}")) && (!calendar || account != null), modifier = Modifier.fillMaxWidth()) { Text("Review context source") }
    }
}
