package io.dawnlight.oscar.mobile;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.widget.TextView;

/** Separate synthetic task; the standalone test APK cannot use the target APK's Kotlin runtime. */
public final class ScreenFixtureActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView frame;
    private final Runnable animate = new Runnable() {
        @Override public void run() {
            frame.setText("Synthetic frame " + SystemClock.elapsedRealtime());
            handler.postDelayed(this, 40);
        }
    };

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (!android.os.Build.HARDWARE.equals("ranchu") && !android.os.Build.HARDWARE.equals("goldfish")) {
            throw new IllegalStateException("Disposable emulator required");
        }
        frame = new TextView(this);
        frame.setBackgroundColor(android.graphics.Color.rgb(30, 140, 60));
        setContentView(frame);
        handler.post(animate);
    }

    @Override public void onDestroy() {
        handler.removeCallbacks(animate);
        super.onDestroy();
    }
}
