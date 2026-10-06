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
    fun changed(previous: CoreSnapshot?, current: CoreSnapshot) {
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
    fun clear() { manager.cancelAll() }
}
