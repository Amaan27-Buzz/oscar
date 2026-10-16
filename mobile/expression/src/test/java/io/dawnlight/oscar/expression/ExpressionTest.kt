package io.dawnlight.oscar.expression

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ExpressionTest {
    @Test fun reservedCorePublicationsRenewFreshnessWithoutReplayingTransitions() {
        val raw = JSONObject(fixtures.getJSONArray("traces").getJSONObject(0).getJSONArray("steps").getJSONObject(0).getJSONObject("event").toString())
        raw.put("source", JSONObject().put("kind", "core").put("id", "presence:canonical"))
            .put("generation", 1).put("kind", "state").put("operation", "idle").put("delivery", "composed")
            .put("eventTime", 1000000).put("expiresAt", 1030000).put("reducedMotion", true)
        val controller = ExpressionController(Source(SourceKind.CORE, "presence:canonical"), data)
        assertEquals("accepted", controller.receive(raw.toString(), 1000000))
        controller.snapshot(1001000); controller.takeAnimationRecords()
        val fresh = JSONObject(raw.toString()).put("generation", 1025).put("eventTime", 1005000).put("expiresAt", 1035000)
        assertEquals("accepted", controller.receive(fresh.toString(), 1005000))
        assertEquals("idle", controller.snapshot(1031000).resolved.operation)
        assertTrue(controller.takeAnimationRecords().isEmpty())
        assertEquals("stale", controller.receive(raw.toString(), 1006000))
        assertEquals("unknown", controller.snapshot(1035000).resolved.operation)
    }
    private fun resource(name: String) = javaClass.classLoader!!.getResourceAsStream(name)!!.bufferedReader().use { it.readText() }
    private val data = MotionData(resource("motion-v1.json"))
    private val fixtures = JSONObject(resource("fixtures/reference-v1.json"))
    private val source = Source(SourceKind.FIXTURE, "cross-v1")
    private fun poseEquals(message: String, expected: JSONObject, actual: Pose) {
        Pose.keys.forEach { assertEquals("$message: $it", expected.getDouble(it), actual[it], 0.00001) }
    }
    @Test fun sixteenReviewedPosesMatchBeforeExtraction() {
        val cases = fixtures.getJSONArray("poseCases"); assertEquals(16, cases.length())
        for(i in 0 until cases.length()) {
            val item = cases.getJSONObject(i); val scene = item.getJSONObject("scene")
            val study = data.study(data.canonical, Scene(scene.getString("operation"), scene.getString("delivery")))
            poseEquals(item.getString("name"), item.getJSONObject("expected"), data.sample(study,item.getDouble("at"),reduced=item.getBoolean("reduced")).first)
        }
    }
    @Test fun fiveControllerTracesMatchTypescriptSemanticsAndGeometry() {
        val traces = fixtures.getJSONArray("traces"); assertEquals(5,traces.length())
        for(i in 0 until traces.length()) {
            val trace = traces.getJSONObject(i); val controller = ExpressionController(source,data); val steps = trace.getJSONArray("steps")
            for(j in 0 until steps.length()) {
                val step = steps.getJSONObject(j); val now = 1000000L+step.getLong("at")
                val admission = if(step.has("event"))controller.receive(step.getJSONObject("event").toString(),now) else null
                if(step.optBoolean("suspend"))controller.suspend()
                if(step.has("reduce"))controller.setReducedMotion(step.getBoolean("reduce"),now)
                val actual = controller.snapshot(now); val expected = step.getJSONObject("expected"); val title = "${trace.getString("name")}: $j"
                assertEquals(title,if(expected.isNull("admission"))null else expected.getString("admission"),admission)
                assertEquals(title,expected.getString("operation"),actual.resolved.operation)
                assertEquals(title,expected.getString("delivery"),actual.resolved.delivery)
                assertEquals(title,expected.getBoolean("muted"),actual.resolved.muted)
                assertEquals(title,expected.getLong("generation"),actual.generation)
                assertEquals(title,expected.getString("priority"),actual.priority.wire)
                assertEquals(title,expected.getString("animation"),actual.animation.wire)
                assertEquals(title,expected.getBoolean("moving"),actual.moving)
                poseEquals(title,expected.getJSONObject("pose"),actual.pose)
                val records = controller.takeAnimationRecords(); val wanted = expected.getJSONArray("records"); assertEquals(title,wanted.length(),records.size)
                records.forEachIndexed { index,record -> val r=wanted.getJSONObject(index);assertEquals(title,r.getLong("generation"),record.generation);assertEquals(title,r.getString("transitionId"),record.transitionId);assertEquals(title,r.getString("outcome"),record.outcome.wire) }
            }
        }
    }
    @Test fun malformedTypesPrivateFieldsAndUnsafeTimesFailClosed() {
        val event = fixtures.getJSONArray("traces").getJSONObject(0).getJSONArray("steps").getJSONObject(0).getJSONObject("event")
        for((key,value) in listOf("version" to "1","muted" to "false","generation" to 9007199254740992.0,"operation" to "available","privateText" to "synthetic","eventTime" to 1000251,"expiresAt" to 1030001)) {
            val copy=JSONObject(event.toString()).put(key,value)
            assertNull("Invalid $key",Contract.validate(copy.toString(),1000000))
        }
        assertNull(Contract.validate("{broken",1000000))
        val encoded=event.toString()
        for(raw in listOf(encoded+" trailing garbage",encoded.replace("\"version\":","version:"),encoded.replace('"','\''),encoded.replace("\"version\":1","\"version\":01")))assertNull(Contract.validate(raw,1000000))
        assertNotNull(Contract.validate(encoded.replace("\"version\":1","\"version\":1,\"version\":1"),1000000))
    }
    @Test fun longSpeechDoesNotReplayAndAnimationRecordsNeverMeanTaskSuccess() {
        val trace=fixtures.getJSONArray("traces").getJSONObject(0);val controller=ExpressionController(source,data)
        controller.receive(trace.getJSONArray("steps").getJSONObject(0).getJSONObject("event").toString(),1000000)
        val held=controller.snapshot(1000700).pose
        Pose.keys.forEach { assertEquals(held[it],controller.snapshot(1025000).pose[it],0.0) }
        assertEquals("speaking",controller.snapshot(1025000).resolved.operation)
        assertTrue(controller.takeAnimationRecords().all { it.outcome==AnimationOutcome.SETTLED })
    }
    @Test fun sharedMalformedWireCorpusIsRejected() {
        val cases=fixtures.getJSONArray("malformedInputs");assertEquals(8,cases.length())
        for(i in 0 until cases.length()) { val fixture=cases.getJSONObject(i);assertNull(fixture.getString("name"),Contract.validate(fixture.getString("raw"),1000000)) }
    }
}
