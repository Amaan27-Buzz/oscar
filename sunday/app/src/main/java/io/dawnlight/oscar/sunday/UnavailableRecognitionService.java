package io.dawnlight.oscar.sunday;
import android.content.Intent;
import android.speech.RecognitionService;
import android.speech.SpeechRecognizer;
/** No recognizer is advertised until a real Voice Core runtime binding is commissioned. */
public final class UnavailableRecognitionService extends RecognitionService {
    @Override protected void onStartListening(Intent intent, Callback listener) {
        try { listener.error(SpeechRecognizer.ERROR_SERVER_DISCONNECTED); }
        catch (android.os.RemoteException unavailable) { /* System requester has disconnected. */ }
    }
    @Override protected void onCancel(Callback listener) { }
    @Override protected void onStopListening(Callback listener) { }
}
