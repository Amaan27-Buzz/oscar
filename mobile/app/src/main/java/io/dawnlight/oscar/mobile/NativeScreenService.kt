package io.dawnlight.oscar.mobile

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.*
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference

/** Per-session Android consent only. Frames stay transient until an independently authorized task. */
class NativeScreenService : Service() {
    private var projection: MediaProjection? = null
    private var display: android.hardware.display.VirtualDisplay? = null
    private var reader: ImageReader? = null
    private data class Capture(val packageName: String, val authorized: () -> Boolean,
        var afterTimestamp: Long = Long.MIN_VALUE, val ready: CountDownLatch = CountDownLatch(1), var result: String? = null)
    private val pending = AtomicReference<Capture?>()
    private var lastTimestamp = Long.MIN_VALUE
    private val handler = Handler(Looper.getMainLooper())
    private val lock = object : BroadcastReceiver() { override fun onReceive(context: Context?, intent: Intent?) { stopSelf() } }
    override fun onCreate() {
        super.onCreate()
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(lock, IntentFilter(Intent.ACTION_SCREEN_OFF), RECEIVER_NOT_EXPORTED)
        else registerReceiver(lock, IntentFilter(Intent.ACTION_SCREEN_OFF))
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "stop" || current != null || intent == null) { stopSelf(); return START_NOT_STICKY }
        @Suppress("DEPRECATION") val consent = intent.getParcelableExtra<Intent>("consent")
        if (intent.getIntExtra("result", Activity.RESULT_CANCELED) != Activity.RESULT_OK || consent == null ||
            getSystemService(KeyguardManager::class.java).isKeyguardLocked) { stopSelf(); return START_NOT_STICKY }
        try {
            val notifications = getSystemService(NotificationManager::class.java)
            notifications.createNotificationChannel(NotificationChannel("screen-observation", "OSCAR screen sharing", NotificationManager.IMPORTANCE_LOW))
            val stop = PendingIntent.getService(this, 32, Intent(this, NativeScreenService::class.java).setAction("stop"), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            val notification = Notification.Builder(this, "screen-observation").setSmallIcon(android.R.drawable.ic_menu_view)
                .setContentTitle("OSCAR screen sharing").setContentText("Shared frames may include other visible content. Stop to end sharing.")
                .setVisibility(Notification.VISIBILITY_PRIVATE).setOngoing(true).addAction(Notification.Action.Builder(null, "Stop", stop).build()).build()
            startForeground(32, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
            val active = requireNotNull(getSystemService(MediaProjectionManager::class.java).getMediaProjection(Activity.RESULT_OK, consent))
            projection = active
            active.registerCallback(object : MediaProjection.Callback() { override fun onStop() { stopSelf() } }, handler)
            val metrics = resources.displayMetrics
            val width = 256; val height = (metrics.heightPixels * width / metrics.widthPixels).coerceIn(128, 640)
            val frames = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2); reader = frames
            frames.setOnImageAvailableListener({ images ->
                images.acquireLatestImage()?.use { image ->
                    lastTimestamp = maxOf(lastTimestamp, image.timestamp)
                    val request = pending.get() ?: return@use
                    if (image.timestamp <= request.afterTimestamp) return@use
                    try {
                        if (request.ready.count > 0 && authorized(request)) {
                            val encoded = encode(image)
                            if (request.ready.count > 0 && authorized(request)) request.result = encoded
                        }
                    } catch (_: Exception) { request.result = null }
                    finally { pending.compareAndSet(request, null); request.ready.countDown() }
                }
            }, handler)
            display = active.createVirtualDisplay("OSCAR consented screen", width, height, metrics.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, frames.surface, null, handler)
            current = this
        } catch (_: Exception) { stopSelf() }
        return START_NOT_STICKY
    }
    private fun authorized(request: Capture): Boolean = current === this && request.authorized() &&
        !getSystemService(KeyguardManager::class.java).isKeyguardLocked &&
        AppControlService.connected?.selectedPackage() == request.packageName

    internal fun capture(packageName: String, authorized: () -> Boolean): String? {
        check(Looper.myLooper() != Looper.getMainLooper())
        val request = Capture(packageName, authorized)
        if (!authorized(request)) return null
        handler.post {
            if (request.ready.count == 0L || !authorized(request)) { request.ready.countDown(); return@post }
            try {
                // Image timestamps use the producer's clock; drain old frames before arming a request.
                reader?.acquireLatestImage()?.use { lastTimestamp = maxOf(lastTimestamp, it.timestamp) }
                request.afterTimestamp = lastTimestamp
                if (!pending.compareAndSet(null, request)) request.ready.countDown()
            } catch (_: Exception) { request.ready.countDown() }
        }
        try {
            if (!request.ready.await(200, TimeUnit.MILLISECONDS) || !authorized(request)) return null
            return request.result
        } finally { request.ready.countDown(); pending.compareAndSet(request, null) }
    }

    private fun encode(image: android.media.Image): String? {
            val plane = image.planes[0]
            val bitmap = Bitmap.createBitmap(plane.rowStride / plane.pixelStride, image.height, Bitmap.Config.ARGB_8888)
            return try {
                bitmap.copyPixelsFromBuffer(plane.buffer)
                val cropped = Bitmap.createBitmap(bitmap, 0, 0, image.width, image.height)
                try {
                    val encoded = ByteArrayOutputStream().use { bytes -> cropped.compress(Bitmap.CompressFormat.JPEG, 35, bytes); bytes.toByteArray() }
                    if (encoded.size > 4500) return null
                    JSONObject().put("mime", "image/jpeg").put("width", image.width).put("height", image.height)
                        .put("base64", android.util.Base64.encodeToString(encoded, android.util.Base64.NO_WRAP)).toString()
                } finally { if (cropped !== bitmap) cropped.recycle() }
            } finally { bitmap.recycle() }
    }
    override fun onDestroy() {
        if (current === this) current = null
        pending.getAndSet(null)?.ready?.countDown()
        display?.release(); reader?.close(); projection?.stop(); projection = null
        unregisterReceiver(lock); stopForeground(STOP_FOREGROUND_REMOVE); super.onDestroy()
    }
    override fun onBind(intent: Intent?): IBinder? = null
    companion object { @Volatile internal var current: NativeScreenService? = null; private set }
}
