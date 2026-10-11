package io.dawnlight.oscar.mobile;

import android.app.*;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.IBinder;

/** User-started foreground audio only; no boot/background auto-microphone. */
public final class MicrophoneService extends Service {
    static volatile NativeVoice.Sink binding;
    private NativeVoice voice;
    private long voiceEpoch = -1;
    @Override public int onStartCommand(Intent intent, int flags, int id) {
        if (intent == null || "stop".equals(intent.getAction())) {
            VoicePresentation.invalidate(); stopSelf(id); return START_NOT_STICKY;
        }
        final long token = intent.getLongExtra("voice_epoch", -1);
        final NativeVoice.Sink consumer = binding;
        if (!VoicePresentation.admitsCapture(token, intent.getBooleanExtra("owner_started", false),
            NativeVoice.permitted(this), consumer != null)) {
            stopSelf(id); return START_NOT_STICKY;
        }
        voiceEpoch = token;
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
            voice.start(new NativeVoice.Sink() {
                private boolean admitted() {
                    if (!VoicePresentation.current(token)) return false;
                    if (binding == consumer && NativeVoice.permitted(MicrophoneService.this)) return true;
                    VoicePresentation.report(token, VoicePhase.FAILED, "Voice binding or microphone grant revoked; audio stopped");
                    stopSelf(id); return false;
                }
                public void microphone(short[] pcm, long time, long generation, boolean ownOutputPossible) {
                    if (admitted()) consumer.microphone(pcm, time, generation, ownOutputPossible);
                }
                public void playback(short[] pcm, int rate, long time, long generation) {
                    if (admitted()) consumer.playback(pcm, rate, time, generation);
                }
                public void failed(String category) {
                    if (!VoicePresentation.current(token)) return;
                    VoicePresentation.report(token, VoicePhase.FAILED, category);
                    try { consumer.failed(category); } finally { stopSelf(id); }
                }
            }, true, token);
        } catch (Exception unavailable) { VoicePresentation.report(token, VoicePhase.FAILED, "Audio service unavailable; microphone stopped"); stopSelf(); }
        return START_NOT_STICKY;
    }
    @Override public void onDestroy() {
        if (voice != null) voice.close();
        VoicePresentation.report(voiceEpoch, VoicePhase.IDLE, "Microphone off");
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent) { return null; }
}
