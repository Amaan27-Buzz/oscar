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
    private val history = GridHistory()
    private var rejected = false
    private var enrollment: CoreClient? = null
    private var pendingShare: String? = null
    private var accountBrowser: AccountBrowser? = null
    private var accountJob: Job? = null
    private var accountClient: CoreClient? = null
    private var accountCode: String? = null
    internal val nativeCapabilities = NativeCapabilities(application)
    private fun connection(saved: JSONObject) = CoreClient(saved, vault::signDevice)
    internal fun phoneContextSource(id: String, retain: Boolean) = PhoneContext.configuration(getApplication(), client, id, retain)

    fun start() {
        nativeCapabilities.gate.foreground(true)
        active = true
        polling?.cancel()
        polling = viewModelScope.launch {
            val epoch = mutable.value.epoch
            if (client == null || mutable.value.draft.isEmpty()) {
                mutable.value = mutable.value.copy(restoring = true)
                try {
                    val saved = wire.withLock { withContext(Dispatchers.IO) {
                        val restored = client ?: vault.load()?.let { connection(it) }
                        val binding = restored?.binding() ?: "unpaired"
                        if (restored?.remote() == true && history.generation.isEmpty()) {
                            try { vault.loadHistory(binding)?.let(history::restore) }
                            catch (_: Exception) { history.clear(); vault.clearHistory() }
                        }
                        Triple(restored, vault.loadDraft(binding), vault.suppressed(binding))
                    } }
                    if (mutable.value.epoch == epoch) {
                        client = saved.first
                        if (mutable.value.draft.isEmpty()) mutable.value = mutable.value.copy(draft = saved.second, privateSuppressed = saved.third, restoring = false)
                        else mutable.value = mutable.value.copy(restoring = false)
                    }
                } catch (cancelled: CancellationException) { throw cancelled }
                catch (_: Exception) { if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Saved connection unavailable. Reconnect from trusted Core.") }
            }
            pendingShare?.let { pendingShare = null; acceptSharedText(it) }
            var failures = 0
            while (isActive && !rejected) {
                if (!mutable.value.busy) refresh()
                if (!mutable.value.busy && accountCode != null && mutable.value.link == Link.CONNECTED) finishAccountBrowser()
                failures = if (mutable.value.link == Link.CONNECTED) 0 else (failures + 1).coerceAtMost(4)
                delay(if (client?.remote() == true) reconnectDelay(failures, kotlin.random.Random.nextLong(1001)) else 15_000)
            }
        }
    }
    fun stop() {
        nativeCapabilities.gate.foreground(false)
        if (BuildConfig.DEBUG) android.util.Log.d("OscarSession", "stop; epoch=${mutable.value.epoch}")
        VoicePresentation.cancel(getApplication())
        val loaded = !mutable.value.restoring
        active = false
        replyText = null
        polling?.cancel(); operation?.cancel(); client?.cancel(); enrollment?.cancel()
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
            val remote = client?.remote() == true
            val started = android.os.SystemClock.elapsedRealtime()
            val response = call("snapshot", if (remote) history.request() else JSONObject(), epoch)
            val received = if (remote) parseGridSnapshot(response, client!!.coreId(), client!!.nodeId()).let { current ->
                if (client!!.canApprove()) current else current.copy(tasks = current.tasks.map { it.copy(actions = it.actions.filterNot { action -> action == "approve" }) })
            } else parseSnapshot(response)
            val clock = CoreClock.observe(received.observedAt, System.currentTimeMillis(), started, android.os.SystemClock.elapsedRealtime(), mutable.value.clock)
            if (remote && client?.hasScope("android:perceive") == true) try {
                PhoneContext.publish(getApplication()) { name, value -> call(name, value, epoch) }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (rejected: CoreClient.SessionRejected) { throw rejected }
            catch (_: Exception) { if (BuildConfig.DEBUG) android.util.Log.w("OscarSession", "Selected phone context unavailable") }
            received.presence?.let { require(io.dawnlight.oscar.expression.Contract.validate(it, clock.now(android.os.SystemClock.elapsedRealtime())) != null) }
            if (!active) return
            val interactions = if (remote && !mutable.value.privateSuppressed) gridInteractions(history.merge(response), received.tasks) else mutable.value.interactions
            if (remote && !mutable.value.privateSuppressed) wire.withLock { withContext(Dispatchers.IO) { vault.saveHistory(history.saved(), client!!.binding()) } }
            if (!active || mutable.value.epoch != epoch) return
            // History persistence suspends; preserve decisions and drafts changed during that wait.
            val old = mutable.value
            val snapshot = if (old.privateSuppressed) received.withoutPrivate() else received
            val next = old.fenced(old.copy(link = Link.CONNECTED, remote = remote, connectedNode = client?.nodeId(), snapshot = snapshot, observedAt = System.currentTimeMillis(), clock = clock,
                interactions = if (old.privateSuppressed) emptyList() else interactions,
                inspected = old.inspected?.let { selected -> snapshot.tasks.find { it.id == selected.id } },
                message = if (old.link == Link.CONNECTED) old.message else null), epoch)
            if (next == old) return
            mutable.value = next
            alerts.changed(old.snapshot, snapshot, clock.now(android.os.SystemClock.elapsedRealtime()))
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (_: CoreClient.SessionRejected) {
            nativeCapabilities.revoke()
            alerts.clearSentry()
            rejected = true
            if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("This device’s connection expired or was revoked. Re-enroll from your trusted Core.")
        }
        catch (failure: Exception) {
            nativeCapabilities.revoke()
            alerts.clearSentry()
            if (mutable.value.epoch == epoch) {
                if (BuildConfig.DEBUG) android.util.Log.w("OscarSession", "snapshot failed (${failure.javaClass.simpleName}); epoch=$epoch")
                mutable.value = mutable.value.unavailable("Core is unavailable or returned invalid state. No action is confirmed; refresh before retrying.")
            }
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
            catch (_: CoreClient.SessionRejected) {
                nativeCapabilities.revoke()
                alerts.clearSentry()
                rejected = true
                if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("This device’s connection expired or was revoked. Re-enroll from your trusted Core.")
            }
            catch (failure: Exception) {
                nativeCapabilities.revoke()
                alerts.clearSentry()
                if (mutable.value.epoch == epoch) {
                    if (BuildConfig.DEBUG) android.util.Log.w("OscarSession", "request failed (${failure.javaClass.simpleName}); epoch=$epoch")
                    mutable.value = mutable.value.unavailable("Request could not be confirmed. Inspect current Core state before retrying.")
                }
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
    fun acceptSharedText(text: String) {
        if (text.isBlank() || text.length > 1000) return
        if (mutable.value.restoring) { pendingShare = text; return }
        if (mutable.value.draft.isNotBlank() && mutable.value.draft != text) {
            message("Shared text was not imported because your existing draft is still open.")
            return
        }
        mutable.value = mutable.value.copy(draft = text)
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
        if (client?.remote() == true) return submitRemote(text, "text", client!!.coreId(), JSONObject())
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
    fun submitRemote(text: String, kind: String, target: String, parameters: JSONObject): Boolean {
        if (client?.remote() != true || text.isBlank() || text.length > 1000 || mutable.value.privateSuppressed) return false
        val retain = client!!.retainsConversation()
        if (!retain && kind != "text") { message("This action needs conversation sharing during trusted enrollment."); return false }
        if (kind !in setOf("text", "addition", "file_read", "file_write")) return false
        return request { epoch ->
            val result = call("submit", JSONObject().put("text", text).put("kind", kind).put("target", target)
                .put("parameters", parameters).put("retain", retain), epoch)
            if (result.has("assistance_proposal")) {
                stageManagement("assistance", result.getJSONObject("assistance_proposal"), epoch)
                return@request
            }
            if (result.has("assistance_started")) {
                parseStartedResponsibility(result.getJSONObject("assistance_started"))
                if (mutable.value.epoch == epoch && mutable.value.draft == text) writeDraft("")
                message("Started this objective within your Full Access. Check Automations for current progress.")
                refresh()
                return@request
            }
            if (result.optString("state") == "blocked" && !result.has("task_id")) {
                require(result.bounded("epistemic", 32) == "UNKNOWN")
                message(result.bounded("message", 1000))
                return@request
            }
            parseGridTask(result, mutable.value.snapshot?.nodes.orEmpty())
            if (mutable.value.epoch == epoch && mutable.value.draft == text) writeDraft("")
            refresh()
        }
    }
    fun inspect(id: String) = request { epoch ->
        val result = call("inspect", JSONObject().put("task_id", id), epoch)
        val task = if (client?.remote() == true) parseGridTask(result, mutable.value.snapshot?.nodes.orEmpty()).let {
            if (client!!.canApprove()) it else it.copy(actions = it.actions.filterNot { action -> action == "approve" })
        } else parseTask(result)
        require(task.id == id)
        if (mutable.value.epoch == epoch && !mutable.value.privateSuppressed) mutable.value = mutable.value.copy(inspected = task)
    }
    fun review(task: CoreTask, action: String) {
        if (action !in task.actions) return
        if (client?.remote() == true && action == "cancel") {
            request { epoch ->
                val result = parseGridTask(call("cancel", JSONObject().put("task_id", task.id), epoch), mutable.value.snapshot?.nodes.orEmpty())
                require(result.id == task.id)
                if (mutable.value.epoch == epoch) message("${result.label}. Cancellation cannot undo an effect already performed.")
                refresh()
            }
            return
        }
        request { epoch ->
            val approval = Approval.parse(call("challenge", JSONObject().put("operation", action).put("task_id", task.id), epoch), mutable.value.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime()))
            require(client?.matches(approval) == true)
            if (mutable.value.epoch == epoch) { replyText = null; mutable.value = mutable.value.copy(approval = approval, replyPreview = null) }
        }
    }
    fun dismissApproval() { replyText = null; mutable.value = mutable.value.copy(approval = null, replyPreview = null) }
    private fun clearAccountBrowser() {
        accountBrowser?.close(); accountBrowser = null; accountClient = null; accountCode = null
        accountJob?.cancel(); accountJob = null
    }
    fun cancelAccountEnrollment() { clearAccountBrowser(); message("Pending local account enrollment cancelled. No new connection is confirmed.") }
    private fun beginAccountBrowser(enrollment: JSONObject) {
        clearAccountBrowser()
        val browser = AccountBrowser(enrollment, mutable.value.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime()))
        accountBrowser = browser; accountClient = client
        accountJob = viewModelScope.launch {
            try {
                withContext(Dispatchers.IO) { browser.bind() }
                check(accountBrowser === browser && accountClient === client)
                val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(browser.url))
                    .addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                getApplication<Application>().startActivity(intent)
                val code = withContext(Dispatchers.IO) { browser.await() }
                if (accountBrowser === browser && accountClient === client) {
                    accountCode = code
                    if (active) { message("Authorization received. Checking your account with Core."); finishAccountBrowser() }
                    delay((browser.expiresAt - System.currentTimeMillis()).coerceIn(0, 600_000))
                    if (accountBrowser === browser) {
                        accountBrowser = null; accountClient = null; accountCode = null
                        if (active) message("Account enrollment expired. Review current Core connections before starting again.")
                    }
                }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) {
                if (accountBrowser === browser) {
                    accountCode = null; accountBrowser = null; accountClient = null
                    if (active) message("Provider enrollment did not finish. No account connection is confirmed. Check provider setup and start a new review.")
                }
            } finally { browser.close() }
        }
    }
    private fun finishAccountBrowser() {
        val browser = accountBrowser ?: return
        val code = accountCode ?: return
        if (accountClient !== client || System.currentTimeMillis() >= browser.expiresAt) { clearAccountBrowser(); return }
        if (!active || mutable.value.busy || mutable.value.link != Link.CONNECTED) return
        request { epoch ->
            // Consume locally once; ambiguous network outcomes are inspected, never automatically retried.
            accountCode = null
            val callback = JSONObject().put("id", browser.id).put("state", browser.state).put("code", code)
            browser.responseIssuer?.let { callback.put("iss", it) }
            val result = call("oauth_callback", callback, epoch)
            require(result.getString("status") == "verified")
            parseConnections(result.getJSONObject("connections"))
            clearAccountBrowser()
            message(result.bounded("message", 1000)); refresh()
        }
    }
    fun reviewManagement(family: String, change: JSONObject): Boolean {
        val snapshot = mutable.value.snapshot ?: return false
        if (client?.remote() != true || client?.canApprove() != true || mutable.value.privateSuppressed ||
            family !in setOf("authority", "assistance", "management") || snapshot.management == null) return false
        val proposal = JSONObject(change.toString())
        return request { epoch ->
            stageManagement(family, proposal, epoch)
        }
    }
    private suspend fun stageManagement(family: String, proposal: JSONObject, epoch: Long) {
        require(client?.remote() == true && client?.canApprove() == true && !mutable.value.privateSuppressed)
        val snapshot = requireNotNull(mutable.value.snapshot)
        require(snapshot.management != null)
        val stamp = snapshot.managementStamp()
        val review = Approval.management(call("${family}_challenge", proposal, epoch), family, proposal, stamp,
            mutable.value.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime()))
        require(client?.matches(review) == true && mutable.value.snapshot?.managementStamp() == stamp)
        if (mutable.value.epoch == epoch && active && !mutable.value.privateSuppressed)
            mutable.value = mutable.value.copy(approval = review, replyPreview = null)
    }
    fun dayBrief(): Boolean {
        if (mutable.value.link != Link.CONNECTED || mutable.value.privateSuppressed) return false
        mutable.value = mutable.value.copy(dayBrief = null)
        return request { epoch ->
            val brief = parseDayBrief(call("day_brief", JSONObject(), epoch).getJSONObject("day_brief"))
            if (mutable.value.epoch == epoch && active && !mutable.value.privateSuppressed)
                mutable.value = mutable.value.copy(dayBrief = brief)
        }
    }
    fun revokeAuthority(): Boolean {
        if (client?.remote() != true || client?.canApprove() != true || mutable.value.privateSuppressed) return false
        return request { epoch ->
            val result = call("authority_revoke", JSONObject(), epoch).getJSONObject("authority")
            require(result.getString("mode") == "ask" && result.getString("status") == "inactive")
            mutable.value = mutable.value.copy(approval = null, message = "Standing delegation revoked. Effects already performed still need readback.")
            refresh()
        }
    }
    fun reviewReply(source: JSONObject, text: String) {
        if (text.isBlank() || text.length > 500) return
        request { epoch ->
            val proposal = JSONObject().put("operation", "reply").put("package", source.bounded("package", 256))
                .put("key_hash", source.bounded("key_hash", 64)).put("text_hash", NotificationBoundary.hash(text))
            val approval = Approval.parse(call("challenge", proposal, epoch), mutable.value.coreNow(System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime()))
            require(client?.matches(approval) == true)
            require(approval.acceptsReply(text))
            if (mutable.value.epoch == epoch) { replyText = text; mutable.value = mutable.value.copy(approval = approval, replyPreview = text) }
        }
    }
    fun complete(approval: Approval, expectedEpoch: Long) {
        if (mutable.value.epoch != expectedEpoch || client?.matches(approval) != true || !approval.current(mutable.value, System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime())) return
        request { epoch ->
            val signature = wire.withLock {
                check(mutable.value.epoch == epoch && approval.current(mutable.value, System.currentTimeMillis(), android.os.SystemClock.elapsedRealtime()))
                withContext(Dispatchers.IO) { vault.sign(approval.signingPayload) }
            }
            val started = android.os.SystemClock.elapsedRealtime()
            val result = call(approval.completion, JSONObject().put("challenge_id", approval.id).put("signature", signature), epoch)
            if (mutable.value.epoch != epoch || !active) return@request
            val message = if (approval.completion != "complete") {
                when (approval.completion) {
                    "authority_complete" -> { result.getJSONObject("authority"); "Access updated by Core. Check the current mode and expiry below." }
                    "assistance_complete" -> {
                        require(result.getString("status") in setOf("verified", "partially_verified", "unknown"))
                        if (result.optBoolean("memory_changed")) {
                            history.clear()
                            withContext(Dispatchers.IO) { vault.clearHistory() }
                            mutable.value = mutable.value.copy(snapshot = null)
                        }
                        result.bounded("message", 1000)
                    }
                    "management_complete" -> {
                        parseConnections(result.getJSONObject("connections"))
                        result.optJSONObject("enrollment")?.let { beginAccountBrowser(it) }
                        result.bounded("message", 1000)
                    }
                    else -> error("Unknown signed review route")
                }
            } else if (approval.operation == "reply") {
                val text = replyText ?: throw IllegalStateException("Reply context expired")
                require(result.bounded("status", 32) == "REPORTED")
                require(approval.acceptsPermit(result.getJSONObject("permit")))
                NotificationBoundary.send(result.getJSONObject("permit"), text, started)
                replyText = null
                "Reply handed to source app. Delivery is unverified."
            } else {
                val task = if (client?.remote() == true) parseGridTask(result, mutable.value.snapshot?.nodes.orEmpty()) else parseTask(result)
                require(task.id == approval.material().getString("task_id") && task.target == approval.target)
                "${task.label}${task.value?.let { ": $it" } ?: ""}"
            }
            mutable.value = mutable.value.copy(approval = null, replyPreview = null, message = message)
            refresh()
        }
    }
    fun message(value: String) { mutable.value = mutable.value.copy(message = value) }
    fun cancelRequest() {
        operation?.cancel(); client?.cancel()
        mutable.value = mutable.value.unavailable("Stopped waiting locally. Core execution may continue; reconnect and inspect before another action.")
    }
    fun connect(session: JSONObject) {
        clearAccountBrowser()
        NativeWorker.stop(getApplication())
        nativeCapabilities.revoke()
        CompanionOverlay.hide(getApplication())
        VoicePresentation.cancel(getApplication())
        operation?.cancel(); client?.cancel()
        client = null; history.clear(); rejected = false
        val epoch = mutable.value.epoch + 1
        mutable.value = MobileState(epoch = epoch, link = Link.CONNECTING, busy = true)
        operation = viewModelScope.launch {
            try {
                val next = wire.withLock {
                    check(mutable.value.epoch == epoch) { "Obsolete pairing" }
                    withContext(NonCancellable + Dispatchers.IO) { val next = connection(session); vault.save(session); next }
                }
                if (mutable.value.epoch == epoch) {
                    client = next; mutable.value = MobileState(epoch = epoch); refresh()
                    if (active && mutable.value.epoch == epoch) start()
                }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Connection could not be saved. Check the trusted origin and scoped credentials.") }
        }
    }
    fun deviceIdentity() {
        val epoch = mutable.value.epoch
        viewModelScope.launch {
            try {
                val identity = wire.withLock { withContext(Dispatchers.IO) { vault.deviceIdentity() } }
                if (mutable.value.epoch == epoch) mutable.value = mutable.value.copy(enrollmentIdentity = identity.toString(2))
            } catch (_: Exception) { if (mutable.value.epoch == epoch) message("Android device proof key is unavailable. Enrollment has not started.") }
        }
    }
    fun enroll(origin: String, invitation: JSONObject, retain: Boolean) {
        clearAccountBrowser()
        NativeWorker.stop(getApplication())
        nativeCapabilities.revoke()
        operation?.cancel(); client?.cancel(); enrollment?.cancel(); polling?.cancel()
        CompanionOverlay.hide(getApplication()); VoicePresentation.cancel(getApplication())
        val epoch = mutable.value.epoch + 1
        mutable.value = MobileState(epoch = epoch, link = Link.CONNECTING, busy = true)
        operation = viewModelScope.launch {
            try {
                val pending = CoreClient(JSONObject().put("url", origin)); enrollment = pending
                val issued = wire.withLock { withContext(Dispatchers.IO) { pending.enroll(invitation, vault.deviceIdentity(), vault::signDevice) } }
                ensureActive()
                if (mutable.value.epoch == epoch && active) connect(issued.put("retain_conversation", retain))
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { if (mutable.value.epoch == epoch) mutable.value = mutable.value.unavailable("Enrollment is unconfirmed. Check the trusted invitation, this device’s public identity and Core address. A consumed invitation needs re-issue.") }
            finally { enrollment?.cancel(); enrollment = null }
        }
    }
    fun revoke() {
        clearAccountBrowser()
        if (client?.remote() != true) { message("Remote revocation requires an authenticated Grid connection."); return }
        request { epoch ->
            require(call("revoke", JSONObject(), epoch).bounded("state", 32) == "revoked")
            if (mutable.value.epoch == epoch) clearLocal(true)
        }
    }
    fun rotateConnection() {
        clearAccountBrowser()
        NativeWorker.stop(getApplication())
        nativeCapabilities.revoke()
        if (client?.remote() != true) return
        request { epoch ->
            val previous = client!!
            val issued = call("rotate", JSONObject(), epoch)
            require(issued.get("version") == 2 && issued.getString("node_id") == previous.nodeId() && issued.getString("core_id") == previous.coreId())
            val draft = mutable.value.draft; val hidden = mutable.value.privateSuppressed
            val cached = if (!hidden && history.generation.isNotEmpty()) history.saved() else null
            val next = wire.withLock {
                check(active && mutable.value.epoch == epoch)
                withContext(NonCancellable + Dispatchers.IO) {
                    val next = connection(issued.put("url", vault.load()!!.getString("url")).put("retain_conversation", previous.retainsConversation()))
                    vault.save(issued); vault.saveDraft(draft, next.binding(), hidden)
                    cached?.let { vault.saveHistory(it, next.binding()) }
                    next
                }
            }
            if (active && mutable.value.epoch == epoch) {
                client = next
                mutable.value = mutable.value.copy(epoch = epoch + 1, approval = null, replyPreview = null, inspected = null, busy = false,
                    message = "Connection renewed. Previous credentials are fenced by Core.")
                refresh()
            }
        }
    }
    fun disconnect() { clearAccountBrowser(); clearLocal(false) }
    private fun clearLocal(revoked: Boolean) {
        clearAccountBrowser()
        NativeWorker.stop(getApplication())
        getApplication<Application>().stopService(android.content.Intent(getApplication(), NativeScreenService::class.java))
        CompanionOverlay.hide(getApplication(), disable = true)
        VoicePresentation.cancel(getApplication())
        stop(); client = null; history.clear(); rejected = false; alerts.clear()
        val epoch = mutable.value.epoch
        mutable.value = MobileState(epoch = epoch)
        viewModelScope.launch {
            try { wire.withLock {
                if (mutable.value.epoch == epoch) withContext(NonCancellable + Dispatchers.IO) { vault.forget() }
            }; if (mutable.value.epoch == epoch) message(if (revoked) "Core revoked this device. Local credentials removed." else "Local credentials removed. Revoke this node from Core separately.") }
            catch (_: Exception) { if (mutable.value.epoch == epoch) message("Local credential removal is unverified.") }
        }
        active = true
    }
    fun discard() {
        clearAccountBrowser()
        if (client?.remote() == true) {
            operation?.cancel(); client?.cancel(); history.clear()
            mutable.value = mutable.value.copy(epoch = mutable.value.epoch + 1, busy = false, draft = "", interactions = emptyList(), approval = null,
                replyPreview = null, inspected = null, dayBrief = null, privateSuppressed = true, snapshot = mutable.value.snapshot?.withoutPrivate())
            val epoch = mutable.value.epoch
            persistDraft("") {
                viewModelScope.launch {
                    try { wire.withLock { if (mutable.value.epoch == epoch) withContext(Dispatchers.IO) { vault.clearHistory() } }
                        if (mutable.value.epoch == epoch) message("Local private cache cleared. Retained Core history needs trusted Core forget; reconnect to read authorized history again.")
                    } catch (_: Exception) { if (mutable.value.epoch == epoch) message("Local history-cache removal is unverified.") }
                }
            }
            return
        }
        if (mutable.value.link == Link.CONNECTING) { message("Wait for the connection outcome or disconnect locally before clearing Core context."); return }
        operation?.cancel(); client?.cancel(); replyText = null
        mutable.value = mutable.value.copy(epoch = mutable.value.epoch + 1, busy = false, draft = "", interactions = emptyList(),
            approval = null, replyPreview = null, inspected = null, snapshot = null, dayBrief = null, privateSuppressed = true, message = "Clearing encrypted private recovery state…")
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
    override fun onCleared() { clearAccountBrowser(); nativeCapabilities.close(); client?.cancel(); enrollment?.cancel(); super.onCleared() }
}
