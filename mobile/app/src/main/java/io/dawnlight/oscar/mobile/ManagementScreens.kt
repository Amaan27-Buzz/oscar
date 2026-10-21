package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import org.json.JSONObject

internal fun MobileState.canManage(): Boolean = remote && link == Link.CONNECTED && !privateSuppressed && !busy && snapshot?.management != null &&
    observedAt > 0 && System.currentTimeMillis() - observedAt in 0..15_000
internal fun reviewChange(session: CoreSession, family: String, change: JSONObject) {
    if (!session.reviewManagement(family, change)) session.message("A fresh trusted owner connection is required. Refresh and review again.")
}
internal fun change(operation: String, id: String, value: JSONObject = JSONObject()) = JSONObject().put("operation", operation).put("id", id).put("value", value)

@Composable fun AccessScreen(session: CoreSession, state: MobileState) {
    val view = state.snapshot?.management
    val accounts = state.snapshot?.connections
    var lifetime by remember(state.epoch) { mutableStateOf(900) }
    val now = state.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime())
    val expired = view?.expires?.let { it <= now } == true
    IllustratedIntro("Access", "On your terms.", R.drawable.oscar_orb)
    PreferenceGroup("Current mode", flat = true) {
        FeatureRow(if (view == null) "Access readback unavailable" else if (expired) "Delegation expired" else when (view.mode) { "full" -> "Full Access"; "secure" -> "Secure"; else -> "Ask" },
            if (view == null) "Connect to your trusted Core to inspect authority." else if (view.mode == "ask") "Core requires approval for protected work."
            else "${view.status} · expires ${java.time.Instant.ofEpochMilli(view.expires!!).atZone(java.time.ZoneId.systemDefault()).toLocalTime().withNano(0)}", "Shield")
        if (view != null && view.mode != "ask") OscarButton(onClick = { session.revokeAuthority() }, enabled = !state.busy && state.link == Link.CONNECTED,
            outlined = true, modifier = Modifier.fillMaxWidth().testTag("revokeDelegation")) { Text("Return to Ask now") }
    }
    PreferenceGroup("Delegation lifetime", flat = true) {
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf(900 to "15 minutes", 3600 to "1 hour", 28800 to "8 hours").forEach { (seconds, label) ->
                FilterChip(selected = lifetime == seconds, onClick = { lifetime = seconds }, label = { Text(label) })
            }
        }
    }
    listOf("secure" to "Secure", "full" to "Full Access").forEach { (mode, label) ->
        TactileSurface(Modifier.fillMaxWidth()) {
            FeatureRow(label, if (mode == "full") "Supported consequential actions proceed without OSCAR per-action prompts."
                else "Ordinary delegated work proceeds; protected actions still need consent.", if (mode == "full") "Door" else "Shield")
            OscarButton(onClick = { if (view != null && accounts != null) reviewChange(session, "authority", delegationRequest(view, accounts, mode, lifetime)) },
                enabled = state.canManage() && accounts != null && !accounts.truncated && !expired,
                modifier = Modifier.fillMaxWidth().testTag("activate-$mode")) { Text("Review $label") }
        }
    }
    SupportingDetails("Exact scope & safeguards") {
        Text("Activation covers only the reviewed connected capabilities, sessions and accounts. New connections need a fresh activation. Android and provider permissions, mandatory external approvals and local physical safety remain enforced.", style = MaterialTheme.typography.bodySmall)
        view?.capabilities?.forEach { Text("${it.node} · ${it.id}\n${it.risk} · ${it.permissions.joinToString()}", style = MaterialTheme.typography.bodySmall) }
        accounts?.accounts()?.filter { it.getString("status") == "connected" }?.forEach { Text("Account: ${it.getString("alias")} · generation ${it.getInt("generation")}", style = MaterialTheme.typography.bodySmall) }
        if (view?.askRules?.isNotEmpty() == true) Text("Full Access explicitly resolves these ASK rules for this bounded delegation: ${view.askRules.joinToString()}")
        Text("Owner confirmation signs the exact scope and lifetime. Core checks current policy and capabilities again. Returning to Ask withdraws standing authority; it cannot undo prior effects.", style = MaterialTheme.typography.bodySmall)
    }
    if (view == null || accounts == null || accounts.truncated || expired) TextButton(onClick = session::refreshNow) { Text("Refresh authority readback") }
}

@Composable private fun ScheduleFields(start: String, setStart: (String) -> Unit, interval: String, setInterval: (String) -> Unit, runs: String, setRuns: (String) -> Unit) {
    OscarField(start, { setStart(it.take(32)) }, label = "First run · local time (2026-10-22T09:00)", modifier = Modifier.fillMaxWidth())
    OscarField(interval, { setInterval(it.filter(Char::isDigit).take(8)) }, label = "Repeat every seconds · leave empty for once", modifier = Modifier.fillMaxWidth())
    OscarField(runs, { setRuns(it.filter(Char::isDigit).take(3)) }, label = "Maximum runs · 1 to 100", modifier = Modifier.fillMaxWidth())
    Text("An empty first-run time starts when enabled. Repeating runs must be at least 60 seconds apart. Missed runs do not burst on reconnect.", style = MaterialTheme.typography.bodySmall)
}
@Composable fun AutomationsScreen(session: CoreSession, state: MobileState, page: String, navigate: (String) -> Unit, converse: (String) -> Unit) {
    val caps = state.snapshot?.management?.capabilities.orEmpty().filter { it.kind == "file_write" }
    var selected by remember(state.epoch) { mutableStateOf("") }
    val cap = caps.find { "${it.node}/${it.id}" == selected } ?: caps.firstOrNull()
    var name by remember(state.epoch) { mutableStateOf("") }
    var goal by remember(state.epoch) { mutableStateOf("") }
    var path by remember(state.epoch) { mutableStateOf("") }
    var content by remember(state.epoch) { mutableStateOf("") }
    var start by remember(state.epoch) { mutableStateOf("") }
    var interval by remember(state.epoch) { mutableStateOf("") }
    var runs by remember(state.epoch) { mutableStateOf("1") }
    var editing by remember(state.epoch) { mutableStateOf<String?>(null) }
    var instructions by remember(state.epoch) { mutableStateOf(true) }
    var node by remember(state.epoch) { mutableStateOf("") }
    var retain by remember(state.epoch) { mutableStateOf(false) }
    val procedures = state.snapshot?.management?.source?.let { JSONObject(it).optJSONArray("procedures") }?.let { array ->
        require(array.length() <= 64); (0 until array.length()).map { array.getJSONObject(it) }
    }.orEmpty()
    val schedule = runCatching { routineSchedule(start, interval, runs) }.getOrNull()
    val routine = if (schedule == null || name.isBlank() || goal.isBlank()) null else if (instructions)
        change("create_natural", "new", JSONObject(schedule.toString()).put("name", name).put("instruction", goal).put("node_id", node).put("conditions", org.json.JSONArray()))
    else if (cap == null) null else runCatching { fileRoutine(name, goal, path, content, cap, schedule) }.getOrNull()
    if (page == "Create") {
        IllustratedIntro("What should\nOSCAR do?", artwork = R.drawable.oscar_orb)
        StatusLabel("A continuing responsibility · exact signed review")
        OscarField(name, { name = it.take(80) }, label = "Name", modifier = Modifier.fillMaxWidth())
        OscarField(goal, { goal = it.take(512) }, label = "Responsibility", minLines = 2, modifier = Modifier.fillMaxWidth().testTag("automationDraft"))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = instructions, onClick = { instructions = true }, label = { Text("Action instructions") })
            FilterChip(selected = !instructions, onClick = { instructions = false }, label = { Text("Exact file contents") })
        }
        if (instructions) {
            Text("One explicit action per line, such as ‘What is 2 plus 3?’ or ‘Write agenda.txt with text Ready for review’. Core resolves exact available executors; ambiguous requests are rejected. Your review shows every compiled step.", style = MaterialTheme.typography.bodySmall)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(selected = node.isEmpty(), onClick = { node = "" }, label = { Text("Choose an unambiguous executor") })
                state.snapshot?.management?.capabilities.orEmpty().map { it.node }.distinct().forEach { id ->
                    FilterChip(selected = node == id, onClick = { node = id }, label = { Text(id) })
                }
            }
        } else {
        Text("Write a file on a connected executor", style = MaterialTheme.typography.titleMedium)
        if (caps.isEmpty()) StatusLabel("No file-writing capability in this fresh Core readback.")
        caps.forEach { candidate -> FilterChip(selected = cap == candidate, onClick = { selected = "${candidate.node}/${candidate.id}" }, label = { Text("${candidate.node} · ${candidate.id}") }) }
        OscarField(path, { path = it.take(1024) }, label = "Workspace path", modifier = Modifier.fillMaxWidth())
        OscarField(content, { content = it.take(8192) }, label = "Exact file contents", minLines = 3, modifier = Modifier.fillMaxWidth())
        }
        ScheduleFields(start, { start = it }, interval, { interval = it }, runs, { runs = it })
        OscarButton(onClick = { if (routine != null) reviewChange(session, "assistance", routine) },
            enabled = state.canManage() && routine != null, modifier = Modifier.fillMaxWidth().testTag("createResponsibility")) { Text("Review responsibility") }
        TextButton(onClick = { converse(goal) }, enabled = goal.isNotBlank()) { Text("Discuss with OSCAR") }
        Text("The reviewed task stays within this executor's current workspace and permissions. Each run uses current authority and requires independent result verification.", style = MaterialTheme.typography.bodySmall)
        return
    }
    IllustratedIntro(if (page == "Worker") "Core responsibilities" else "Automations", artwork = R.drawable.illustration_automations, height = 152.dp)
    StatusLabel(if (state.snapshot?.executive == null) "Responsibility readback unavailable" else "Current Core readback")
    state.snapshot?.executive?.forEach { item ->
        key(item.id) { TactileSurface(Modifier.fillMaxWidth()) {
            FeatureRow(item.goal, "${item.state} · ${item.runs} of ${item.maxRuns} runs verified", "Activity")
            if (item.state in setOf("enabled", "paused", "proposed")) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(enabled = state.canManage(), onClick = { reviewChange(session, "assistance", change(if (item.state == "enabled") "pause" else "resume", item.id)) }) { Text(if (item.state == "enabled") "Pause" else "Resume") }
                    TextButton(enabled = state.canManage(), onClick = { editing = if (editing == item.id) null else item.id; start = ""; interval = ""; runs = "${item.maxRuns}" }) { Text("Edit schedule") }
                    TextButton(enabled = state.canManage(), onClick = { reviewChange(session, "assistance", change("delete", item.id)) }) { Text("Retire") }
                }
            }
            if (editing == item.id) {
                ScheduleFields(start, { start = it }, interval, { interval = it }, runs, { runs = it })
                OscarButton(onClick = { if (schedule != null) reviewChange(session, "assistance", change("edit", item.id, schedule)) }, enabled = state.canManage() && schedule != null,
                    modifier = Modifier.fillMaxWidth()) { Text("Review replacement schedule") }
            }
            if (item.state == "completed" && procedures.none { it.getString("source_goal_id") == item.id }) {
                TextButton(enabled = state.canManage() && retain, onClick = { reviewChange(session, "assistance", change("learn", item.id, JSONObject().put("retain", true))) }) { Text("Review saving this procedure") }
            }
        } }
    }
    if (state.snapshot?.executive?.isEmpty() == true) Text("No continuing responsibilities in Core.")
    SupportingDetails("Reusable procedures") {
        Row { Checkbox(retain, { retain = it }); Text("Allow saving reviewed steps and evidence for up to seven days", Modifier.weight(1f).padding(top = 12.dp)) }
        Text("Only independently verified work can be saved. Reuse requires a fresh exact review; a saved procedure grants no authority.", style = MaterialTheme.typography.bodySmall)
        if (procedures.isEmpty()) Text("No reusable procedures saved.")
        procedures.forEach { procedure -> key(procedure.getString("id")) {
            Text(procedure.getString("goal"), style = MaterialTheme.typography.titleSmall)
            Text(if (procedure.getString("state") == "exact_replay_verified") "Exact replay verified" else "Candidate from verified work", style = MaterialTheme.typography.bodySmall)
            TextButton(enabled = state.canManage(), onClick = { reviewChange(session, "assistance", change("reuse", procedure.getString("id"), routineSchedule("", "", "1"))) }) { Text("Review one-time replay") }
            state.snapshot?.executive.orEmpty().filter { it.id != procedure.getString("source_goal_id") && it.state == "completed" && it.goal == procedure.getString("goal") }.forEach { replay ->
                TextButton(enabled = state.canManage() && retain, onClick = { reviewChange(session, "assistance", change("evaluate", procedure.getString("id"), JSONObject().put("retain", true).put("replay_goal_id", replay.id))) }) { Text("Review evaluation of replay ${replay.id.take(8)}") }
            }
        } }
    }
    TactileSurface(Modifier.fillMaxWidth()) { FeatureRow("Workers", "Responsibilities managed by your Core", "Automations", action = { navigate("Worker") }) }
    OscarButton(onClick = { navigate("Create") }, modifier = Modifier.fillMaxWidth()) { Text("New responsibility") }
    SupportingDetails("Responsibility & authority") { Text("Creation, schedule changes, pause, resume and retirement each require an exact owner review. Retiring stops future runs and requests cancellation; effects already performed remain visible in Activity.", style = MaterialTheme.typography.bodySmall) }
}
