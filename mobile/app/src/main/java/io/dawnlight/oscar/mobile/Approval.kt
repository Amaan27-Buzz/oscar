package io.dawnlight.oscar.mobile

import org.json.JSONObject
import java.security.MessageDigest
import java.nio.ByteBuffer

data class Approval(
    val id: String, val signingPayload: String, val expiresAt: Long, val operation: String,
    val description: String, val target: String, val capability: String, val reason: String,
    val consequence: String, val policyReason: String, val review: String, val exactRequest: String,
    val scope: String, val nodeId: String, val sessionId: String,
    val generation: Int?, val completion: String = "complete", val contextStamp: String? = null,
) {
    fun material(): JSONObject = JSONObject(String(java.util.Base64.getDecoder().decode(signingPayload), Charsets.UTF_8)).getJSONObject("material")
    fun current(state: MobileState, now: Long, elapsedNow: Long? = null): Boolean = state.link == Link.CONNECTED && state.approval == this && state.coreNow(now, elapsedNow) < expiresAt &&
        (operation !in setOf("approve", "retry", "reply") || !state.privateSuppressed) &&
        (if (completion != "complete") !state.privateSuppressed && contextStamp != null && state.snapshot?.managementStamp() == contextStamp
        else if (operation == "reply") state.replyPreview?.let { acceptsReply(it) } == true
        else state.snapshot?.tasks?.any { it.id == material().getString("task_id") && it.target == target && it.generation == generation && operation in it.actions &&
            (scope != "grid:approve" || it.reviewDigest == material().getString("digest") && it.capability == capability) } == true)
    fun acceptsReply(text: String): Boolean = operation == "reply" && text.length in 1..500 && NotificationBoundary.hash(text) == material().getString("text_hash")
    fun acceptsPermit(permit: JSONObject): Boolean = operation == "reply" &&
        listOf("package", "key_hash", "text_hash").all { permit.get(it) is String && permit.getString(it) == material().getString(it) } && permit.getString("id") == id
    companion object {
        /** Management challenges use the same owner key and exact display digest, with a pinned route and proposal. */
        fun management(json: JSONObject, family: String, expected: JSONObject, stamp: String, now: Long): Approval {
            val capability = mapOf("authority" to "authority.manage", "assistance" to "assistance.manage", "management" to "connections.manage")[family]
                ?: error("Unknown management family")
            require(json.bounded("capability", 80) == capability && json.getString("operation") == "approve" && json.getString("scope") == "grid:approve")
            require(!json.has("confirmation") || json.getString("confirmation") == "biometric_or_device_credential")
            val payload = json.bounded("signing_payload", 50_000)
            val claim = JSONObject(String(java.util.Base64.getDecoder().decode(payload), Charsets.UTF_8))
            require(claim.get("version") == 2 && claim.getString("operation") == "approve" && claim.getString("scope") == "grid:approve")
            val deadline = json.get("expires_at_ms"); val signedDeadline = claim.get("expires_at_ms")
            require((deadline is Int || deadline is Long) && (signedDeadline is Int || signedDeadline is Long) && (deadline as Number).toLong() == (signedDeadline as Number).toLong())
            require(now >= 0 && deadline.toLong() > now && deadline.toLong() - now <= 30_250)
            val generation = json.get("generation"); require(generation is Int && generation >= 0 && generation == claim.get("generation"))
            val material = claim.getJSONObject("material")
            require(canonicalJson(material.getJSONObject("change")) == canonicalJson(expected))
            if (family == "authority") require(material.get("epoch") == generation && material.getString("relationship") == material.getString("task_id"))
            else require(material.bounded("digest", 64).matches(Regex("[a-f0-9]{64}")))
            val target = json.bounded("target", 256); require(target == material.getString("target"))
            val review = json.bounded("review", 24_000); val exact = json.bounded("exact_request", 8192)
            require((review + exact).toByteArray().size <= 32_000)
            val reviewed = when (family) {
                "authority" -> material
                "assistance" -> material.getJSONObject("review").also {
                    require(canonicalJson(it.getJSONObject("change")) == canonicalJson(expected))
                }
                else -> expected
            }
            require(canonicalJson(JSONObject(review)) == canonicalJson(reviewed))
            require(claim.getString("display_digest") == displayDigest("approve", "grid:approve", target, review, exact))
            val node = claim.bounded("node_id", 80); val session = claim.bounded("session_id", 80)
            require(listOf(node, session).all { it.matches(Regex("[A-Za-z0-9_-]{1,80}")) } && claim.getString("nonce").matches(Regex("[a-f0-9]{32}")))
            return Approval(json.bounded("challenge_id", 80), payload, deadline.toLong(), "approve", json.bounded("description", 8192).take(256), target,
                capability, json.bounded("reason", 256), json.bounded("consequence", 8192), json.bounded("policy_reason", 256), review, exact,
                "grid:approve", node, session, generation, "${family}_complete", stamp)
        }
        fun displayDigest(vararg fields: String): String {
            val digest = MessageDigest.getInstance("SHA-256")
            fields.forEach { field -> val bytes = field.toByteArray(Charsets.UTF_8); digest.update(ByteBuffer.allocate(4).putInt(bytes.size).array()); digest.update(bytes) }
            return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
        }
        fun parse(json: JSONObject, now: Long = System.currentTimeMillis()): Approval {
            require(json.getString("confirmation") == "biometric_or_device_credential")
            val payload = json.bounded("signing_payload", 16000)
            val claim = JSONObject(String(java.util.Base64.getDecoder().decode(payload), Charsets.UTF_8))
            val version = claim.get("version"); require(version == 1 || version == 2)
            val expires = json.get("expires_at_ms")
            val signedExpires = claim.get("expires_at_ms")
            require((expires is Long || expires is Int) && (signedExpires is Long || signedExpires is Int) && (expires as Number).toLong() == (signedExpires as Number).toLong())
            val deadline = (expires as Number).toLong()
            require(now >= 0 && deadline > now && deadline - now <= 30_250)
            val operation = json.bounded("operation", 16)
            require(operation == claim.getString("operation") && operation in setOf("approve", "deny", "cancel", "retry", "reply"))
            val scope = json.bounded("scope", 256)
            require(scope == claim.getString("scope"))
            val generation = if (operation == "reply") { require(json.isNull("generation") && claim.isNull("generation")); null }
                else { val value = json.get("generation"); require(value is Int && value >= 0 && value == claim.get("generation")); value }
            val material = claim.getJSONObject("material")
            val target = json.bounded("target", 256)
            require((if (operation == "reply") material.getString("package") else material.getString("target")) == target)
            require(if (version == 2) operation == "approve" && scope == "grid:approve" && material.bounded("digest", 64).matches(Regex("[a-f0-9]{64}"))
                else scope == if (operation == "reply") "notifications:reply" else "control:${if (operation == "cancel") "cancel" else "approve"}:$target")
            val review = json.get("review"); val exact = json.get("exact_request")
            require(review is String && exact is String && (review + exact).toByteArray(Charsets.UTF_8).size <= 24_000)
            require(claim.getString("display_digest") == displayDigest(operation, scope, target, review, exact))
            val node = claim.bounded("node_id", 80); val session = claim.bounded("session_id", 80)
            require(listOf(node, session).all { it.matches(Regex("[A-Za-z0-9_-]{1,80}")) })
            require(claim.getString("nonce").matches(Regex(if (version == 2) "[a-f0-9]{32}" else "[a-f0-9]{64}")))
            if (operation != "reply") require(material.bounded("task_id", 80).matches(Regex("[A-Za-z0-9_-]{1,80}")))
            return Approval(json.bounded("challenge_id", 80), payload, deadline, operation,
                json.bounded("description", if (version == 2) 8192 else 256).take(256), target, json.bounded("capability", 80), json.bounded("reason", 256),
                json.bounded("consequence", 256), json.bounded("policy_reason", 256), review, exact, scope, node, session, generation)
        }
    }
}
