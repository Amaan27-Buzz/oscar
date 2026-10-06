package io.dawnlight.oscar.sunday;

import android.Manifest;
import android.app.*;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.IBinder;

/** User-started foreground audio only; no boot/background auto-microphone. */
public final class MicrophoneService extends Service {
    static volatile NativeVoice.Sink binding;
    private NativeVoice voice;
    @Override public int onStartCommand(Intent intent, int flags, int id) {
        if (intent == null || "stop".equals(intent.getAction()) || binding == null ||
            !intent.getBooleanExtra("owner_started", false) ||
            checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED ||
            !getSharedPreferences("permissions", MODE_PRIVATE).getBoolean("microphone_perception", false)) {
            stopSelf(); return START_NOT_STICKY;
        }
        NotificationManager manager = getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("voice", "OSCAR microphone", NotificationManager.IMPORTANCE_LOW));
        PendingIntent stop = PendingIntent.getService(this, 0, new Intent(this, MicrophoneService.class)
            .setAction("stop"), PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification notification = new Notification.Builder(this, "voice")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now).setContentTitle("OSCAR microphone active")
            .setContentText("No raw recording retained. Stop at any time.")
            .addAction(new Notification.Action.Builder(null, "Stop", stop).build()).setOngoing(true).build();
        try {
            startForeground(8, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE);
            if (voice != null) voice.close();
            voice = new NativeVoice(this);
            voice.start(binding, true);
        } catch (Exception unavailable) { stopSelf(); }
        return START_NOT_STICKY;
    }
    @Override public void onDestroy() {
        if (voice != null) voice.close();
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent) { return null; }
}
