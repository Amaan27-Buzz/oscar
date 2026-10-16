package io.dawnlight.oscar.mobile

import android.Manifest
import android.app.*
import android.content.*
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.graphics.PixelFormat
import android.os.*
import android.provider.Settings
import android.view.*
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.TextButton
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.ViewCompositionStrategy
import androidx.compose.ui.unit.dp
import androidx.lifecycle.*
import androidx.savedstate.*
import io.dawnlight.oscar.expression.Contract
import io.dawnlight.oscar.expression.ExpressionPresence
import io.dawnlight.oscar.expression.SourceKind
import kotlinx.coroutines.*
import org.json.JSONObject

/** Separate projection connection. Never keeps CoreSession, private conversation or audio alive. */
object CompanionOverlay {
    private var startToken: String? = null
    fun permitted(context: Context) = Settings.canDrawOverlays(context) && context.getSystemService(NotificationManager::class.java).areNotificationsEnabled() &&
        (Build.VERSION.SDK_INT < 33 || context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED)
    fun show(context: Context) {
        check(permitted(context)) { "Overlay and notification permissions required" }
        val token = java.util.UUID.randomUUID().toString(); startToken = token
        context.getSharedPreferences("presence", Context.MODE_PRIVATE).edit().putBoolean("overlay_enabled", true).apply()
        context.startForegroundService(Intent(context, CompanionOverlayService::class.java).putExtra("start_token", token))
    }
    fun consume(token: String?) = token != null && token == startToken && run { startToken = null; true }
    fun hide(context: Context, disable: Boolean = false) {
        startToken = null
        if (disable) context.getSharedPreferences("presence", Context.MODE_PRIVATE).edit().putBoolean("overlay_enabled", false).apply()
        context.stopService(Intent(context, CompanionOverlayService::class.java))
    }
}

private class OverlayOwner : LifecycleOwner, SavedStateRegistryOwner {
    private val registry = LifecycleRegistry(this)
    private val saved = SavedStateRegistryController.create(this)
    override val lifecycle: Lifecycle get() = registry
    override val savedStateRegistry: SavedStateRegistry get() = saved.savedStateRegistry
    init { saved.performAttach(); saved.performRestore(null); registry.handleLifecycleEvent(Lifecycle.Event.ON_CREATE) }
    fun start() { registry.handleLifecycleEvent(Lifecycle.Event.ON_START) }
    fun close() { registry.handleLifecycleEvent(Lifecycle.Event.ON_STOP); registry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY) }
}

class CompanionOverlayService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var wire: CoreClient? = null
    private var owner: OverlayOwner? = null
    private var view: ComposeView? = null
    private var event by mutableStateOf<String?>(null)
    private var polling: Job? = null
    private val screen = object : BroadcastReceiver() { override fun onReceive(c: Context?, i: Intent?) { if (i?.action == Intent.ACTION_SCREEN_OFF) stopSelf() } }
    override fun onCreate() {
        super.onCreate()
        val filter = IntentFilter(Intent.ACTION_SCREEN_OFF)
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(screen, filter, RECEIVER_NOT_EXPORTED) else registerReceiver(screen, filter)
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "hide" || !CompanionOverlay.consume(intent?.getStringExtra("start_token")) || !CompanionOverlay.permitted(this)) { stopSelf(); return START_NOT_STICKY }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("companion", "OSCAR Companion", NotificationManager.IMPORTANCE_LOW))
        val hide = PendingIntent.getService(this, 16, Intent(this, CompanionOverlayService::class.java).setAction("hide"), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val open = PendingIntent.getActivity(this, 16, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val notification = Notification.Builder(this, "companion").setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("OSCAR Companion is visible")
            .setContentText("Read-only presence. No microphone or conversation capture.").setContentIntent(open).setVisibility(Notification.VISIBILITY_PRIVATE)
            .addAction(Notification.Action.Builder(null, "Hide", hide).build()).setOngoing(true).build()
        try {
            if (Build.VERSION.SDK_INT >= 34) startForeground(16, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE) else startForeground(16, notification)
            if (view == null) attach()
            polling?.cancel()
            polling = scope.launch {
                var binding: String? = null
                try {
                    while (isActive) {
                        check(CompanionOverlay.permitted(this@CompanionOverlayService) && !getSystemService(KeyguardManager::class.java).isKeyguardLocked)
                        val saved = withContext(Dispatchers.IO) { SessionVault(this@CompanionOverlayService).load() } ?: error("No pairing")
                        val connection = CoreClient(saved)
                        val nextBinding = connection.binding()
                        if (binding != null && binding != nextBinding) error("Pairing changed")
                        binding = nextBinding; wire = connection
                        val response = withContext(Dispatchers.IO) { connection.call("presence", JSONObject()) }
                        require(response.get("visible") is Boolean)
                        if (!response.getBoolean("visible")) { stopSelf(); return@launch }
                        val raw = response.getJSONObject("expression").toString()
                        val admitted = Contract.validate(raw, System.currentTimeMillis()) ?: error("Stale presence")
                        require(admitted.source.kind == SourceKind.CORE && admitted.source.id.startsWith("presence:"))
                        event = raw
                        delay(5000)
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (_: Exception) { event = null; stopSelf() }
            }
        } catch (_: Exception) { stopSelf() }
        return START_NOT_STICKY
    }
    private fun attach() {
        val windows = getSystemService(WindowManager::class.java)
        val lifecycle = OverlayOwner(); owner = lifecycle
        val content = ComposeView(this); view = content
        content.setViewTreeLifecycleOwner(lifecycle); content.setViewTreeSavedStateRegistryOwner(lifecycle)
        content.setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
        content.setContent {
            val current = event?.let { raw -> Contract.parse(raw)?.let { raw to it } }
            Column {
                if (current != null) ExpressionPresence(current.first, current.second.source, 64.dp, current.second.reducedMotion)
                TextButton(onClick = { stopSelf() }) { Text("Hide OSCAR") }
            }
        }
        val density = resources.displayMetrics.density
        val params = WindowManager.LayoutParams((120 * density).toInt(), (120 * density).toInt(), WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_SECURE, PixelFormat.TRANSLUCENT)
        params.gravity = Gravity.TOP or Gravity.START; params.x = 0; params.y = (160 * density).toInt()
        var x = 0f; var y = 0f
        content.setOnTouchListener { _, touch ->
            when (touch.actionMasked) {
                MotionEvent.ACTION_DOWN -> { x = touch.rawX - params.x; y = touch.rawY - params.y; false }
                MotionEvent.ACTION_MOVE -> {
                    val bounds = windows.currentWindowMetrics.bounds
                    params.x = (touch.rawX - x).toInt().coerceIn(0, (bounds.width() - params.width).coerceAtLeast(0))
                    params.y = (touch.rawY - y).toInt().coerceIn(0, (bounds.height() - params.height).coerceAtLeast(0))
                    try { windows.updateViewLayout(content, params) } catch (_: Exception) { stopSelf() }; true
                }
                else -> false
            }
        }
        windows.addView(content, params); lifecycle.start()
    }
    override fun onDestroy() {
        wire?.cancel(); scope.cancel(); event = null
        view?.let { try { getSystemService(WindowManager::class.java).removeViewImmediate(it) } catch (_: Exception) { } }
        owner?.close(); view = null; owner = null
        unregisterReceiver(screen); stopForeground(STOP_FOREGROUND_REMOVE)
        super.onDestroy()
    }
    override fun onBind(intent: Intent?): IBinder? = null
}
