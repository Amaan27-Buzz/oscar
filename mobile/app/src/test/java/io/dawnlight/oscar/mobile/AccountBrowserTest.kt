package io.dawnlight.oscar.mobile

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.net.URLEncoder
import java.net.ServerSocket
import java.net.Socket
import java.net.SocketTimeoutException
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class AccountBrowserTest {
    @Test fun mcpResourceCallbackKeepsExactIssuerAndResourceBinding() {
        val resource = "https://mcp.example.com/mcp"
        val issuer = "https://auth.example.com/tenant"
        val value = enrollment().put("authorization_kind", "mcp-resource").put("issuer", issuer)
            .put("issuer_required", true).put("resource", resource)
            .put("authorization_endpoint", "https://auth.example.com/authorize")
            .put("url", "https://auth.example.com/authorize?state=$state&redirect_uri=${URLEncoder.encode(redirect,"UTF-8")}&resource=${URLEncoder.encode(resource,"UTF-8")}&code_challenge_method=S256")
        AccountBrowser(value, 100_000).use { browser ->
            assertThrows(Exception::class.java) { browser.callback(request("state=$state&code=x")) }
            assertThrows(Exception::class.java) { browser.callback(request("state=$state&code=x&iss=https%3A%2F%2Fattacker.test")) }
            assertEquals("synthetic-code", browser.callback(request("state=$state&code=synthetic-code&iss=${URLEncoder.encode(issuer,"UTF-8")}")))
            assertEquals(issuer, browser.responseIssuer)
        }
        assertThrows(Exception::class.java) { AccountBrowser(value.put("resource", "https://other.example/mcp"), 100_000) }
    }
    private val state = "synthetic-owner-state-with-32-characters"
    private val redirect = "http://127.0.0.1:48123/oauth/callback"
    private fun enrollment() = JSONObject().put("id", "pending").put("expires_at", 120)
        .put("redirect_uri", redirect).put("url", "https://accounts.google.com/o/oauth2/v2/auth?state=$state&redirect_uri=${URLEncoder.encode(redirect, "UTF-8")}")
    private fun request(query: String, path: String = "/oauth/callback", host: String = "127.0.0.1:48123") = "GET $path?$query HTTP/1.1\r\nHost: $host\r\n\r\n"
    @Test fun callbackRequiresExactHostPathStateAndUnambiguousCode() {
        AccountBrowser(enrollment(), 100_000).use { browser ->
            assertEquals("synthetic-code", browser.callback(request("state=$state&code=synthetic-code")))
            listOf(request("state=wrong&code=x"), request("state=$state&code=x&state=$state"), request("state=$state&code=x&code=y"),
                request("state=$state&code=x", "/other"), request("state=$state&code=x", host = "example.com:48123"),
                request("state=$state&error=denied"), request("state=$state&code=x%0Ay"),
                request("state=$state&code=x").replace("\r\n\r\n", "\r\nHost: 127.0.0.1:48123\r\n\r\n")).forEach { wire ->
                assertThrows(Exception::class.java) { browser.callback(wire) }
            }
        }
    }
    @Test fun enrollmentRejectsForeignOriginsUnsafeCallbacksAndExpiry() {
        assertThrows(Exception::class.java) { AccountBrowser(enrollment(), 120_000) }
        assertThrows(Exception::class.java) { AccountBrowser(enrollment().put("expires_at", 1000), 100_000) }
        assertThrows(Exception::class.java) { AccountBrowser(enrollment().put("url", "https://example.com/authorize?state=$state"), 100_000) }
        listOf("http://0.0.0.0:48123/oauth/callback", "http://127.0.0.1:80/oauth/callback", "https://127.0.0.1:48123/oauth/callback").forEach {
            assertThrows(Exception::class.java) { AccountBrowser(enrollment().put("redirect_uri", it), 100_000) }
        }
        assertThrows(Exception::class.java) { AccountBrowser(enrollment().put("url", enrollment().getString("url") + "&redirect_uri=https%3A%2F%2Fexample.com"), 100_000) }
    }
    @Test fun slowlyArrivingCallbackCannotExtendTotalReadDeadline() {
        val writer = Executors.newSingleThreadExecutor()
        ServerSocket(0, 1, java.net.InetAddress.getLoopbackAddress()).use { server ->
            Socket(server.inetAddress, server.localPort).use { client ->
                server.accept().use { accepted ->
                    val drip = writer.submit {
                        try { while (!Thread.currentThread().isInterrupted) {
                            client.getOutputStream().write('x'.code)
                            client.getOutputStream().flush()
                            Thread.sleep(80)
                        } } catch (_: Exception) { }
                    }
                    try {
                        val start = System.nanoTime()
                        assertThrows(SocketTimeoutException::class.java) { AccountBrowser.readRequest(accepted) }
                        assertTrue("Incremental input extended callback deadline", System.nanoTime() - start < TimeUnit.SECONDS.toNanos(4))
                    } finally { drip.cancel(true); writer.shutdownNow() }
                }
            }
        }
    }
}
