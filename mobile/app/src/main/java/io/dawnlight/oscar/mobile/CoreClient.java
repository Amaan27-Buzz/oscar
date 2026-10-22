package io.dawnlight.oscar.mobile;

import org.json.JSONObject;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.security.MessageDigest;
import java.util.Base64;

/** Bounded, no-redirect, no-mutation-retry transport to the same OSCAR Core. */
final class CoreClient {
    interface Signer { String sign(byte[] payload) throws Exception; }
    static final class SessionRejected extends SecurityException {
        SessionRejected() { super("Core credentials expired or revoked. Re-enroll this device from trusted Core."); }
    }
    private final JSONObject session;
    private final Signer signer;
    private final java.util.concurrent.atomic.AtomicLong cancellation = new java.util.concurrent.atomic.AtomicLong();
    private volatile HttpURLConnection active;
    void cancel() { cancellation.incrementAndGet(); HttpURLConnection current = active; if (current != null) current.disconnect(); }
    private void current(long epoch) throws java.io.IOException {
        if (cancellation.get() != epoch) throw new java.io.IOException("Request cancelled; inspect state before retrying");
    }
    CoreClient(JSONObject session) throws Exception {
        this(session, null);
    }
    CoreClient(JSONObject session, Signer signer) throws Exception {
        validateEndpoint(session.getString("url"));
        if (session.optInt("version", 1) != 1 && session.optInt("version", 1) != 2)
            throw new SecurityException("Incompatible Core protocol");
        this.session = new JSONObject(session.toString());
        this.signer = signer;
    }
    String binding() throws Exception { return NotificationBoundary.hash(session.optString("url") + "\n" + session.optString("node_id") + "\n" + session.optString("session_id")); }
    boolean matches(Approval approval) { return session.optString("node_id").equals(approval.getNodeId()) && session.optString("session_id").equals(approval.getSessionId()); }
    String nodeId() { return session.optString("node_id"); }
    String coreId() { return session.optString("core_id"); }
    boolean remote() { return session.optInt("version", 1) == 2; }
    boolean retainsConversation() { return session.optBoolean("retain_conversation", false); }
    String workspace() { return session.optString("workspace"); }
    boolean hasScope(String scope) {
        var scopes = session.optJSONArray("scopes");
        if (scopes != null) for (int index = 0; index < scopes.length(); index++) if (scope.equals(scopes.optString(index))) return true;
        return false;
    }
    boolean canApprove() {
        var scopes = session.optJSONArray("scopes");
        if (scopes != null) for (int index = 0; index < scopes.length(); index++) if ("grid:approve".equals(scopes.optString(index))) return true;
        return false;
    }
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
        long epoch = cancellation.get();
        if (remote() && System.currentTimeMillis() >= session.getLong("expires_at_ms")) throw new SessionRejected();
        byte[] body = new JSONObject().put("version", remote() ? 2 : 1).put("operation", operation)
            .put("request_id", requestId).put("payload", payload).toString().getBytes(StandardCharsets.UTF_8);
        if (body.length > 32768) throw new IllegalArgumentException("Request exceeds boundary");
        HttpURLConnection connection = open(session.getString("url"), remote() ? "/v2/grid/request" : "/v1/mobile");
        active = connection;
        try {
        connection.setRequestProperty("Authorization", "Bearer " + session.getString("token"));
        connection.setRequestProperty("X-Oscar-Node", session.getString("node_id"));
        connection.setRequestProperty("X-Oscar-Session", session.getString("session_id"));
        if (remote()) {
            if (signer == null) throw new SecurityException("Device proof key unavailable");
            String nonce = UUID.randomUUID().toString().replace("-", "");
            String timestamp = Long.toString(System.currentTimeMillis());
            connection.setRequestProperty("X-Oscar-Nonce", nonce);
            connection.setRequestProperty("X-Oscar-Time", timestamp);
            connection.setRequestProperty("X-Oscar-Signature", signer.sign(signingMaterial(session.getString("node_id"),
                session.getString("session_id"), nonce, timestamp, body)));
        }
            return exchange(connection, body, epoch);
        } finally { connection.disconnect(); if (active == connection) active = null; }
        // Never retry a mutation automatically after an ambiguous network outcome.
    }
    static byte[] signingMaterial(String node, String session, String nonce, String time, byte[] body) throws Exception {
        StringBuilder digest = new StringBuilder();
        for (byte value : MessageDigest.getInstance("SHA-256").digest(body)) digest.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        return ("OSCAR-GRID-2\nPOST\n/v2/grid/request\n" + node + "\n" + session + "\n" + nonce + "\n" + time + "\n" + digest).getBytes(StandardCharsets.UTF_8);
    }
    JSONObject enroll(JSONObject invitation, JSONObject identity, Signer proofSigner) throws Exception {
        long epoch = cancellation.get();
        String origin = session.getString("url");
        validateEndpoint(origin);
        if (invitation.toString().length() > 24000 || invitation.getInt("version") != 2 ||
            !"mobile".equals(invitation.getString("role")) ||
            !identity.getString("installation_id").equals(invitation.getString("installation_id")) ||
            !identity.getString("public_key").equals(invitation.getString("public_key")) ||
            invitation.getLong("expires_at_ms") <= System.currentTimeMillis() ||
            invitation.getLong("expires_at_ms") - System.currentTimeMillis() > 300_000)
            throw new SecurityException("Invitation does not match this device or has expired");
        byte[] proof = Base64.getDecoder().decode(invitation.getString("signing_payload"));
        if (proof.length < 1 || proof.length > 16000) throw new SecurityException("Invalid enrollment challenge");
        byte[] body = new JSONObject().put("version", 2).put("challenge_id", invitation.getString("challenge_id"))
            .put("signature", proofSigner.sign(proof)).toString().getBytes(StandardCharsets.UTF_8);
        HttpURLConnection connection = open(origin, "/v2/grid/enroll");
        active = connection;
        try {
            JSONObject issued = exchange(connection, body, epoch);
            if (issued.getInt("version") != 2 || !issued.getString("core_id").equals(invitation.getString("core_id")) ||
                !issued.getString("node_id").equals(invitation.getString("node_id")) || issued.getLong("expires_at_ms") <= System.currentTimeMillis())
                throw new SecurityException("Enrollment response does not match trusted invitation");
            if (!invitation.optString("workspace").isEmpty()) {
                if (!issued.optString("workspace", invitation.getString("workspace")).equals(invitation.getString("workspace")))
                    throw new SecurityException("Worker workspace differs from trusted invitation");
                issued.put("workspace", invitation.getString("workspace"));
            }
            return issued.put("url", origin);
        } finally { connection.disconnect(); if (active == connection) active = null; }
    }
    private static HttpURLConnection open(String origin, String path) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URI(origin + path).toURL().openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setConnectTimeout(5000); connection.setReadTimeout(8000);
        connection.setRequestMethod("POST"); connection.setDoOutput(true);
        connection.setRequestProperty("Content-Type", "application/json");
        return connection;
    }
    private JSONObject exchange(HttpURLConnection connection, byte[] body, long epoch) throws Exception {
        current(epoch);
        connection.setFixedLengthStreamingMode(body.length);
        try (var output = connection.getOutputStream()) { output.write(body); }
        current(epoch);
        int status = connection.getResponseCode();
        current(epoch);
        if (status == 401) throw new SessionRejected();
        if (status != 200) throw new SecurityException("Core rejected the request; inspect current state before retrying");
        try (InputStream input = connection.getInputStream()) {
            ByteArrayOutputStream collected = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192]; int count;
            while ((count = input.read(buffer)) != -1) {
                current(epoch);
                if (collected.size() + count > 262144) throw new SecurityException("Core response exceeds boundary");
                collected.write(buffer, 0, count);
            }
            current(epoch);
            return new JSONObject(new String(collected.toByteArray(), StandardCharsets.UTF_8));
        }
    }
}
