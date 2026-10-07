package io.dawnlight.oscar.mobile

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONObject

/** Owns a connection and its transient readback. Core alone owns tasks, authority and memory. */
class CoreSession(application: Application) : AndroidViewModel(application) {
    private val vault = SessionVault(application)
    private val mutable = MutableStateFlow(MobileState())
    val state = mutable.asStateFlow()
    private val wire = Mutex()
    private var client: CoreClient? = null
    private var polling: Job? = null
    private var operation: Job? = null
    private var active = false
    private val alerts = TaskNotifications(application)
    private var replyText: String? = null

    fun start() {
        active = true
        polling?.cancel()
        polling = viewModelScope.launch {
            if (client == null) {
                val epoch = mutable.value.epoch
                try {
                    val saved = wire.withLock { withContext(Dispatchers.IO) { vault.load()?.let { CoreClient(it) } } }
                    if (mutable.value.epoch == epoch) client = saved
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (_: Exception) { mutable.value = mutable.value.unavailable("Saved connection unavailable. Reconnect from trusted Core.") }
            }
            while (isActive) { if (!mutable.value.busy) refresh(); delay(15_000) }
        }
    }
    fun stop() {
        active = false
        replyText = null
        polling?.cancel(); operation?.cancel(); client?.cancel()
        mutable.value = MobileState(epoch = mutable.value.epoch + 1)
    }
    private suspend fun call(operation: String, payload: JSONObject): JSONObject = wire.withLock {
        val connection = client ?: throw IllegalStateException("No connection")
        withContext(Dispatchers.IO) { connection.call(operation, payload) }
    }
    suspend fun refresh() {
        if (client == null || !active) return
        val epoch = mutable.value.epoch
        try {
            val snapshot = parseSnapshot(call("snapshot", JSONObject()))
            if (!active) return
            val old = mutable.value
            val next = old.fenced(old.copy(link = Link.CONNECTED, snapshot = snapshot,
                message = if (old.link == Link.CONNECTED) old.message else null), epoch)
            if (next == old) return
            mutable.value = next
            alerts.changed(old.snapshot, snapshot)
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (_: Exception) {
            if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Core is unavailable or returned invalid state. No action is confirmed; refresh before retrying.")
        }
    }
    fun refreshNow() { viewModelScope.launch { refresh() } }
    private fun request(work: suspend (Long) -> Unit) {
        if (!active || mutable.value.busy || client == null || mutable.value.link != Link.CONNECTED) return
        val epoch = mutable.value.epoch
        mutable.value = mutable.value.copy(busy = true, message = null)
        operation = viewModelScope.launch {
            try { work(epoch) }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) {
                if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Request could not be confirmed. Inspect current Core state before retrying.")
            } finally {
                if (mutable.value.epoch == epoch) mutable.value = mutable.value.copy(busy = false)
            }
        }
    }
    fun send(text: String) {
        if (text.isBlank() || text.length > 1000) return
        request { epoch ->
            val result = call("text", JSONObject().put("text", text))
            val item = if (result.has("task_id")) {
                val task = parseTask(result)
                Interaction(text, task.label, task.id)
            } else {
                require(result.bounded("state", 32) == "blocked" && result.bounded("epistemic", 32) == "UNKNOWN")
                Interaction(text, result.bounded("message", 1000))
            }
            if (mutable.value.epoch == epoch) mutable.value = mutable.value.copy(interactions = (mutable.value.interactions + item).takeLast(20))
            refresh()
        }
    }
    fun inspect(id: String) = request { epoch ->
        val task = parseTask(call("inspect", JSONObject().put("task_id", id)))
        require(task.id == id)
        if (mutable.value.epoch == epoch) mutable.value = mutable.value.copy(message = "${task.description}\n${task.label}\n${task.blocker ?: task.value ?: "No verified result available."}\nEvidence: ${task.evidence.size}")
    }
    fun review(task: CoreTask, action: String) {
        if (action !in task.actions) return
        request { epoch ->
            val approval = Approval.parse(call("challenge", JSONObject().put("operation", action).put("task_id", task.id)))
            if (mutable.value.epoch == epoch) mutable.value = mutable.value.copy(approval = approval)
        }
    }
    fun dismissApproval() { replyText = null; mutable.value = mutable.value.copy(approval = null) }
    fun reviewReply(source: JSONObject, text: String) {
        if (text.isBlank() || text.length > 500) return
        request { epoch ->
            val proposal = JSONObject().put("operation", "reply").put("package", source.bounded("package", 256))
                .put("key_hash", source.bounded("key_hash", 64)).put("text_hash", NotificationBoundary.hash(text))
            val approval = Approval.parse(call("challenge", proposal))
            if (mutable.value.epoch == epoch) { replyText = text; mutable.value = mutable.value.copy(approval = approval) }
        }
    }
    fun complete(approval: Approval, expectedEpoch: Long) {
        if (mutable.value.epoch != expectedEpoch || mutable.value.approval != approval) return
        request { epoch ->
            val signature = withContext(Dispatchers.IO) { vault.sign(approval.signingPayload) }
            val started = android.os.SystemClock.elapsedRealtime()
            val result = call("complete", JSONObject().put("challenge_id", approval.id).put("signature", signature))
            if (mutable.value.epoch != epoch || !active) return@request
            val message = if (approval.operation == "reply") {
                val text = replyText ?: throw IllegalStateException("Reply context expired")
                require(result.bounded("status", 32) == "REPORTED")
                require(approval.acceptsPermit(result.getJSONObject("permit")))
                NotificationBoundary.send(result.getJSONObject("permit"), text, started)
                replyText = null
                "Reply handed to source app. Delivery is unverified."
            } else {
                val task = parseTask(result)
                require(task.id == approval.material().getString("task_id") && task.target == approval.target)
                "${task.label}${task.value?.let { ": $it" } ?: ""}"
            }
            mutable.value = mutable.value.copy(approval = null, message = message)
            refresh()
        }
    }
    fun message(value: String) { mutable.value = mutable.value.copy(message = value) }
    fun cancelRequest() {
        operation?.cancel(); client?.cancel()
        mutable.value = mutable.value.unavailable("Stopped waiting locally. Core execution may continue; reconnect and inspect before another action.")
    }
    fun connect(session: JSONObject) {
        operation?.cancel(); client?.cancel()
        val epoch = mutable.value.epoch + 1
        mutable.value = MobileState(epoch = epoch, link = Link.CONNECTING, busy = true)
        operation = viewModelScope.launch {
            try {
                val next = withContext(Dispatchers.IO) { vault.save(session); CoreClient(session) }
                if (mutable.value.epoch == epoch) { client = next; mutable.value = MobileState(epoch = epoch); refresh() }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Connection could not be saved. Check the trusted origin and scoped credentials.") }
        }
    }
    fun disconnect() {
        stop(); client = null; alerts.clear()
        viewModelScope.launch {
            try { withContext(Dispatchers.IO) { vault.forget() }; message("Local credentials removed. Revoke this node from Core separately.") }
            catch (_: Exception) { message("Local credential removal is unverified.") }
        }
        active = true
    }
    fun publicIdentity() {
        viewModelScope.launch {
            try { message(withContext(Dispatchers.IO) { vault.publicIdentity() }) }
            catch (_: Exception) { message("Owner key unavailable. Configure a device lock and verify platform support during commissioning.") }
        }
    }
    override fun onCleared() { client?.cancel(); super.onCleared() }
}
