package io.dawnlight.oscar.mobile

import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.os.*
import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject

/** User-started, visible outbound executor. A killed service never resumes an uncertain effect. */
internal object NativeWorker {
    private val requests = OverlayRequests()
    @Volatile var running = false; private set
    @Volatile var status = "Stopped"; private set
    fun start(context: Context) {
        check(context.getSystemService(NotificationManager::class.java).areNotificationsEnabled() &&
            (Build.VERSION.SDK_INT < 33 || context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == android.content.pm.PackageManager.PERMISSION_GRANTED)) { "Enable notifications before starting phone tasks" }
        check(!context.getSystemService(KeyguardManager::class.java).isKeyguardLocked)
        val token = requests.request()
        try { context.startForegroundService(Intent(context, NativeWorkerService::class.java).putExtra("start_token", token)) }
        catch (failure: RuntimeException) { requests.cancel(token); throw failure }
    }
    fun stop(context: Context) { requests.cancel(); NativeWorkerService.instance?.withdraw(); context.stopService(Intent(context, NativeWorkerService::class.java)) }
    fun consume(token: String?) = requests.consume(token)
    fun current(token: String?) = requests.current(token)
    fun state(active: Boolean, message: String) { running = active; status = message }
}

class NativeWorkerService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var client: CoreClient? = null
    private var adapter: NativeCapabilities? = null
    private var work: Job? = null
    private var token: String? = null
    private var permitted: NativeAction? = null
    private var permitUntil = 0L
    private val locked = object : BroadcastReceiver() { override fun onReceive(context: Context?, intent: Intent?) { NativeWorker.stop(this@NativeWorkerService) } }
    override fun onCreate() {
        super.onCreate(); instance = this
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(locked, IntentFilter(Intent.ACTION_SCREEN_OFF), RECEIVER_NOT_EXPORTED)
        else registerReceiver(locked, IntentFilter(Intent.ACTION_SCREEN_OFF))
    }
    internal fun withdraw() { permitted = null; permitUntil = 0; adapter?.revoke(); NativeWorker.state(false, "Stopped") }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "stop") { NativeWorker.stop(this); return START_NOT_STICKY }
        val requested = intent?.getStringExtra("start_token")
        if (!NativeWorker.consume(requested)) { stopSelf(); return START_NOT_STICKY }
        token = requested; work?.cancel(); client?.cancel(); adapter?.close(); withdraw()
        val notifications = getSystemService(NotificationManager::class.java)
        notifications.createNotificationChannel(NotificationChannel("native-tasks", "OSCAR phone tasks", NotificationManager.IMPORTANCE_LOW))
        val stop = PendingIntent.getService(this, 31, Intent(this, NativeWorkerService::class.java).setAction("stop"), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val open = PendingIntent.getActivity(this, 31, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val notification = Notification.Builder(this, "native-tasks").setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("OSCAR phone tasks").setContentText("Only selected apps and current Core authority. Tap Stop to withdraw.")
            .setVisibility(Notification.VISIBILITY_PRIVATE).setContentIntent(open).setOngoing(true)
            .addAction(Notification.Action.Builder(null, "Stop", stop).build()).build()
        try {
            if (Build.VERSION.SDK_INT >= 34) startForeground(31, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE) else startForeground(31, notification)
            work = scope.launch {
                val vault = SessionVault(this@NativeWorkerService)
                var phase = "connection"
                try {
                    val saved = withContext(Dispatchers.IO) { vault.load() } ?: error("No connection")
                    val connection = CoreClient(saved, vault::signDevice); client = connection
                    require(connection.remote() && connection.hasScope("advertise") && connection.hasScope("execute"))
                    val workspace = saved.getString("workspace"); require(workspace.matches(Regex("[A-Za-z0-9_-]{1,80}")))
                    val binding = connection.binding()
                    val native = NativeCapabilities(this@NativeWorkerService, executionReady = true) { action ->
                        action == permitted && SystemClock.elapsedRealtime() < permitUntil && NativeWorker.current(token) &&
                            !getSystemService(KeyguardManager::class.java).isKeyguardLocked
                    }; adapter = native; native.gate.foreground(true)
                    while (isActive && NativeWorker.current(requested)) {
                        phase = "advertisement"
                        require(!getSystemService(KeyguardManager::class.java).isKeyguardLocked)
                        val current = withContext(Dispatchers.IO) { vault.load() } ?: error("Connection removed")
                        require(CoreClient(current).binding() == binding)
                        val caps = native.status().filter { it.availability == "available" }.map { cap -> nativeAdvertisement(cap.id, connection.nodeId()) }
                        withContext(Dispatchers.IO) { connection.call("advertise", JSONObject().put("workspace", workspace).put("capabilities", JSONArray(caps))) }
                        NativeWorker.state(true, "Connected · ${caps.size} available capabilities")
                        phase = "poll"
                        val response = withContext(Dispatchers.IO) { connection.call("poll", JSONObject()) }
                        if (!response.isNull("delivery")) {
                            phase = "delivery validation"
                            val delivery = NativeGridDelivery.parse(response.getJSONObject("delivery"), connection.nodeId(), saved.getString("session_id"), workspace, System.currentTimeMillis())
                            native.gate.invalidate()
                            val action = delivery.native(native.gate.generation, SystemClock.elapsedRealtime(), System.currentTimeMillis())
                            // Claim on disk before any effect. A lost receipt or process death is never replayed.
                            withContext(Dispatchers.IO) {
                                phase = "effect claim and authority check"
                                val journal = getSharedPreferences("native-execution-claims", MODE_PRIVATE)
                                val key = NotificationBoundary.hash(binding + ":" + delivery.action.getString("id") + ":" + delivery.kind)
                                require(!journal.contains(key)) { "Outcome already claimed; inspect before retry" }
                                require(journal.all.size < 4096) { "Execution journal requires reviewed recovery" }
                                check(journal.edit().putBoolean(key, true).commit())
                                require(delivery.acceptsCheck(connection.call("check", delivery.checkRequest())))
                            }
                            ensureActive()
                            phase = "native dispatch"
                            permitted = action; permitUntil = SystemClock.elapsedRealtime() + 500
                            val dispatch = if (action.capability.startsWith("android.ui.") || platformCapability(action.capability)) this@NativeWorkerService
                                else MainActivity.foregroundActivity ?: AppControlService.connected
                            val result = if (dispatch == null) NativeResult(action.requestId, action.taskId, "blocked", "Open OSCAR or enable the reviewed accessibility service to launch an app")
                                else if (action.capability.startsWith("android.files.") || action.capability == "android.screen.capture") withContext(Dispatchers.IO) { native.execute(dispatch, action) }
                                else native.execute(dispatch, action)
                            permitted = null; permitUntil = 0
                            val receipt = delivery.receipt(result)
                            phase = "result delivery"
                            withContext(Dispatchers.IO) { require(connection.call("deliver", JSONObject().put("delivery_id", delivery.id).put("result", receipt)).getBoolean("accepted")) }
                        }
                        delay(1500)
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (failure: Exception) {
                    val location = failure.stackTrace.firstOrNull { it.className == NativeGridDelivery::class.java.name + "\$Companion" }
                    android.util.Log.w("OscarNativeWorker", "Stopped during $phase (${failure.javaClass.simpleName}, ${location?.lineNumber ?: 0})")
                    NativeWorker.state(false, "Disconnected or task outcome uncertain. Inspect Core before restarting.")
                }
                finally {
                    withdraw()
                    withContext(NonCancellable + Dispatchers.IO) { try { client?.call("advertise", JSONObject().put("workspace", client?.workspace()).put("capabilities", JSONArray())) } catch (_: Exception) { } }
                    stopSelf()
                }
            }
        } catch (_: Exception) { NativeWorker.state(false, "Android did not start the task service"); stopSelf() }
        return START_NOT_STICKY
    }
    override fun onDestroy() {
        withdraw(); client?.cancel(); work?.cancel(); adapter?.close(); scope.cancel()
        if (instance === this) instance = null
        unregisterReceiver(locked); stopForeground(STOP_FOREGROUND_REMOVE); super.onDestroy()
    }
    override fun onBind(intent: Intent?): IBinder? = null
    companion object { @Volatile internal var instance: NativeWorkerService? = null; private set }
}

internal fun nativeAdvertisement(id: String, node: String): JSONObject {
    require(id in nativeCapabilityIds)
    val perception = id in setOf("android.ui.inspect", "android.files.read", "android.clipboard.read", "android.media.inspect", "android.screen.capture")
    val risk = when { perception -> "low"; id in setOf("android.app.launch", "android.link.open", "android.ui.scroll", "android.contact.view", "android.settings.open", "android.media.control") -> "medium"; else -> "high" }
    return JSONObject().put("id", id).put("name", id).put("summary", "Selected-app Android operation; OS and local grants rechecked")
        .put("execution_class", "machine").put("node_id", node).put("permissions", JSONArray(listOf(if (perception) "android:perceive" else "android:act")))
        .put("input_kind", id.replace('.', '_')).put("output_kind", "reference").put("risk", risk).put("version", 1).put("reversible", false)
}
