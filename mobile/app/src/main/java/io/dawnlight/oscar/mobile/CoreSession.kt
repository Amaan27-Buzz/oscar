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
    private val mutable = MutableStateFlow(MobileState(restoring = true))
    val state = mutable.asStateFlow()
    private val wire = Mutex()
    private var client: CoreClient? = null
    private var polling: Job? = null
    private var operation: Job? = null
    private var active = false
    private val alerts = TaskNotifications(application)
    private var replyText: String? = null
    private var draftWrite: Job? = null
    private var draftRevision = 0L

    fun start() {
        active = true
        polling?.cancel()
        polling = viewModelScope.launch {
            val epoch = mutable.value.epoch
            if (client == null || mutable.value.draft.isEmpty()) {
                mutable.value = mutable.value.copy(restoring = true)
                try {
                    val saved = wire.withLock { withContext(Dispatchers.IO) {
                        val connection = client ?: vault.load()?.let { CoreClient(it) }
                        val binding = connection?.binding() ?: "unpaired"
                        Triple(connection, vault.loadDraft(binding), vault.suppressed(binding))
                    } }
                    if (mutable.value.epoch == epoch) {
                        client = saved.first
                        if (mutable.value.draft.isEmpty()) mutable.value = mutable.value.copy(draft = saved.second, privateSuppressed = saved.third, restoring = false)
                        else mutable.value = mutable.value.copy(restoring = false)
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (_: Exception) { if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Saved connection unavailable. Reconnect from trusted Core.") }
            }
            while (isActive) { if (!mutable.value.busy) refresh(); delay(15_000) }
        }
    }
    fun stop() {
        val loaded = !mutable.value.restoring
        active = false
        replyText = null
        polling?.cancel(); operation?.cancel(); client?.cancel()
        mutable.value = MobileState(epoch = mutable.value.epoch + 1, draft = mutable.value.draft, privateSuppressed = mutable.value.privateSuppressed)
        if (loaded) writeDraft(mutable.value.draft)
    }
    private suspend fun call(operation: String, payload: JSONObject, epoch: Long): JSONObject = wire.withLock {
        check(active && mutable.value.epoch == epoch) { "Obsolete request" }
        val connection = client ?: throw IllegalStateException("No connection")
        withContext(Dispatchers.IO) { connection.call(operation, payload) }
    }
    suspend fun refresh() {
        if (client == null || !active) return
        val epoch = mutable.value.epoch
        try {
            val received = parseSnapshot(call("snapshot", JSONObject(), epoch))
            require(kotlin.math.abs(System.currentTimeMillis() - received.observedAt) <= 30_000) { "Stale Core observation" }
            val snapshot = if (mutable.value.privateSuppressed) received.withoutPrivate() else received
            if (!active) return
            val old = mutable.value
            val next = old.fenced(old.copy(link = Link.CONNECTED, snapshot = snapshot, observedAt = System.currentTimeMillis(),
                inspected = old.inspected?.let { selected -> snapshot.tasks.find { it.id == selected.id } },
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
    private fun request(work: suspend (Long) -> Unit): Boolean {
        if (!active || mutable.value.busy || client == null || mutable.value.link != Link.CONNECTED) return false
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
        return true
    }
    fun writeDraft(text: String) {
        if (mutable.value.restoring || mutable.value.link == Link.CONNECTING) return
        persistDraft(text)
    }
    private fun persistDraft(text: String, saved: () -> Unit = {}) {
        if (text.length > 1000) return
        mutable.value = mutable.value.copy(draft = text)
        draftWrite?.cancel()
        val epoch = mutable.value.epoch; val revision = ++draftRevision
        val hidden = mutable.value.privateSuppressed
        draftWrite = viewModelScope.launch {
            try { wire.withLock {
                if (mutable.value.epoch == epoch && draftRevision == revision) withContext(NonCancellable + Dispatchers.IO) {
                    vault.saveDraft(text, client?.binding() ?: "unpaired", hidden)
                }
            }; if (mutable.value.epoch == epoch && draftRevision == revision) saved()
            } catch (_: Exception) {
                if (mutable.value.epoch == epoch && draftRevision == revision) message("Draft is held for this process; encrypted recovery could not be verified.")
            }
        }
    }
    fun send(text: String): Boolean {
        if (text.isBlank() || text.length > 1000 || mutable.value.privateSuppressed) return false
        return request { epoch ->
            val result = call("text", JSONObject().put("text", text), epoch)
            val item = if (result.has("task_id")) {
                val task = parseTask(result)
                Interaction(text, task.label, task.id)
            } else {
                require(result.bounded("state", 32) == "blocked" && result.bounded("epistemic", 32) == "UNKNOWN")
                Interaction(text, result.bounded("message", 1000))
            }
            if (mutable.value.epoch == epoch) {
                mutable.value = mutable.value.copy(interactions = (mutable.value.interactions + item).takeLast(20))
                if (mutable.value.draft == text) writeDraft("")
            }
            refresh()
        }
    }
    fun inspect(id: String) = request { epoch ->
        val task = parseTask(call("inspect", JSONObject().put("task_id", id), epoch))
        require(task.id == id)
        if (mutable.value.epoch == epoch && !mutable.value.privateSuppressed) mutable.value = mutable.value.copy(inspected = task)
    }
    fun review(task: CoreTask, action: String) {
        if (action !in task.actions) return
        request { epoch ->
            val approval = Approval.parse(call("challenge", JSONObject().put("operation", action).put("task_id", task.id), epoch))
            if (mutable.value.epoch == epoch) mutable.value = mutable.value.copy(approval = approval)
        }
    }
    fun dismissApproval() { replyText = null; mutable.value = mutable.value.copy(approval = null) }
    fun reviewReply(source: JSONObject, text: String) {
        if (text.isBlank() || text.length > 500) return
        request { epoch ->
            val proposal = JSONObject().put("operation", "reply").put("package", source.bounded("package", 256))
                .put("key_hash", source.bounded("key_hash", 64)).put("text_hash", NotificationBoundary.hash(text))
            val approval = Approval.parse(call("challenge", proposal, epoch))
            if (mutable.value.epoch == epoch) { replyText = text; mutable.value = mutable.value.copy(approval = approval) }
        }
    }
    fun complete(approval: Approval, expectedEpoch: Long) {
        if (mutable.value.epoch != expectedEpoch || mutable.value.approval != approval) return
        request { epoch ->
            val signature = withContext(Dispatchers.IO) { vault.sign(approval.signingPayload) }
            val started = android.os.SystemClock.elapsedRealtime()
            val result = call("complete", JSONObject().put("challenge_id", approval.id).put("signature", signature), epoch)
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
        client = null
        val epoch = mutable.value.epoch + 1
        mutable.value = MobileState(epoch = epoch, link = Link.CONNECTING, busy = true)
        operation = viewModelScope.launch {
            try {
                val next = wire.withLock {
                    check(mutable.value.epoch == epoch) { "Obsolete pairing" }
                    withContext(NonCancellable + Dispatchers.IO) { val connection = CoreClient(session); vault.save(session); connection }
                }
                if (mutable.value.epoch == epoch) { client = next; mutable.value = MobileState(epoch = epoch); refresh() }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Connection could not be saved. Check the trusted origin and scoped credentials.") }
        }
    }
    fun disconnect() {
        stop(); client = null; alerts.clear()
        val epoch = mutable.value.epoch
        mutable.value = MobileState(epoch = epoch)
        viewModelScope.launch {
            try { wire.withLock {
                if (mutable.value.epoch == epoch) withContext(NonCancellable + Dispatchers.IO) { vault.forget() }
            }; if (mutable.value.epoch == epoch) message("Local credentials removed. Revoke this node from Core separately.") }
            catch (_: Exception) { if (mutable.value.epoch == epoch) message("Local credential removal is unverified.") }
        }
        active = true
    }
    fun discard() {
        if (mutable.value.link == Link.CONNECTING) { message("Wait for the connection outcome or disconnect locally before clearing Core context."); return }
        operation?.cancel(); client?.cancel(); replyText = null
        mutable.value = mutable.value.copy(epoch = mutable.value.epoch + 1, busy = false, draft = "", interactions = emptyList(),
            approval = null, inspected = null, snapshot = null, privateSuppressed = true, message = "Clearing encrypted private recovery state…")
        persistDraft("") {
        if (!request { epoch ->
            val result = call("discard", JSONObject(), epoch)
            require(result.get("discarded") == true && result.get("retained") == false)
            if (mutable.value.epoch == epoch) {
                mutable.value = mutable.value.copy(privateSuppressed = false, message = "Private interaction discarded. Active Core work is not implicitly cancelled.")
                writeDraft(mutable.value.draft)
            }
            refresh()
        }) message("Encrypted draft cleared. Core discard is unverified until connected; private readback stays hidden.")
        }
    }
    internal fun sourceBinding(): String? = client?.binding()
    fun closeInspector() { mutable.value = mutable.value.copy(inspected = null) }
    fun publicIdentity() {
        val epoch = mutable.value.epoch
        viewModelScope.launch {
            try { val identity = wire.withLock {
                check(mutable.value.epoch == epoch)
                withContext(NonCancellable + Dispatchers.IO) { vault.publicIdentity() }
            }; if (mutable.value.epoch == epoch) message(identity) }
            catch (_: Exception) { if (mutable.value.epoch == epoch) message("Owner key unavailable. Configure a device lock and verify platform support during commissioning.") }
        }
    }
    override fun onCleared() { client?.cancel(); super.onCleared() }
}
