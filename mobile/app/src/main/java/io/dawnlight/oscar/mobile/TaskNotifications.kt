package io.dawnlight.oscar.mobile

import android.Manifest
import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build

/** Alerts from observed Core transitions only; no background inference or private task text. */
class TaskNotifications(private val context: Context) {
    private val manager = context.getSystemService(NotificationManager::class.java)
    fun changed(previous: CoreSnapshot?, current: CoreSnapshot, coreNow: Long) {
        sentry(current, coreNow)
        if (!context.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("task_alerts", false) ||
            !manager.areNotificationsEnabled() || (Build.VERSION.SDK_INT >= 33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)) return
        manager.createNotificationChannel(NotificationChannel("activity", "OSCAR activity", NotificationManager.IMPORTANCE_DEFAULT))
        current.tasks.forEach { task ->
            val old = previous?.tasks?.find { it.id == task.id }
            if (old?.state == task.state || (previous == null && "approve" !in task.actions)) return@forEach
            if (task.state !in setOf("planned", "verified", "failed", "blocked")) return@forEach
            val open = PendingIntent.getActivity(context, 0, Intent(context, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            manager.notify(task.id, 1, Notification.Builder(context, "activity").setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("OSCAR · ${task.label}").setContentText("Open OSCAR to inspect current task state.")
                .setVisibility(Notification.VISIBILITY_PRIVATE).setContentIntent(open).setAutoCancel(true).build())
        }
    }
    private fun sentry(current: CoreSnapshot, coreNow: Long) {
        val started = android.os.SystemClock.elapsedRealtime()
        val allowed = context.getSharedPreferences("permissions", Context.MODE_PRIVATE).getBoolean("task_alerts", false) &&
            manager.areNotificationsEnabled() && (Build.VERSION.SDK_INT < 33 || context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED)
        val notices = if (allowed) parseSentryAlerts(current.management, coreNow) else emptyList()
        manager.activeNotifications.filter { it.id == 2 && it.tag?.startsWith("sentry:") == true && it.tag.removePrefix("sentry:") !in notices.map { notice -> notice.id } }
            .forEach { manager.cancel(it.tag, 2) }
        if (notices.isEmpty()) return
        val receipts = context.getSharedPreferences("sentry_notice_receipts", Context.MODE_PRIVATE)
        val seen = receipts.all.filterValues { it is Long && it > coreNow }.mapValues { it.value as Long }.toMutableMap()
        manager.createNotificationChannel(NotificationChannel("awareness", "OSCAR awareness", NotificationManager.IMPORTANCE_DEFAULT))
        notices.forEach { notice ->
            if (notice.id in seen || seen.size >= 256) return@forEach
            seen[notice.id] = notice.expires
            // Consume before delivery: uncertain OS outcomes must not replay after restart.
            if (!receipts.edit().clear().also { editor -> seen.forEach { (id, expires) -> editor.putLong(id, expires) } }.commit()) return@forEach
            val dispatchNow = coreNow + android.os.SystemClock.elapsedRealtime() - started
            if (notice.expires <= dispatchNow) return@forEach
            val open = PendingIntent.getActivity(context, 0, Intent(context, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            try {
                manager.notify("sentry:${notice.id}", 2, Notification.Builder(context, "awareness")
                    .setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("OSCAR · Awareness${if (notice.simulated) " · Simulated" else ""}")
                    .setContentText("A selected source needs your attention. Open OSCAR to review current context.")
                    .setVisibility(Notification.VISIBILITY_PRIVATE).setContentIntent(open).setAutoCancel(true)
                    .setTimeoutAfter(notice.expires - dispatchNow).build())
            } catch (_: SecurityException) { /* Permission may change after the platform check. */ }
        }
    }
    fun clearSentry() { manager.activeNotifications.filter { it.id == 2 && it.tag?.startsWith("sentry:") == true }.forEach { manager.cancel(it.tag, 2) } }
    fun clear() { manager.cancelAll() }
}
