package io.dawnlight.oscar.mobile;
import android.content.Intent;
import android.speech.RecognitionService;
import android.speech.SpeechRecognizer;
/** No recognizer is advertised until a real Voice Core runtime binding is commissioned. */
public final class UnavailableRecognitionService extends RecognitionService {
    @Override protected void onStartListening(Intent intent, Callback listener) {
        try { listener.error(android.os.Build.VERSION.SDK_INT >= 31 ? SpeechRecognizer.ERROR_SERVER_DISCONNECTED : SpeechRecognizer.ERROR_SERVER); }
        catch (android.os.RemoteException unavailable) { /* System requester has disconnected. */ }
    }
    @Override protected void onCancel(Callback listener) { }
    @Override protected void onStopListening(Callback listener) { }
}
