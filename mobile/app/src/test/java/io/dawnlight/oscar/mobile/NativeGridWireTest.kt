package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.security.MessageDigest

class NativeGridWireTest {
    private fun delivery(): JSONObject {
        val action = JSONObject("""{"id":"action","task_id":"task","correlation_id":"correlation","capability_id":"android.ui.set_text","parameters":{"package":"example.synthetic","target":"example.synthetic:id/input","value":"Synthetic café"},"idempotency_key":"task","initiator":"owner"}""")
        val review = JSONObject().put("action", action).put("target", "phone").put("workspace", "selected-apps").put("deadline_ms", 2000)
        val digest = MessageDigest.getInstance("SHA-256").digest(canonical(review).toByteArray()).joinToString("") { "%02x".format(it.toInt() and 255) }
        return JSONObject().put("id", "delivery").put("kind", "action").put("node_id", "phone").put("session_id", "session")
            .put("task_id", "task").put("lease_id", "lease").put("action", action).put("deadline_ms", 2000).put("workspace", "selected-apps")
            .put("review_digest", digest).put("approved", true).put("parameters", JSONObject(action.getJSONObject("parameters").toString()))
    }
    private fun parse(value: JSONObject) = NativeGridDelivery.parse(value, "phone", "session", "selected-apps", 1000)
    private fun rejected(value: JSONObject) { try { parse(value); fail("Invalid remote delivery accepted") } catch (_: IllegalArgumentException) { } }

    @Test fun deliveryPinsExactNativeActionAndMonotonicDeadline() {
        val parsed = parse(delivery())
        val action = parsed.native("local-generation", 500, 1000)
        assertEquals(1500L, action.deadlineElapsed)
        assertEquals("local-generation", action.generation)
        assertEquals("android.ui.set_text", action.capability)
        assertEquals("Synthetic café", action.value)
    }
    @Test fun substitutionWrongIdentityScopeLeaseAndExpiredDeadlineAreRejected() {
        listOf("node_id" to "wrong", "session_id" to "wrong", "workspace" to "wrong", "kind" to "unknown", "lease_id" to "", "review_digest" to "0".repeat(64)).forEach { (field, value) -> rejected(delivery().put(field, value)) }
        rejected(delivery().put("deadline_ms", 1000)); rejected(delivery().put("deadline_ms", 181001))
        val changed = delivery(); changed.getJSONObject("parameters").put("value", "different"); rejected(changed)
        rejected(delivery().put("hidden_authority", true))
    }
    @Test fun independentReadbackCanOnlyInspectOriginalSelectedPackage() {
        val readback = delivery().put("kind", "readback").put("parameters", JSONObject("""{"package":"example.synthetic","target":"","value":""}"""))
        assertEquals("android.ui.inspect", parse(readback).native("generation", 500, 1000).capability)
        val wrong = JSONObject(readback.toString()); wrong.getJSONObject("parameters").put("package", "example.other"); rejected(wrong)
        val mutation = JSONObject(readback.toString()); mutation.getJSONObject("parameters").put("value", "repeat mutation"); rejected(mutation)
    }
    @Test fun authorityPinHasNoOfflineExtensionAndCannotAcceptNegativeEpoch() {
        val value = delivery().put("authority", JSONObject().put("epoch", 7).put("task_generation", 2).put("expires_at_ms", 1500))
        assertEquals(7L, parse(value).authorityEpoch)
        assertEquals(2L, parse(value).taskGeneration)
        assertEquals(canonical(value.getJSONObject("authority")), canonical(parse(value).checkRequest().getJSONObject("authority")))
        assertTrue(parse(value).acceptsCheck(JSONObject().put("authorized", true).put("authority", value.getJSONObject("authority"))))
        assertFalse(parse(value).acceptsCheck(JSONObject().put("authorized", true)))
        val replaced = JSONObject(value.getJSONObject("authority").toString()).put("epoch", 8)
        assertFalse(parse(value).acceptsCheck(JSONObject().put("authorized", true).put("authority", replaced)))
        value.getJSONObject("authority").put("expires_at_ms", 999); rejected(value)
        value.getJSONObject("authority").put("expires_at_ms", 1500).put("epoch", -1); rejected(value)
    }
    @Test fun reportedNativeReceiptNeverPromotesAndroidReturnToVerified() {
        val parsed = parse(delivery())
        val receipt = parsed.receipt(NativeResult("delivery", "task", "reported", "Accepted"))
        assertEquals("REPORTED", receipt.getString("status")); assertEquals("action", receipt.getString("action_id"))
        assertTrue(receipt.getBoolean("success")); assertTrue(receipt.isNull("artifact"))
        val blocked = parsed.receipt(NativeResult("delivery", "task", "blocked", "Permission withdrawn"))
        assertFalse(blocked.getBoolean("success")); assertTrue(blocked.isNull("value"))
    }
    @Test fun readbackBoundsUtf8WithoutInventingObservations() {
        val parsed = parse(delivery().put("kind", "readback").put("parameters", JSONObject("""{"package":"example.synthetic","target":"","value":""}""")))
        val result = parsed.receipt(NativeResult("delivery", "task", "reported", "Observed", List(128) { NativeObservation("id-$it", "é".repeat(256), false, false) }))
        val content = result.getString("content")
        assertTrue(content.toByteArray().size <= 8192)
        assertTrue(JSONObject(content).getJSONArray("observations").length() in 1..127)
    }
    @Test fun asciiCanonicalReviewMatchesPythonIncludingUnicodeAndLiteralSlash() {
        assertEquals("{\"a\":\"</\\u00e9\\ud83d\\ude00\",\"b\":[true,null,7]}", canonical(JSONObject("""{"b":[true,null,7],"a":"</é😀"}""")))
    }
    @Test fun exactParameterShapeExcludesHiddenIntentAndUnsafeTargets() {
        listOf(JSONObject("""{"package":"example.synthetic","target":"example.other:id/field","value":"x"}"""),
            JSONObject("""{"package":"example.synthetic","target":"example.synthetic:id/field","value":"x","intent":"root"}""")).forEach {
            try { validateNativeParameters("android.ui.set_text", it); fail("Unscoped native parameters accepted") } catch (_: IllegalArgumentException) { }
        }
    }
}
