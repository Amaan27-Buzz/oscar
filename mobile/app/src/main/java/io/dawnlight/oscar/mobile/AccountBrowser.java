package io.dawnlight.oscar.mobile;

import org.json.JSONObject;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.io.*;

/** One explicit, ephemeral provider enrollment. Codes stay outside Compose, logs and durable storage. */
final class AccountBrowser implements AutoCloseable {
    final String id, url, state;
    final long expiresAt;
    final URI redirect;
    private volatile ServerSocket listener;
    AccountBrowser(JSONObject enrollment, long now) throws Exception {
        id = text(enrollment, "id", 128); url = text(enrollment, "url", 8192);
        double expires = enrollment.getDouble("expires_at");
        if (!Double.isFinite(expires) || expires * 1000 <= now || expires * 1000 > now + 600000) throw new SecurityException("Expired enrollment");
        expiresAt = (long)(expires * 1000);
        URI provider = new URI(url); redirect = new URI(text(enrollment, "redirect_uri", 8192));
        boolean known = "accounts.google.com".equals(provider.getHost()) && "/o/oauth2/v2/auth".equals(provider.getPath()) ||
            "login.microsoftonline.com".equals(provider.getHost()) && provider.getPath().endsWith("/oauth2/v2.0/authorize");
        if (!known || !"https".equals(provider.getScheme()) || provider.getPort() != -1 && provider.getPort() != 443 || provider.getRawUserInfo() != null || provider.getFragment() != null)
            throw new SecurityException("Verified provider endpoint required");
        if (!"http".equals(redirect.getScheme()) || !"127.0.0.1".equals(redirect.getHost()) || redirect.getPort() < 1024 || redirect.getPort() > 65535 ||
            redirect.getRawUserInfo() != null || redirect.getRawQuery() != null || redirect.getFragment() != null || redirect.getRawPath().length() > 200)
            throw new SecurityException("Exact IPv4 loopback callback required");
        Map<String,String> query = pairs(provider.getRawQuery()); state = query.get("state");
        if (state == null || state.length() < 24 || state.length() > 512 || !redirect.toString().equals(query.get("redirect_uri")))
            throw new SecurityException("Provider callback binding rejected");
    }
    private static String text(JSONObject object, String key, int max) throws Exception {
        Object value = object.get(key);
        if (!(value instanceof String) || ((String)value).isEmpty() || ((String)value).length() > max || ((String)value).chars().anyMatch(Character::isISOControl))
            throw new SecurityException("Invalid enrollment");
        return (String)value;
    }
    static Map<String,String> pairs(String query) throws Exception {
        if (query == null || query.length() > 16000) throw new SecurityException("Missing callback parameters");
        Map<String,String> result = new HashMap<>();
        for (String item : query.split("&", -1)) {
            String[] pair = item.split("=", 2);
            if (pair.length != 2) throw new SecurityException("Invalid callback parameters");
            String key = URLDecoder.decode(pair[0], "UTF-8"), value = URLDecoder.decode(pair[1], "UTF-8");
            if (result.put(key, value) != null || key.chars().anyMatch(Character::isISOControl) || value.chars().anyMatch(Character::isISOControl))
                throw new SecurityException("Ambiguous callback parameters");
        }
        return result;
    }
    String callback(String request) throws Exception {
        if (request.length() > 16000 || !request.endsWith("\r\n\r\n")) throw new SecurityException("Invalid callback request");
        String[] lines = request.split("\r\n"), first = lines[0].split(" ", -1);
        if (first.length != 3 || !"GET".equals(first[0]) || !"HTTP/1.1".equals(first[2]) || !first[1].startsWith("/") || first[1].startsWith("//"))
            throw new SecurityException("Invalid callback request");
        String host = null;
        for (int i = 1; i < lines.length; i++) {
            int colon = lines[i].indexOf(':'); if (colon < 1) throw new SecurityException("Invalid callback header");
            if ("host".equalsIgnoreCase(lines[i].substring(0, colon))) {
                if (host != null) throw new SecurityException("Ambiguous callback host");
                host = lines[i].substring(colon + 1).trim();
            }
        }
        if (!("127.0.0.1:" + redirect.getPort()).equals(host)) throw new SecurityException("Callback host rejected");
        URI callback = redirect.resolve(new URI(first[1]));
        if (!redirect.getScheme().equals(callback.getScheme()) || !redirect.getAuthority().equals(callback.getAuthority()) || !redirect.getRawPath().equals(callback.getRawPath()) || callback.getFragment() != null)
            throw new SecurityException("Callback path rejected");
        Map<String,String> query = pairs(callback.getRawQuery()); String code = query.get("code");
        if (!state.equals(query.get("state")) || query.containsKey("error") || code == null || code.isEmpty() || code.length() > 4096)
            throw new SecurityException("Callback authorization rejected");
        return code;
    }
    void bind() throws Exception {
        listener = new ServerSocket(); listener.setReuseAddress(false);
        listener.bind(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), redirect.getPort()), 2); listener.setSoTimeout(1000);
    }
    static String readRequest(Socket socket) throws Exception {
        long deadline = System.nanoTime() + 2_000_000_000L;
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(); InputStream input = socket.getInputStream();
        while (bytes.size() < 16000) {
            long remaining = deadline - System.nanoTime();
            if (remaining <= 0 || Thread.currentThread().isInterrupted()) throw new SocketTimeoutException("Callback read deadline exceeded");
            socket.setSoTimeout((int)Math.max(1, Math.min(2000, (remaining + 999999) / 1000000)));
            int next = input.read(); if (next < 0) break; bytes.write(next);
            byte[] data = bytes.toByteArray(); int n = data.length;
            if (n >= 4 && data[n-4] == 13 && data[n-3] == 10 && data[n-2] == 13 && data[n-1] == 10)
                return bytes.toString("UTF-8");
        }
        throw new SecurityException("Incomplete or oversized callback request");
    }
    String await() throws Exception {
        long deadline = System.nanoTime() + 600_000_000_000L;
        while (System.currentTimeMillis() < expiresAt && System.nanoTime() < deadline && listener != null && !listener.isClosed()) {
            try (Socket socket = listener.accept()) {
                String code = null;
                try { code = callback(readRequest(socket)); } catch (Exception rejected) { /* No code or request enters diagnostics. */ }
                if (System.currentTimeMillis() >= expiresAt || System.nanoTime() >= deadline || listener == null || listener.isClosed())
                    throw new SecurityException("Enrollment expired or cancelled");
                String body = code == null ? "Callback rejected. Return to OSCAR." : "Authorization received. Return to OSCAR to finish connecting.";
                String response = "HTTP/1.1 " + (code == null ? "400 Bad Request" : "200 OK") + "\r\nContent-Type: text/plain\r\nCache-Control: no-store\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; frame-ancestors 'none'\r\nConnection: close\r\nContent-Length: " + body.length() + "\r\n\r\n" + body;
                socket.getOutputStream().write(response.getBytes(StandardCharsets.UTF_8));
                if (code != null && System.currentTimeMillis() < expiresAt) return code;
            } catch (SocketTimeoutException ignored) { }
        }
        throw new SecurityException("Enrollment expired or cancelled");
    }
    public void close() { ServerSocket socket = listener; listener = null; if (socket != null) try { socket.close(); } catch (Exception ignored) { } }
}
