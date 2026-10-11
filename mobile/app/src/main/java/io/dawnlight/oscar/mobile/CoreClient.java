package io.dawnlight.oscar.mobile;

import org.json.JSONObject;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

/** Bounded, no-redirect, no-mutation-retry transport to the same OSCAR Core. */
final class CoreClient {
    private final JSONObject session;
    private volatile HttpURLConnection active;
    void cancel() { HttpURLConnection current = active; if (current != null) current.disconnect(); }
    CoreClient(JSONObject session) throws Exception {
        validateEndpoint(session.getString("url"));
        this.session = session;
    }
    String binding() throws Exception { return NotificationBoundary.hash(session.optString("url") + "\n" + session.optString("node_id") + "\n" + session.optString("session_id")); }
    static void validateEndpoint(String endpoint) throws Exception {
        URI uri = new URI(endpoint);
        boolean local = BuildConfig.DEBUG && "http".equals(uri.getScheme()) &&
            ("127.0.0.1".equals(uri.getHost()) || "localhost".equals(uri.getHost()));
        if ((!"https".equals(uri.getScheme()) && !local) || uri.getHost() == null ||
            uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null ||
            !uri.getPath().isEmpty() || endpoint.endsWith("/"))
            throw new SecurityException("Use a trusted HTTPS Core origin");
    }
    JSONObject call(String operation, JSONObject payload) throws Exception {
        return call(operation, payload, UUID.randomUUID().toString());
    }
    JSONObject call(String operation, JSONObject payload, String requestId) throws Exception {
        byte[] body = new JSONObject().put("version", 1).put("operation", operation)
            .put("request_id", requestId).put("payload", payload).toString().getBytes(StandardCharsets.UTF_8);
        if (body.length > 32768) throw new IllegalArgumentException("Request exceeds boundary");
        HttpURLConnection connection = (HttpURLConnection) new URI(session.getString("url") + "/v1/mobile").toURL().openConnection();
        active = connection;
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(5000);
        connection.setReadTimeout(8000);
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("Authorization", "Bearer " + session.getString("token"));
        connection.setRequestProperty("X-Oscar-Node", session.getString("node_id"));
        connection.setRequestProperty("X-Oscar-Session", session.getString("session_id"));
        connection.setFixedLengthStreamingMode(body.length);
        try {
            try (var output = connection.getOutputStream()) { output.write(body); }
            if (connection.getResponseCode() != 200)
                throw new SecurityException("Core rejected the request; refresh pairing and policy");
            try (InputStream input = connection.getInputStream()) {
                ByteArrayOutputStream collected = new ByteArrayOutputStream();
                byte[] buffer = new byte[8192];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (collected.size() + count > 262144) throw new SecurityException("Core response exceeds boundary");
                    collected.write(buffer, 0, count);
                }
                byte[] result = collected.toByteArray();
                return new JSONObject(new String(result, StandardCharsets.UTF_8));
            }
        } finally { connection.disconnect(); if (active == connection) active = null; }
        // Never retry a mutation automatically after an ambiguous network outcome.
    }
}
