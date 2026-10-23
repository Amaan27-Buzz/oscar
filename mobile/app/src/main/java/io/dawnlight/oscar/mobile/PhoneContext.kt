package io.dawnlight.oscar.mobile

import android.app.KeyguardManager
import android.app.NotificationManager
import android.content.ComponentName
import android.content.Context
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import android.os.SystemClock
import org.json.JSONArray
import org.json.JSONObject
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/** Only explicit local metadata grants; no notification text, track title or recording. */
internal object PhoneContext {
    private val publishing = Mutex()
    private var nextAt = 0L
    private fun prefs(context: Context) = context.getSharedPreferences("permissions", Context.MODE_PRIVATE)
    private fun packages(context: Context, key: String) = prefs(context).getString(key, "").orEmpty().split(',').map(String::trim).filter(String::isNotEmpty).toSet()
    private fun access(context: Context) = context.getSystemService(NotificationManager::class.java).isNotificationListenerAccessGranted(ComponentName(context, NotificationBoundary::class.java))
    fun configuration(context: Context, client: CoreClient?, id: String, retain: Boolean): JSONObject? {
        if (client?.remote() != true || !client.hasScope("android:perceive")) return null
        val selected = (packages(context, "notification_sources") + packages(context, "native_action_packages")).sorted()
        return phoneSourceValue(client.nodeId(), client.sessionId(), id, selected, retain)
    }
    private fun privacy(context: Context) = listOf("phone_context", "notification_context", "notification_sources", "media_perception", "native_action_packages").joinToString("\n") { "${it}:${prefs(context).all[it]}" } + ":${access(context)}:${context.getSystemService(KeyguardManager::class.java).isKeyguardLocked}"
    internal fun media(context: Context, selected: Set<String>): JSONArray? {
        if (!access(context) || !prefs(context).getBoolean("media_perception", false)) return null
        val allowed = selected.intersect(packages(context, "native_action_packages"))
        if (allowed.isEmpty()) return null
        return try {
            val sessions = context.getSystemService(MediaSessionManager::class.java).getActiveSessions(ComponentName(context, NotificationBoundary::class.java)).filter { it.packageName in allowed }
            if (sessions.size > 8 || sessions.map { it.packageName }.distinct().size != sessions.size || sessions.any { it.playbackState == null }) return null
            JSONArray(sessions.map { JSONObject().put("package", it.packageName).put("state", it.playbackState!!.state) })
        } catch (_: Exception) { null }
    }
    fun retreat(context: Context): Boolean {
        if (!prefs(context).getBoolean("overlay_retreat_media", false) || context.getSystemService(KeyguardManager::class.java).isKeyguardLocked) return false
        val states = media(context, packages(context, "native_action_packages")) ?: return false
        return (0 until states.length()).any { states.getJSONObject(it).getInt("state") == PlaybackState.STATE_PLAYING }
    }
    suspend fun publish(context: Context, call: suspend (String, JSONObject) -> JSONObject) = publishing.withLock {
        if (SystemClock.elapsedRealtime() < nextAt) return@withLock
        nextAt = SystemClock.elapsedRealtime() + PHONE_CONTEXT_PUBLISH_MS
        val privacyStamp = privacy(context)
        publishPhoneContext(call, SystemClock::elapsedRealtime, { privacyStamp == privacy(context) }) { source ->
            val selected = source.getJSONArray("packages").let { values -> require(values.length() in 1..8); (0 until values.length()).map { values.getString(it) }.toSet() }
            val permitted = prefs(context).getBoolean("phone_context", false) && !context.getSystemService(KeyguardManager::class.java).isKeyguardLocked
            val notifications = if (permitted) NotificationBoundary.contextCounts(context, selected) else null
            val media = if (permitted) media(context, selected) else null
            if (notifications == null && media == null) null
            else JSONObject().put("notifications_available", notifications != null).put("notifications", notifications ?: JSONArray())
                .put("media_available", media != null).put("media", media ?: JSONArray())
        }
    }
}

internal const val PHONE_CONTEXT_PUBLISH_MS = 5000L

/** One preparation and one bounded submission; an uncertain submission is never retried. */
internal suspend fun publishPhoneContext(call: suspend (String, JSONObject) -> JSONObject, now: () -> Long,
    valid: () -> Boolean, capture: (JSONObject) -> JSONObject?) {
    val prepared = call("phone_context", JSONObject())
    val received = now()
    val sources = prepared.getJSONArray("sources"); require(sources.length() <= 8)
    val identifiers = mutableSetOf<String>()
    val batch = JSONArray()
    for (index in 0 until sources.length()) {
        if (!valid()) return
        val source = sources.getJSONObject(index)
        require(identifiers.add(source.getString("id")) && source.getLong("epoch") > 0 && source.getLong("sequence") > 0)
        val value = capture(source)
        batch.put(if (value == null) JSONObject().put("withdraw", source.getString("id")).put("epoch", source.getLong("epoch"))
            else phoneContextPayload(source, value, prepared.getLong("observed_at_ms") + now() - received))
    }
    if (batch.length() > 0 && valid()) call("phone_context", JSONObject().put("batch", batch))
}

internal fun phoneContextPayload(source: JSONObject, value: JSONObject, observedAt: Long): JSONObject {
    require(source.getLong("epoch") > 0 && source.getLong("sequence") > 0 && observedAt > 0)
    return JSONObject().put("source_id", source.getString("id")).put("epoch", source.getLong("epoch"))
        .put("sequence", source.getLong("sequence")).put("observed_at_ms", observedAt).put("value", value)
}

internal fun phoneSourceValue(node: String, session: String, id: String, selected: List<String>, retain: Boolean): JSONObject? {
    if (selected.size !in 1..8 || selected.distinct().size != selected.size || selected.any { it.length > 100 || !it.matches(Regex("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) }) return null
    return JSONObject().put("id", id).put("adapter", "android").put("entity_id", "phone:$node")
        .put("interval_seconds", 5).put("retain", retain).put("retention_seconds", 3600)
        .put("node_id", node).put("session_id", session).put("packages", JSONArray(selected))
}
