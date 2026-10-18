package io.dawnlight.oscar.mobile

import org.json.JSONObject
import java.security.MessageDigest
import java.nio.ByteBuffer

data class Approval(
    val id: String, val signingPayload: String, val expiresAt: Long, val operation: String,
    val description: String, val target: String, val capability: String, val reason: String,
    val consequence: String, val policyReason: String, val review: String, val exactRequest: String,
    val scope: String, val nodeId: String, val sessionId: String,
    val generation: Int?,
) {
    fun material(): JSONObject = JSONObject(String(java.util.Base64.getDecoder().decode(signingPayload), Charsets.UTF_8)).getJSONObject("material")
    fun current(state: MobileState, now: Long): Boolean = state.link == Link.CONNECTED && state.approval == this && state.coreNow(now) < expiresAt &&
        (operation !in setOf("approve", "retry", "reply") || !state.privateSuppressed) &&
        (if (operation == "reply") state.replyPreview?.let { acceptsReply(it) } == true
        else state.snapshot?.tasks?.any { it.id == material().getString("task_id") && it.target == target && it.generation == generation && operation in it.actions &&
            (scope != "grid:approve" || it.reviewDigest == material().getString("digest") && it.capability == capability) } == true)
    fun acceptsReply(text: String): Boolean = operation == "reply" && text.length in 1..500 && NotificationBoundary.hash(text) == material().getString("text_hash")
    fun acceptsPermit(permit: JSONObject): Boolean = operation == "reply" &&
        listOf("package", "key_hash", "text_hash").all { permit.get(it) is String && permit.getString(it) == material().getString(it) } && permit.getString("id") == id
    companion object {
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
