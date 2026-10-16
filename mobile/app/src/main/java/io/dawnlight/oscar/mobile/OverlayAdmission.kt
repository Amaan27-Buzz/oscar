package io.dawnlight.oscar.mobile

import io.dawnlight.oscar.expression.Contract
import io.dawnlight.oscar.expression.EventKind
import io.dawnlight.oscar.expression.SourceKind
import org.json.JSONObject

/** In-process request fence; never restored after process replacement. */
class OverlayRequests {
    private var token: String? = null
    private var consumed = false
    @Synchronized fun request(): String { token = java.util.UUID.randomUUID().toString(); consumed = false; return token!! }
    @Synchronized fun consume(value: String?): Boolean {
        if (value == null || value != token || consumed) return false
        consumed = true; return true
    }
    @Synchronized fun current(value: String?) = value != null && value == token
    @Synchronized fun pending() = token != null
    @Synchronized fun cancel() { token = null; consumed = false }
    @Synchronized fun cancel(value: String?) { if (value == token) cancel() }
}

/** No window is admitted until all local and canonical Core boundaries pass. */
class OverlayAdmission {
    private var binding: String? = null
    private var source: String? = null
    private var generation = -1L
    var expiresAt = 0L
        private set
    fun admit(response: JSONObject, now: Long, pairing: String, requested: Boolean, permitted: Boolean, unlocked: Boolean, enabled: Boolean): String {
        check(requested && permitted && unlocked && enabled)
        require(response.get("version") == 1 && response.get("visible") is Boolean && response.getBoolean("visible"))
        require(pairing.isNotEmpty() && (binding == null || binding == pairing))
        val raw = response.getJSONObject("expression").toString()
        val event = Contract.validate(raw, now) ?: error("Stale or malformed Core presence")
        require(event.source.kind == SourceKind.CORE && event.source.id.startsWith("presence:") && event.kind == EventKind.STATE)
        require((source == null || source == event.source.id) && event.generation > generation)
        binding = pairing; source = event.source.id; generation = event.generation; expiresAt = event.expiresAt
        return raw
    }
}
