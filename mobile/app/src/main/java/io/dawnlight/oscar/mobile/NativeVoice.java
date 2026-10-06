package io.dawnlight.oscar.mobile;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.*;
import android.media.audiofx.AcousticEchoCanceler;
import android.os.Build;
import android.os.SystemClock;
import java.util.concurrent.atomic.AtomicLong;

/** Portable PCM/generation contracts underneath Android audio/session adapters. No model brain. */
final class NativeVoice implements AutoCloseable {
    interface Sink {
        void microphone(short[] pcm, long monotonicNanos, long generation, boolean ownOutputPossible);
        void playback(short[] pcm, int rate, long monotonicNanos, long generation);
        void failed(String category);
    }
    private final Context context;
    private final AudioManager manager;
    private final AtomicLong generation = new AtomicLong();
    private final AtomicLong outputGeneration = new AtomicLong();
    private boolean ownsSession;
    long outputEpoch() { return outputGeneration.get(); }
    private AudioRecord capture;
    private AudioTrack output;
    private AcousticEchoCanceler aec;
    private volatile boolean listening;
    private volatile long outputTail;
    private AudioFocusRequest focus;
    private Sink sink;
    NativeVoice(Context context) {
        this.context = context.getApplicationContext();
        manager = context.getSystemService(AudioManager.class);
    }
    void start(Sink sink, boolean perceptionGranted) {
        if (!perceptionGranted || context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
            throw new SecurityException("Separate microphone perception grant required");
        if (sink == null) throw new IllegalStateException("Voice Core binding unavailable");
        close();
        this.sink = sink;
        focus = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT)
            .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setOnAudioFocusChangeListener(change -> { if (change < 0) close(); }).build();
        if (manager.requestAudioFocus(focus) != AudioManager.AUDIOFOCUS_REQUEST_GRANTED)
            throw new IllegalStateException("Audio session unavailable");
        manager.setMode(AudioManager.MODE_IN_COMMUNICATION);
        ownsSession = true;
        int minimum = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        if (minimum <= 0) { close(); throw new IllegalStateException("16 kHz capture unsupported"); }
        capture = new AudioRecord.Builder().setAudioSource(MediaRecorder.AudioSource.VOICE_COMMUNICATION)
            .setAudioFormat(new AudioFormat.Builder().setSampleRate(16000)
                .setChannelMask(AudioFormat.CHANNEL_IN_MONO).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
            .setBufferSizeInBytes(Math.max(minimum * 2, 4096)).build();
        if (capture.getState() != AudioRecord.STATE_INITIALIZED) { close(); throw new IllegalStateException("Capture unavailable"); }
        if (AcousticEchoCanceler.isAvailable()) {
            aec = AcousticEchoCanceler.create(capture.getAudioSessionId());
            if (aec != null && aec.setEnabled(true) != 0) { aec.release(); aec = null; }
        }
        // Effect availability/enabling never establishes room AEC or barge-in acceptance.
        AudioRecord device = capture;
        long turn = generation.incrementAndGet();
        device.startRecording();
        listening = true;
        new Thread(() -> {
            try {
                while (listening && generation.get() == turn) {
                    short[] frame = new short[512];
                    int count = device.read(frame, 0, frame.length, AudioRecord.READ_BLOCKING);
                    if (count != frame.length) throw new IllegalStateException("capture discontinuity");
                    if (generation.get() != turn) break;
                    sink.microphone(frame, SystemClock.elapsedRealtimeNanos(), turn,
                        SystemClock.elapsedRealtimeNanos() < outputTail);
                }
            } catch (Exception failure) {
                if (generation.get() == turn) { sink.failed("capture unavailable or permission revoked"); close(); }
            }
        }, "oscar-audio").start();
    }
    synchronized void play(short[] pcm, int rate, long turn) {
        if (outputGeneration.get() != turn || sink == null || rate < 8000 || rate > 48000 || pcm.length > rate * 30)
            throw new IllegalStateException("Invalid or obsolete Voice output");
        if (output == null || output.getSampleRate() != rate) {
            releaseOutput();
            output = new AudioTrack.Builder().setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                .setAudioFormat(new AudioFormat.Builder().setSampleRate(rate).setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
                .setBufferSizeInBytes(Math.max(rate / 5 * 2, AudioTrack.getMinBufferSize(rate,
                    AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)))
                .setTransferMode(AudioTrack.MODE_STREAM).build();
            output.play();
        }
        AudioTrack track = output;
        Sink consumer = sink;
        for (int offset = 0; offset < pcm.length; offset += rate / 32) {
            if (outputGeneration.get() != turn) return;
            int count = Math.min(rate / 32, pcm.length - offset);
            short[] reference = java.util.Arrays.copyOfRange(pcm, offset, offset + count);
            outputTail = SystemClock.elapsedRealtimeNanos() + 500_000_000L;
            consumer.playback(reference, rate, SystemClock.elapsedRealtimeNanos(), turn);
            if (track.write(pcm, offset, count, AudioTrack.WRITE_BLOCKING) != count)
                throw new IllegalStateException("Playback discontinuity");
        }
    }
    boolean route(int deviceId) {
        if (Build.VERSION.SDK_INT < 31) return false;
        if (context.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED)
            return false;
        for (AudioDeviceInfo device : manager.getAvailableCommunicationDevices())
            if (device.getId() == deviceId) return manager.setCommunicationDevice(device);
        return false;
    }
    void cancelOutput() {
        outputGeneration.incrementAndGet();
        releaseOutput();
    }
    private void releaseOutput() {
        AudioTrack track = output;
        output = null;
        if (track != null) {
            try { track.pause(); track.flush(); }
            catch (IllegalStateException lost) { if (sink != null) sink.failed("playback cancellation unverified"); }
            finally { track.release(); }
        }
    }
    @Override public void close() {
        listening = false;
        generation.incrementAndGet();
        cancelOutput();
        AudioRecord device = capture;
        capture = null;
        if (device != null) {
            try { device.stop(); }
            catch (IllegalStateException lost) { if (sink != null) sink.failed("capture stop unverified"); }
            finally { device.release(); }
        }
        if (aec != null) { aec.release(); aec = null; }
        if (focus != null) { manager.abandonAudioFocusRequest(focus); focus = null; }
        if (ownsSession) {
            manager.setMode(AudioManager.MODE_NORMAL);
            if (Build.VERSION.SDK_INT >= 31) manager.clearCommunicationDevice();
            ownsSession = false;
        }
        sink = null;
    }
}
