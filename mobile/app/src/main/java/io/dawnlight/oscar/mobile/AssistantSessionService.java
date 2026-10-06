package io.dawnlight.oscar.mobile;
import android.content.Intent;
import android.os.Bundle;
import android.service.voice.VoiceInteractionSession;
import android.service.voice.VoiceInteractionSessionService;
public final class AssistantSessionService extends VoiceInteractionSessionService {
    @Override public VoiceInteractionSession onNewSession(Bundle args) {
        return new VoiceInteractionSession(this) {
            @Override public void onShow(Bundle args, int flags) {
                startAssistantActivity(new Intent(getContext(), MainActivity.class));
                finish();
            }
        };
    }
}
