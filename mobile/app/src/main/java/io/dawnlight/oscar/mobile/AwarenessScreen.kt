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
    SentryNotices(state)
    CurrentBrief(session, state)
    AddContextSource(session, state)
    val sources = current.objects("sources", 64)
    var mode by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getString("mode")) }
    var attention by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getString("state")) }
    var selected by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getJSONArray("source_ids").texts(32).toSet()) }
    var interrupts by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getBoolean("allow_interrupt")) }
    var triggers by remember(state.epoch, current.getInt("generation")) { mutableStateOf(current.getJSONArray("trigger_keys").texts(32).joinToString(", ")) }
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
        OscarField(triggers, { triggers = it.take(1000) }, label = "Trigger keys, separated by commas", modifier = Modifier.fillMaxWidth())
        Text("Delivery also needs an explicit Allow policy for sentry:deliver. Android notifications need activity alerts and notification permission. No source content appears in an alert.", style = MaterialTheme.typography.bodySmall)
        OscarButton(onClick = { reviewChange(session, "assistance", change("sentry", "awareness", JSONObject().put("mode", mode).put("state", attention)
            .put("source_ids", JSONArray(selected.sorted())).put("trigger_keys", JSONArray(triggers.split(',').map { it.trim() }.filter { it.isNotEmpty() }.distinct())).put("allow_interrupt", interrupts))) },
            enabled = state.canManage() && triggers.split(',').filter { it.isNotBlank() }.let { keys -> keys.size <= 32 && keys.all { it.trim().matches(Regex("[A-Za-z0-9_.:/-]{1,160}")) } }, modifier = Modifier.fillMaxWidth()) { Text("Review awareness change") }
    }
    SupportingDetails("Awareness & privacy") {
        Text("Perception, durable retention and action are separate signed grants. These controls configure connected sources. Capture still requires Android or provider permission, and source readiness remains separate from configuration. This screen never starts microphone or camera capture.", style = MaterialTheme.typography.bodySmall)
        TextButton(onClick = privacy) { Text("Android capture permissions") }
    }
}

@Composable internal fun SentryNotices(state: MobileState) {
    var now by remember(state.epoch) { mutableLongStateOf(0) }
    LaunchedEffect(state.epoch, state.snapshot) {
        while (state.snapshot != null) {
            now = state.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime())
            kotlinx.coroutines.delay(1000)
        }
    }
    val notices = if (state.privateSuppressed || state.link != Link.CONNECTED) emptyList()
        else parseSentryAlerts(state.snapshot?.management, now)
    if (notices.isNotEmpty()) PreferenceGroup("Needs your attention", flat = true) {
        notices.forEach { notice -> Text("${if (notice.simulated) "Simulated · " else ""}${notice.source} · ${notice.key}") }
        Text("A selected source triggered an authorized notice. Check current context before acting.", style = MaterialTheme.typography.bodySmall)
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
            val currentSources = mutableSetOf<String>()
            brief.sources.forEach { source ->
                val grant = state.snapshot?.management?.source?.let { JSONObject(it).getJSONObject("sentry").objects("sources", 64) }?.find { it.getString("id") == source.id }
                val account = state.snapshot?.connections?.accounts()?.find { it.getString("id") == source.accountId }
                val authorized = grant?.getBoolean("perceive") == true && grant.getInt("epoch") == source.epoch &&
                    (source.accountId == null || account?.getString("status") == "connected" && account.getInt("generation") == source.accountGeneration)
                val current = authorized && source.state == "current" && source.freshUntil?.let { now > 0 && now < it * 1000 } == true
                Text("${source.id} · ${if (current) source.epistemic.lowercase() else "Needs refresh"}", style = MaterialTheme.typography.titleSmall)
                val value = source.value?.let { runCatching { JSONObject(it) }.getOrNull() }
                if (current && value != null) {
                    currentSources.add(source.id)
                    if (source.adapter == "time") Text(value.optString("datetime", "Time unavailable"))
                    else if (source.adapter == "weather") {
                        Text(value.optString("place", "Selected place"))
                        Text("${value.optString("temperature_c", "Unknown")} °C · wind ${value.optString("wind_mps", "Unknown")} m/s", style = MaterialTheme.typography.bodySmall)
                        Text("Forecast ${value.optString("forecast_time", "time unavailable")} · updated ${value.optString("updated_at", "time unavailable")}", style = MaterialTheme.typography.bodySmall)
                        Text("MET Norway · CC BY 4.0 · https://creativecommons.org/licenses/by/4.0/", style = MaterialTheme.typography.bodySmall)
                    } else if (source.adapter == "calendar") {
                        val events = runCatching { value.objects("events", 8) }.getOrDefault(emptyList())
                        Text("${events.size} observed events")
                        events.forEach { event -> Text(event.optString("summary", event.optString("subject", "Calendar event")).take(200), style = MaterialTheme.typography.bodySmall) }
                    } else if (source.adapter == "connected_tasks") {
                        if (!value.optBoolean("complete")) Text("Task list coverage is incomplete.")
                        runCatching { value.objects("tasks", 8) }.getOrDefault(emptyList()).forEach { task ->
                            Text(task.optString("title", "Untitled task").take(1024), style = MaterialTheme.typography.bodySmall)
                            Text(task.optString("status", "Status unavailable"), style = MaterialTheme.typography.bodySmall)
                            if (task.has("due_date")) Text("Due date ${task.getString("due_date")} (date only)", style = MaterialTheme.typography.bodySmall)
                            task.optJSONObject("due_time")?.let { due -> Text("Due ${due.optString("dateTime")} · ${due.optString("timeZone")}", style = MaterialTheme.typography.bodySmall) }
                            if (task.has("importance")) Text(task.getString("importance"), style = MaterialTheme.typography.bodySmall)
                        }
                    } else if (source.adapter == "android") {
                        Text("Selected phone metadata. Playback does not establish attention.", style = MaterialTheme.typography.bodySmall)
                        if (!value.optBoolean("notifications_available")) Text("Notification context unavailable.")
                        else runCatching { value.objects("notifications", 8) }.getOrDefault(emptyList()).forEach { item ->
                            Text("${item.optString("package").take(100)} · ${item.optInt("count")} selected notifications", style = MaterialTheme.typography.bodySmall)
                        }
                        if (!value.optBoolean("media_available")) Text("Media context unavailable.")
                        else runCatching { value.objects("media", 8) }.getOrDefault(emptyList()).forEach { item ->
                            val playback = when (item.optInt("state", -1)) { 3 -> "playing"; 2 -> "paused"; 1 -> "stopped"; else -> "other playback state" }
                            Text("${item.optString("package").take(100)} · $playback", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
            if (brief.sources.all { it.id in currentSources }) {
                val attention = brief.attentionLines(currentSources, now / 1000.0)
                if (attention.isNotEmpty()) Text("Reported task attention", style = MaterialTheme.typography.titleSmall)
                attention.forEach { Text(it, style = MaterialTheme.typography.bodySmall) }
                if (brief.attentionFreshUntil?.let { now > 0 && now < it * 1000 } == true) {
                    if (brief.attentionIncomplete) Text("Task attention covers only the selected available tasks.", style = MaterialTheme.typography.bodySmall)
                    if (brief.unknownDueTimes > 0) Text("Some task due dates or times need clarification.", style = MaterialTheme.typography.bodySmall)
                } else if (brief.attentionFreshUntil != null) Text("Refresh to reassess task attention.", style = MaterialTheme.typography.bodySmall)
                Text("${brief.overlaps} overlapping intervals in this observation${if (brief.incomplete) " · incomplete calendar coverage" else ""}.", style = MaterialTheme.typography.bodySmall)
            } else Text("Refresh to reassess task attention and schedule conflicts.", style = MaterialTheme.typography.bodySmall)
            Text("Refreshing context grants no authority to change your schedule.", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable private fun AddContextSource(session: CoreSession, state: MobileState) {
    var id by remember(state.epoch) { mutableStateOf("") }
    var kind by remember(state.epoch) { mutableStateOf("time") }
    var place by remember(state.epoch) { mutableStateOf("") }
    var latitude by remember(state.epoch) { mutableStateOf("") }
    var longitude by remember(state.epoch) { mutableStateOf("") }
    var timezone by remember(state.epoch) { mutableStateOf(java.time.ZoneId.systemDefault().id) }
    var accountId by remember(state.epoch) { mutableStateOf("") }
    var calendarId by remember(state.epoch) { mutableStateOf("primary") }
    var taskListId by remember(state.epoch) { mutableStateOf("") }
    var retain by remember(state.epoch) { mutableStateOf(false) }
    val accounts = state.snapshot?.connections?.accounts().orEmpty().filter { account ->
        account.getString("status") == "connected" && account.objects("services", 64).any { service ->
            val scopes = service.getJSONArray("scopes").texts(128)
            if (kind == "connected_tasks") service.getString("id") == "google.tasks" && "https://www.googleapis.com/auth/tasks.readonly" in scopes ||
                service.getString("id") == "microsoft.graph" && "Tasks.Read" in scopes
            else service.getString("id") == "google.calendar" && "https://www.googleapis.com/auth/calendar.events.readonly" in scopes ||
                service.getString("id") == "microsoft.graph" && "Calendars.Read" in scopes
        }
    }
    SupportingDetails("Connect current context") {
        OscarField(id, { id = it.take(80) }, label = "Source name", modifier = Modifier.fillMaxWidth())
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("time" to "Time and date", "calendar" to "Connected calendar", "connected_tasks" to "Connected tasks", "weather" to "Weather", "android" to "This phone").forEach { (value, label) ->
                FilterChip(selected = kind == value, onClick = { kind = value }, label = { Text(label) })
            }
        }
        if (kind == "time") OscarField(timezone, { timezone = it.take(100) }, label = "Timezone", modifier = Modifier.fillMaxWidth())
        else if (kind == "weather") {
            OscarField(place, { place = it.take(80) }, label = "Place name", modifier = Modifier.fillMaxWidth())
            OscarField(latitude, { latitude = it.take(16) }, label = "Latitude", modifier = Modifier.fillMaxWidth())
            OscarField(longitude, { longitude = it.take(16) }, label = "Longitude", modifier = Modifier.fillMaxWidth())
            Text("Forecast from MET Norway for coordinates you choose. Coordinates are sent to its public weather service; your device location is never requested. Use up to four decimal places. Updates every ten minutes while selected in Sentry.", style = MaterialTheme.typography.bodySmall)
        } else if (kind == "android") {
            Text("Uses this phone's current enrolled session and the app IDs selected in Android capture permissions. Up to eight apps. Only counts and playback state are shared, while OSCAR is open or phone tasks are visibly running. Enable sharing separately in capture permissions, then select this source in Sentry.", style = MaterialTheme.typography.bodySmall)
        } else {
            if (accounts.isEmpty()) Text("Connect an account with ${if (kind == "connected_tasks") "task" else "calendar"} read permission first.")
            accounts.forEach { account -> FilterChip(selected = accountId == account.getString("id"), onClick = { accountId = account.getString("id") }, label = { Text(account.getString("alias")) }) }
            if (kind == "connected_tasks") {
                OscarField(taskListId, { taskListId = it.take(160) }, label = "Task list ID", modifier = Modifier.fillMaxWidth())
                Text("Reads the first eight tasks. Additional pages are marked incomplete. Google due is date-only; Microsoft times keep their timezone. Task notes are excluded.", style = MaterialTheme.typography.bodySmall)
            } else OscarField(calendarId, { calendarId = it.take(160) }, label = "Calendar ID", modifier = Modifier.fillMaxWidth())
        }
        Row { Checkbox(retain, { retain = it }); Text("Retain selected observations for one hour", Modifier.weight(1f).padding(top = 12.dp)) }
        Text("Time, calendar and tasks update every 30 seconds after you select the source in Sentry. Calendar reads cover the next 24 hours, up to eight events; additional pages remain incomplete. No action authority is granted.", style = MaterialTheme.typography.bodySmall)
        val account = accounts.find { it.getString("id") == accountId }
        val weather = weatherSourceValue(id, place, latitude, longitude, retain)
        val phone = if (kind == "android") session.phoneContextSource(id, retain) else null
        OscarButton(onClick = {
            val value = if (kind == "weather") weather!! else if (kind == "android") phone!! else JSONObject().put("id", id).put("adapter", kind)
                .put("entity_id", if (kind in listOf("calendar", "connected_tasks")) "$kind:$id" else "core").put("interval_seconds", 30).put("retain", retain).put("retention_seconds", 3600)
            if (kind == "calendar") value.put("account_id", accountId).put("account_generation", account!!.getInt("generation")).put("calendar_id", calendarId).put("horizon_seconds", 86400)
            else if (kind == "connected_tasks") value.put("account_id", accountId).put("account_generation", account!!.getInt("generation")).put("task_list_id", taskListId)
            else if (kind == "time") value.put("timezone", timezone)
            reviewChange(session, "assistance", change("source_create", id, value))
        }, enabled = state.canManage() && id.matches(Regex("[A-Za-z0-9_.:/-]{1,80}")) && (kind !in listOf("calendar", "connected_tasks") || account != null) && (kind != "connected_tasks" || taskListId.isNotBlank()) && (kind != "weather" || weather != null) && (kind != "android" || phone != null), modifier = Modifier.fillMaxWidth()) { Text("Review context source") }
    }
}

internal fun weatherSourceValue(id: String, place: String, latitude: String, longitude: String, retain: Boolean): JSONObject? {
    fun coordinate(text: String, bound: Double): Double? = text.toDoubleOrNull()?.takeIf {
        it.isFinite() && it >= -bound && it <= bound && java.math.BigDecimal.valueOf(it).stripTrailingZeros().scale() <= 4
    }
    val lat = coordinate(latitude, 90.0) ?: return null
    val lon = coordinate(longitude, 180.0) ?: return null
    if (!id.matches(Regex("[A-Za-z0-9_.:/-]{1,80}")) || place.length !in 1..80 || place.any { it.isISOControl() }) return null
    return JSONObject().put("id", id).put("adapter", "weather").put("entity_id", "weather:$id")
        .put("interval_seconds", 600).put("retain", retain).put("retention_seconds", 3600)
        .put("latitude", lat).put("longitude", lon).put("place", place)
}
