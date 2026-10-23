package io.dawnlight.oscar.mobile

import org.json.JSONObject

data class SentryAlert(val id: String, val source: String, val key: String, val expires: Long, val simulated: Boolean)

/** Only generic metadata crosses this surface; source values stay in authorized current context. */
internal fun parseSentryAlerts(management: ManagementView?, now: Long): List<SentryAlert> {
    if (management == null || now <= 0) return emptyList()
    val sentry = JSONObject(management.source).getJSONObject("sentry")
    if (!sentry.has("alerts")) return emptyList()
    val notices = sentry.objects("alerts", 16)
    val sources = sentry.objects("sources", 64)
    val selected = sentry.getJSONArray("source_ids").texts(32)
    val triggers = sentry.getJSONArray("trigger_keys").texts(32)
    val enabled = sentry.getString("mode") != "manual" && sentry.getString("state") != "sleep" && sentry.getBoolean("allow_interrupt")
    val result = notices.mapNotNull { item ->
        val id = item.bounded("id", 64); require(id.matches(Regex("[a-f0-9]{64}")))
        val source = item.bounded("source_id", 160)
        val key = item.bounded("key", 160)
        item.bounded("observation_id", 160)
        val epoch = item.get("source_epoch"); require(epoch is Int && epoch > 0)
        val generation = item.get("generation"); require(generation is Int && generation > 0)
        val expiry = item.getDouble("fresh_until"); require(expiry.isFinite() && expiry > 0)
        val expires = (expiry * 1000).toLong()
        require(item.get("simulated") is Boolean)
        require(item.getJSONArray("policy_ids").texts(64).isNotEmpty())
        val grant = sources.find { it.getString("id") == source }
        if (!enabled || source !in selected || key !in triggers || generation != sentry.getInt("generation") ||
            grant == null || grant.getInt("epoch") != epoch || !grant.getBoolean("perceive") || !grant.getBoolean("act") ||
            expires <= now || expires - now > 60_000) null
        else SentryAlert(id, source, key, expires, item.getBoolean("simulated"))
    }
    require(result.map { it.id }.distinct().size == result.size)
    return result
}
