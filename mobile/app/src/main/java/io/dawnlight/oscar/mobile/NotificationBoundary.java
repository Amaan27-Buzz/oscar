package io.dawnlight.oscar.mobile;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.RemoteInput;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Transient, source-filtered notification perception. No raw archive or unrestricted app access. */
public final class NotificationBoundary extends NotificationListenerService {
    private static volatile NotificationBoundary active;
    private final Map<String, StatusBarNotification> current = new LinkedHashMap<>();
    private final Set<String> consumed = new HashSet<>();

    @Override public void onListenerConnected() { active = this; }
    @Override public void onListenerDisconnected() {
        if (active == this) active = null;
        synchronized (current) { current.clear(); consumed.clear(); }
    }
    @Override public void onDestroy() { onListenerDisconnected(); super.onDestroy(); }
    static void privacyChanged() {
        NotificationBoundary listener = active;
        if (listener == null) return;
        synchronized (listener.current) {
            listener.current.values().removeIf(value -> !listener.allowed(value.getPackageName()));
        }
    }
    private boolean allowed(String source) {
        var prefs = getSharedPreferences("permissions", MODE_PRIVATE);
        return getSystemService(NotificationManager.class).isNotificationListenerAccessGranted(
            new ComponentName(this, NotificationBoundary.class)) &&
            prefs.getBoolean("notification_context", false) &&
            Arrays.asList(prefs.getString("notification_sources", "").split(",")).contains(source);
    }
    @Override public void onNotificationPosted(StatusBarNotification notification) {
        if (!allowed(notification.getPackageName())) return;
        synchronized (current) {
            if (current.size() >= 32) current.remove(current.keySet().iterator().next());
            current.put(notification.getKey(), notification);
        }
    }
    @Override public void onNotificationRemoved(StatusBarNotification notification) {
        synchronized (current) { current.remove(notification.getKey()); }
    }
    static String hash(String text) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8));
        StringBuilder value = new StringBuilder();
        for (byte part : digest) value.append(String.format(Locale.ROOT, "%02x", part & 255));
        return value.toString();
    }
    static String identity(StatusBarNotification notification) throws Exception {
        Notification.Action action = replyAction(notification);
        Bundle extras = notification.getNotification().extras;
        String currentContent = String.valueOf(extras.getCharSequence(Notification.EXTRA_TITLE, "")) + "\u0000" +
            String.valueOf(extras.getCharSequence(Notification.EXTRA_TEXT, ""));
        return hash(notification.getKey() + ":" + notification.getPostTime() + ":" + hash(currentContent) + ":" +
            (action == null ? "unavailable" : action.actionIntent.hashCode()));
    }
    static Notification.Action replyAction(StatusBarNotification notification) {
        Notification.Action[] actions = notification.getNotification().actions;
        if (actions == null) return null;
        for (Notification.Action action : actions) {
            if (action.actionIntent == null || action.getSemanticAction() != Notification.Action.SEMANTIC_ACTION_REPLY ||
                !notification.getPackageName().equals(action.actionIntent.getCreatorPackage()) ||
                (Build.VERSION.SDK_INT >= 31 && action.actionIntent.isImmutable()) || action.getRemoteInputs() == null) continue;
            for (RemoteInput input : action.getRemoteInputs()) if (input.getAllowFreeFormInput()) return action;
        }
        return null;
    }
    static List<JSONObject> exposed() throws Exception {
        NotificationBoundary listener = active;
        if (listener == null) return Collections.emptyList();
        List<JSONObject> result = new ArrayList<>();
        synchronized (listener.current) {
            for (StatusBarNotification notification : listener.current.values()) {
                if (!listener.allowed(notification.getPackageName()) || replyAction(notification) == null) continue;
                String title = String.valueOf(notification.getNotification().extras.getCharSequence(Notification.EXTRA_TITLE, "Notification"));
                result.add(new JSONObject().put("package", notification.getPackageName())
                    .put("key_hash", identity(notification)).put("title", title.substring(0, Math.min(120, title.length()))));
            }
        }
        return result;
    }
    static void send(JSONObject permit, String text, long requestStartedElapsed) throws Exception {
        NotificationBoundary listener = active;
        if (listener == null || text.isEmpty() || text.length() > 500)
            throw new SecurityException("Notification reply unavailable");
        long ttl = permit.getLong("expires_at_ms") - permit.getLong("issued_at_ms");
        if (!(permit.get("expires_at_ms") instanceof Number) || !(permit.get("issued_at_ms") instanceof Number) ||
            requestStartedElapsed > SystemClock.elapsedRealtime() || ttl <= 0 || ttl > 10000 || SystemClock.elapsedRealtime() - requestStartedElapsed >= ttl ||
            !permit.getString("text_hash").equals(hash(text)))
            throw new SecurityException("Reply permit expired or text changed");
        if (!listener.getSharedPreferences("permissions", MODE_PRIVATE).getBoolean("notification_reply", false))
            throw new SecurityException("Separate local reply authority required");
        synchronized (listener.current) {
            if (listener.consumed.contains(permit.getString("id")) || listener.consumed.size() >= 64)
                throw new SecurityException("Reply permit already consumed or session bound reached");
            for (StatusBarNotification notification : listener.getActiveNotifications()) {
                if (!listener.allowed(notification.getPackageName()) ||
                    !permit.getString("package").equals(notification.getPackageName()) ||
                    !permit.getString("key_hash").equals(identity(notification))) continue;
                Notification.Action action = replyAction(notification);
                if (action == null) break;
                Bundle reply = new Bundle();
                for (RemoteInput input : action.getRemoteInputs())
                    if (input.getAllowFreeFormInput()) reply.putCharSequence(input.getResultKey(), text);
                Intent intent = new Intent();
                RemoteInput.addResultsToIntent(action.getRemoteInputs(), intent, reply);
                listener.consumed.add(permit.getString("id"));
                action.actionIntent.send(listener, 0, intent);
                return; // Handed to the source app, never a VERIFIED delivery claim.
            }
        }
        throw new PendingIntent.CanceledException("Source notification changed or reply disappeared");
    }
}
