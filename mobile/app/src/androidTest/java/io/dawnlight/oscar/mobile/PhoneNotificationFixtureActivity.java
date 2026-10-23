package io.dawnlight.oscar.mobile;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.os.Bundle;

/** Actual OS notification in the disposable test package; no target Kotlin runtime. */
public final class PhoneNotificationFixtureActivity extends Activity {
    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (!android.os.Build.HARDWARE.equals("ranchu") && !android.os.Build.HARDWARE.equals("goldfish")) {
            throw new IllegalStateException("Disposable emulator required");
        }
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (getIntent().getBooleanExtra("clear", false)) manager.cancel(47);
        else {
            manager.createNotificationChannel(new NotificationChannel("phone-context-fixture", "Synthetic context", NotificationManager.IMPORTANCE_LOW));
            manager.notify(47, new Notification.Builder(this, "phone-context-fixture")
                .setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("OSCAR synthetic notification")
                .setContentText("synthetic-sensitive-body-marker").build());
        }
        finish();
    }
}
