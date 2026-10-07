package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.net.ServerSocket
import java.net.InetAddress
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

class CoreTransportTest {
    @Test fun transportBoundsAndCancellationAreReal() {
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val server = ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))
        server.soTimeout = 5000
        val serving = Thread {
            try {
                server.accept().use { socket ->
                    socket.soTimeout = 5000
                    val input = socket.getInputStream()
                    val header = StringBuilder()
                    while (!header.endsWith("\r\n\r\n") && header.length < 16384) {
                        val value = input.read(); if (value < 0) break
                        header.append(value.toChar())
                    }
                    entered.countDown()
                    release.await(5, TimeUnit.SECONDS)
                    socket.getOutputStream().write("HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}".toByteArray())
                }
            } catch (_: Exception) { }
        }
        serving.start()
        try {
            val client = CoreClient(JSONObject().put("url", "http://127.0.0.1:${server.localPort}")
                .put("node_id", "fixture").put("session_id", "fixture").put("token", "synthetic-only"))
            val finished = CountDownLatch(1)
            var accepted = false
            val thread = Thread {
                try { client.call("snapshot", JSONObject()); accepted = true }
                catch (_: Exception) { } finally { finished.countDown() }
            }
            thread.start()
            assertTrue(entered.await(5, TimeUnit.SECONDS))
            client.cancel(); release.countDown()
            assertTrue(finished.await(5, TimeUnit.SECONDS))
            assertFalse(accepted)
            try { client.call("text", JSONObject().put("text", "x".repeat(32769))); fail("Unbounded request accepted") }
            catch (_: IllegalArgumentException) { }
        } finally { release.countDown(); server.close(); serving.join(5000) }
    }
}
