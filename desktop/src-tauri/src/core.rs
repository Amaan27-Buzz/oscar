use crate::{protocol::*, signing::Signer};
use base64::{Engine, engine::general_purpose::STANDARD};
use reqwest::blocking::Client;
use serde_json::{Value, json};
use std::{
    collections::HashMap,
    io::Read,
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, AtomicU64, Ordering},
    },
    time::{Duration, SystemTime, UNIX_EPOCH},
};
use zeroize::Zeroizing;

pub fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
struct CoreSnapshot {
    connections: Option<Value>,
    nodes: Vec<Value>,
    presence: Option<Value>,
    core_clock: Option<Value>,
    setup: Option<Value>,
    executive: Option<Value>,
    adaptive_views: Vec<Value>,
    tasks: Vec<TaskView>,
    capabilities: Vec<CapabilityView>,
    observed_at: u64,
    conversation: ConversationView,
    operating: Option<Value>,
    voice_available: bool,
}
pub struct CoreClient {
    remote: Option<crate::remote::RemoteClient>,
    url: String,
    node: String,
    session: String,
    token: Zeroizing<String>,
    client: Client,
    signer: Arc<Signer>,
    pending: Mutex<HashMap<String, Pending>>,
    oauth_active: AtomicBool,
    oauth_epoch: AtomicU64,
    oauth_notice: Mutex<Option<String>>,
    pub reference: bool,
    pub reference_target: Option<Value>,
}
struct Pending {
    complete_operation: String,
    challenge_id: String,
    body: Vec<u8>,
    view: ReviewView,
}

impl CoreClient {
    pub fn new(bootstrap: Bootstrap, signer: Arc<Signer>) -> Result<Self, String> {
        let url = reqwest::Url::parse(&bootstrap.url).map_err(|_| "Core endpoint rejected")?;
        if url.scheme() != "http"
            || url.host_str() != Some("127.0.0.1")
            || url.port().is_none()
            || url.path() != "/"
            || url.query().is_some()
            || url.fragment().is_some()
            || !url.username().is_empty()
            || url.password().is_some()
        {
            return Err("trusted loopback Core endpoint required".into());
        }
        for value in [&bootstrap.node, &bootstrap.session] {
            bound(value, 128)?;
            if value.is_empty() {
                return Err("Core enrollment required".into());
            }
        }
        if bootstrap.token.len() < 24 || bootstrap.token.len() > 256 {
            return Err("invalid native enrollment".into());
        }
        let client = Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .connect_timeout(Duration::from_secs(2))
            .timeout(Duration::from_secs(130))
            .build()
            .map_err(|_| "native Core client unavailable")?;
        Ok(Self {
            remote: None,
            url: bootstrap.url.trim_end_matches('/').into(),
            node: bootstrap.node,
            session: bootstrap.session,
            token: Zeroizing::new(bootstrap.token),
            client,
            signer,
            pending: Mutex::new(HashMap::new()),
            oauth_active: AtomicBool::new(false),
            oauth_epoch: AtomicU64::new(0),
            oauth_notice: Mutex::new(None),
            reference: bootstrap.reference,
            reference_target: bootstrap.reference_target,
        })
    }
    pub fn from_remote(connection: &crate::remote::Connection) -> Result<Self, String> {
        let remote = crate::remote::RemoteClient::new(connection)?;
        Self::from_remote_transport(connection, remote)
    }
    pub fn from_remote_transport(
        connection: &crate::remote::Connection,
        remote: crate::remote::RemoteClient,
    ) -> Result<Self, String> {
        let session = &remote.session;
        Ok(Self {
            url: remote.endpoint.clone(),
            node: session.node_id.clone(),
            session: session.session_id.clone(),
            token: Zeroizing::new(session.token.clone()),
            client: Client::new(),
            signer: Arc::new(Signer::persistent(&format!(
                "{}-owner",
                connection.installation_id
            ))?),
            pending: Mutex::new(HashMap::new()),
            oauth_active: AtomicBool::new(false),
            oauth_epoch: AtomicU64::new(0),
            oauth_notice: Mutex::new(None),
            reference: false,
            reference_target: None,
            remote: Some(remote),
        })
    }
    pub fn is_remote(&self) -> bool {
        self.remote.is_some()
    }
    pub fn remote_request(&self, operation: &str, payload: Value) -> Result<Value, String> {
        self.remote
            .as_ref()
            .ok_or("remote connection required")?
            .request(operation, payload)
    }
    pub fn request(&self, operation: &str, payload: Value) -> Result<Value, String> {
        if let Some(remote) = &self.remote {
            return remote.compatible(operation, payload);
        }
        let request = json!({"version":1,"request_id":uuid::Uuid::new_v4().simple().to_string(),
            "operation":operation,"payload":payload});
        let response = self
            .client
            .post(format!("{}/v1/desktop", self.url))
            .bearer_auth(self.token.as_str())
            .header("X-Oscar-Node", &self.node)
            .header("X-Oscar-Session", &self.session)
            .json(&request)
            .timeout(Duration::from_secs(
                if matches!(operation, "snapshot" | "catalog") {
                    5
                } else {
                    130
                },
            ))
            .send()
            .map_err(|error| {
                if error.is_timeout() {
                    "Core request timed out; outcome UNKNOWN; inspect before retry"
                } else {
                    "Core unavailable; outcome UNKNOWN; inspect before retry"
                }
            })?;
        let status = response.status();
        let limit = if matches!(operation, "snapshot" | "conversation") {
            4_194_304
        } else if matches!(operation, "assistance_complete" | "management_complete") {
            262_144
        } else {
            65_536
        };
        let mut bytes = Vec::new();
        response
            .take(limit + 1)
            .read_to_end(&mut bytes)
            .map_err(|_| "Core response unavailable")?;
        if bytes.len() as u64 > limit {
            return Err("Core response exceeds boundary".into());
        }
        let value: Value = serde_json::from_slice(&bytes).map_err(|_| "invalid Core response")?;
        if serde_json::to_string(&value)
            .map_err(|_| "invalid Core response")?
            .contains(self.token.as_str())
        {
            return Err("Core credential cannot enter presentation".into());
        }
        if !status.is_success() {
            let reason = value["message"]
                .as_str()
                .or_else(|| value["error"].as_str())
                .unwrap_or("Inspect Core for details");
            return Err(
                if status.as_u16() == 401
                    || (status.as_u16() == 403 && value["error"] == "permission_denied")
                {
                    format!("Permission denied by Core: {reason}")
                } else if matches!(status.as_u16(), 408 | 504) {
                    "Core request timed out; outcome UNKNOWN; inspect before retry".into()
                } else if status.is_server_error() {
                    format!(
                        "Core returned an error; outcome UNKNOWN; inspect before retry: {reason}"
                    )
                } else {
                    format!("Core rejected {operation}: {reason}")
                },
            );
        }
        Ok(value)
    }
    fn snapshot(&self) -> Result<CoreSnapshot, String> {
        let value = self.request("snapshot", json!({}))?;
        let tasks =
            serde_json::from_value(value["tasks"].clone()).map_err(|_| "invalid Core task view")?;
        let catalog = self.request("catalog", json!({}))?;
        let caps = serde_json::from_value(catalog["capabilities"].clone())
            .map_err(|_| "invalid Core capability view")?;
        let conversation = if value["conversation"].is_null() {
            ConversationView::default()
        } else {
            serde_json::from_value(value["conversation"].clone())
                .map_err(|_| "invalid Core conversation")?
        };
        let operating = value.get("operating").cloned();
        Ok(CoreSnapshot {
            connections: value.get("connections").cloned(),
            nodes: value["nodes"].as_array().cloned().unwrap_or_default(),
            presence: value.get("presence").cloned(),
            core_clock: value.get("core_clock").cloned(),
            setup: value.get("setup").cloned(),
            executive: value.get("executive").cloned(),
            adaptive_views: value["adaptive_views"]
                .as_array()
                .cloned()
                .unwrap_or_default(),
            tasks,
            capabilities: caps,
            observed_at: value["observed_at_ms"].as_u64().unwrap_or(0),
            conversation,
            operating,
            voice_available: value["voice_available"].as_bool().unwrap_or(false),
        })
    }
    pub fn review(&self, task_id: &str, operation: ControlOperation) -> Result<ReviewView, String> {
        self.review_change(task_id, operation, "challenge", "complete", None)
    }
    fn review_change(
        &self,
        task_id: &str,
        operation: ControlOperation,
        challenge_operation: &str,
        complete_operation: &str,
        payload: Option<Value>,
    ) -> Result<ReviewView, String> {
        bound(task_id, 80)?;
        let value = self.request(
            challenge_operation,
            payload.unwrap_or_else(|| json!({"operation":operation,"task_id":task_id})),
        )?;
        let body = STANDARD
            .decode(
                value["signing_payload"]
                    .as_str()
                    .ok_or("missing signing envelope")?,
            )
            .map_err(|_| "invalid signing envelope")?;
        let claim: Value = serde_json::from_slice(&body).map_err(|_| "invalid signing envelope")?;
        if claim["node_id"] != self.node
            || claim["session_id"] != self.session
            || claim["operation"]
                != serde_json::to_value(operation).map_err(|_| "invalid operation")?
            || claim["material"]["task_id"] != task_id
            || body.len() > 32768
        {
            return Err("signing envelope identity rejected".into());
        }
        let expires = value["expires_at_ms"]
            .as_u64()
            .ok_or("invalid review expiry")?;
        if expires <= now_ms() || expires > now_ms() + 31000 {
            return Err("review expired".into());
        }
        if claim["expires_at_ms"] != expires || claim["material"]["target"] != value["target"] {
            return Err("review presentation is not bound to signed target/expiry".into());
        }
        if self.is_remote() || challenge_operation.ends_with("_challenge") {
            use sha2::{Digest, Sha256};
            let mut digest = Sha256::new();
            for field in ["operation", "scope", "target", "review", "exact_request"] {
                let bytes = value[field]
                    .as_str()
                    .ok_or("invalid remote review")?
                    .as_bytes();
                digest.update((bytes.len() as u32).to_be_bytes());
                digest.update(bytes);
            }
            if claim["version"] != 2
                || (self.is_remote() && claim["scope"] != "grid:approve")
                || claim["generation"] != value["generation"]
                || claim["display_digest"] != format!("{:x}", digest.finalize())
            {
                return Err("exact displayed remote review binding rejected".into());
            }
        }
        let text = |name: &str| -> Result<String, String> {
            let text = value[name].as_str().ok_or("invalid Core review")?;
            bound(text, if name == "review" { 24000 } else { 12000 })?;
            Ok(text.into())
        };
        let id = uuid::Uuid::new_v4().simple().to_string();
        let view = ReviewView {
            review_id: id.clone(),
            task_id: task_id.into(),
            operation: text("operation")?,
            description: text("description")?,
            target: text("target")?,
            capability: text("capability")?,
            reason: text("reason")?,
            consequence: text("consequence")?,
            policy_reason: text("policy_reason")?,
            evidence_state: if self.is_remote() {
                "PLANNED".into()
            } else {
                text("evidence_state")?
            },
            review: text("review")?,
            expires_at_ms: expires,
        };
        let mut pending = self
            .pending
            .lock()
            .map_err(|_| "native review unavailable")?;
        pending.retain(|_, p| p.view.expires_at_ms > now_ms());
        if pending.len() >= 16 {
            return Err("review bound reached".into());
        }
        pending.insert(
            id,
            Pending {
                complete_operation: complete_operation.into(),
                challenge_id: text("challenge_id")?,
                body,
                view: view.clone(),
            },
        );
        Ok(view)
    }
    pub fn confirm<F: FnOnce(&ReviewView) -> bool>(
        &self,
        id: &str,
        accepted: bool,
        owner_review: F,
    ) -> Result<Value, String> {
        bound(id, 80)?;
        let pending = self
            .pending
            .lock()
            .map_err(|_| "native review unavailable")?
            .remove(id)
            .ok_or("review stale or already consumed")?;
        if pending.view.expires_at_ms <= now_ms() {
            return Err("review expired; inspect current task".into());
        }
        if !accepted || !owner_review(&pending.view) {
            return Ok(json!({"message":"Review dismissed; nothing executed"}));
        }
        if pending.view.expires_at_ms <= now_ms() {
            return Err("review expired during owner confirmation".into());
        }
        let signature = self.signer.sign(&pending.body)?;
        self.request(
            &pending.complete_operation,
            json!({"challenge_id":pending.challenge_id,"signature":STANDARD.encode(signature)}),
        )
    }
    pub fn invalidate_reviews(&self) {
        if let Ok(mut p) = self.pending.lock() {
            p.clear();
        }
    }
    fn start_oauth(self: &Arc<Self>, value: &mut Value) -> Result<(), String> {
        let Some(enrollment) = value.as_object_mut().and_then(|v| v.remove("enrollment")) else {
            return Ok(());
        };
        let enrollment = crate::oauth::Enrollment::parse(&enrollment, now_ms() / 1000)?;
        let listener = enrollment.bind()?;
        if self
            .oauth_active
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .is_err()
        {
            return Err("Finish the current account enrollment before starting another.".into());
        }
        if let Err(error) = enrollment.open() {
            self.oauth_active.store(false, Ordering::Release);
            return Err(error);
        }
        let client = Arc::clone(self);
        let epoch = self.oauth_epoch.load(Ordering::Acquire);
        std::thread::spawn(move || {
            let current = || client.oauth_epoch.load(Ordering::Acquire) == epoch;
            let result = enrollment.wait(listener, current).and_then(|code| {
                if !current() {
                    return Err("Account enrollment cancelled.".into());
                }
                client.request(
                    "oauth_callback",
                    json!({"id":enrollment.id,"state":enrollment.state(),"code":code}),
                )
            });
            if current() {
                let notice = match result {
                    Ok(value) => value["message"].as_str().unwrap_or("Account response received; check Connections for current state.").to_owned(),
                    Err(_) => "Account connection could not be verified. Check Connections before trying again.".into(),
                };
                if let Ok(mut pending) = client.oauth_notice.lock() {
                    *pending = Some(notice);
                }
            }
            client.oauth_active.store(false, Ordering::Release);
        });
        Ok(())
    }
    fn review_needs_task(&self, id: &str) -> bool {
        self.pending
            .lock()
            .ok()
            .and_then(|p| p.get(id).map(|r| r.complete_operation == "complete"))
            .unwrap_or(true)
    }
}

pub struct Bridge {
    pub client: Mutex<Option<Arc<CoreClient>>>,
    pub view: Mutex<View>,
    pub capture_choice: Mutex<ContextChoice>,
    hide_private: AtomicBool,
    voice_revision: AtomicU64,
    content_revision: AtomicU64,
}
impl Bridge {
    pub fn new() -> Self {
        Self {
            client: Mutex::new(None),
            view: Mutex::new(View {
                expression: ExpressionReadback {
                    epoch: uuid::Uuid::new_v4().simple().to_string(),
                    ..Default::default()
                },
                link: "unconfigured".into(),
                orb: "unavailable".into(),
                voice: "idle".into(),
                shortcut: "Not registered".into(),
                ..Default::default()
            }),
            capture_choice: Mutex::new(ContextChoice::None),
            hide_private: AtomicBool::new(false),
            voice_revision: AtomicU64::new(0),
            content_revision: AtomicU64::new(0),
        }
    }
    pub fn client(&self) -> Result<Arc<CoreClient>, String> {
        self.client
            .lock()
            .map_err(|_| "native connection unavailable")?
            .clone()
            .ok_or_else(|| "Core is not enrolled; native connection required".into())
    }
    pub fn view(&self) -> View {
        self.view.lock().unwrap_or_else(|p| p.into_inner()).clone()
    }
    pub fn replace_client(
        &self,
        client: Option<Arc<CoreClient>>,
    ) -> Result<Option<Arc<CoreClient>>, String> {
        let mut active = self
            .client
            .lock()
            .map_err(|_| "native connection unavailable")?;
        self.content_revision.fetch_add(1, Ordering::SeqCst);
        self.voice_revision.fetch_add(1, Ordering::SeqCst);
        if let Some(previous) = active.as_ref() {
            if self
                .view()
                .voice_settings
                .as_ref()
                .is_some_and(|settings| settings.continuous_active)
                || matches!(
                    self.view().voice.as_str(),
                    "listening" | "processing" | "speaking"
                )
            {
                let _ = previous.request("voice", json!({"operation":"cancel"}));
            }
            previous.invalidate_reviews();
            previous.oauth_epoch.fetch_add(1, Ordering::AcqRel);
        }
        Ok(std::mem::replace(&mut *active, client))
    }
    pub fn refresh(&self) -> Result<View, String> {
        let client = self.client()?;
        if matches!(
            self.view().voice.as_str(),
            "listening" | "processing" | "speaking" | "aware"
        ) || self
            .view()
            .voice_settings
            .as_ref()
            .is_some_and(|settings| settings.continuous_active)
        {
            self.voice_request(json!({"operation":"inspect"}))?;
        }
        let CoreSnapshot {
            connections,
            nodes,
            presence,
            core_clock,
            setup,
            executive,
            adaptive_views,
            mut tasks,
            capabilities: caps,
            observed_at: at,
            conversation,
            operating,
            voice_available,
        } = client.snapshot().map_err(|error| {
            if error.starts_with("Permission denied") {
                error
            } else {
                format!("Core unavailable; {error}")
            }
        })?;
        // Connection replacement or logout fences snapshots already in flight.
        let active = self
            .client
            .lock()
            .map_err(|_| "native connection unavailable")?;
        if !active
            .as_ref()
            .is_some_and(|value| Arc::ptr_eq(value, &client))
        {
            return Ok(self.view());
        }
        let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
        if at < view.observed_at_ms {
            return Ok(view.clone());
        }
        if self.hide_private.load(Ordering::Acquire) {
            for task in &mut tasks {
                task.response = None;
                task.value = None;
                task.source_event_ids.clear();
                task.artifacts.clear();
            }
        }
        // A snapshot started before a command must not erase its newer task/approval readback.
        if at >= view.expression.current_observed_at_ms {
            if let Some(current) = &view.current {
                view.current = tasks.iter().find(|t| t.task_id == current.task_id).cloned();
            }
            view.expression.current_observed_at_ms = at;
        }
        if view.link != "online" {
            if view.voice != "muted" {
                view.voice = "idle".into();
            }
            view.expression.voice_observed_at_ms = 0;
            if view
                .message
                .as_deref()
                .is_some_and(|m| m.starts_with("Core unavailable"))
            {
                view.message = None;
            }
        }
        view.expression.generation += 1;
        view.expression.observed_at_ms = at;
        view.expression.tasks_observed_at_ms = at;
        view.tasks = tasks;
        if view.review.as_ref().is_some_and(|review| {
            review.expires_at_ms <= now_ms()
                || (client.review_needs_task(&review.review_id)
                    && !view
                        .current
                        .as_ref()
                        .filter(|task| {
                            task.task_id == review.task_id
                                && view.expression.current_observed_at_ms
                                    >= view.expression.tasks_observed_at_ms
                        })
                        .or_else(|| {
                            view.tasks
                                .iter()
                                .find(|task| task.task_id == review.task_id)
                        })
                        .is_some_and(|task| task.actions.contains(&review.operation)))
        }) {
            client.invalidate_reviews();
            view.review = None;
        }
        view.capabilities = caps;
        if let Ok(mut notice) = client.oauth_notice.lock() {
            if let Some(message) = notice.take() {
                view.message = Some(message);
            }
        }
        view.nodes = nodes;
        if let Some(connection) = &mut view.connection {
            connection.status = "online".into();
        }
        view.operating = operating;
        view.connections = connections;
        view.presence = presence;
        view.core_clock = core_clock;
        view.setup = setup;
        view.executive = if self.hide_private.load(Ordering::Acquire) {
            None
        } else {
            executive
        };
        view.adaptive_views = if self.hide_private.load(Ordering::Acquire) {
            Vec::new()
        } else {
            adaptive_views
        };
        view.voice_available = voice_available;
        if !self.hide_private.load(Ordering::Acquire) {
            if client.is_remote() {
                view.conversation = conversation;
            } else {
                let unchanged = view.conversation.revision == conversation.revision
                    && view.conversation.persistence == conversation.persistence;
                let mut turns = if unchanged {
                    view.conversation
                        .turns
                        .iter()
                        .filter(|t| t.retained)
                        .cloned()
                        .collect()
                } else {
                    Vec::new()
                };
                let before = if unchanged && !turns.is_empty() {
                    view.conversation.before
                } else {
                    conversation.before
                };
                for turn in conversation.turns.iter().cloned() {
                    turns.retain(|prior| prior.task_id != turn.task_id || prior.role != turn.role);
                    turns.push(turn);
                }
                turns.sort_by(|a, b| a.occurred_at.total_cmp(&b.occurred_at));
                view.conversation = ConversationView {
                    turns,
                    before,
                    ..conversation
                };
            }
        }
        view.observed_at_ms = at;
        view.link = "online".into();
        view.reference = client.reference;
        view.orb = orb(&view.link, view.current.as_ref(), &view.voice);
        if let Some(context) = &mut view.context
            && now_ms() as f64 > context.timestamp * 1000. + 15000.
        {
            context.freshness = "stale".into();
        }
        Ok(view.clone())
    }
    pub fn fail(&self, message: String) -> View {
        let mut view = self.view.lock().unwrap_or_else(|p| p.into_inner());
        if message.starts_with("Core unavailable") || message.starts_with("Permission denied") {
            if view.link == "online" {
                view.expression.epoch = uuid::Uuid::new_v4().simple().to_string();
            }
            if view.voice != "muted" {
                view.voice = "idle".into();
            }
            view.expression.voice_observed_at_ms = 0;
            view.link = "unavailable".into();
            view.presence = None;
            view.core_clock = None;
            view.adaptive_views.clear();
            view.executive = None;
            view.day_brief = None;
            view.voice_settings = None;
            view.voice_devices.clear();
            view.voice_support = VoiceSupport::default();
            view.setup = None;
            view.connections = None;
            view.capabilities.clear();
            view.nodes.clear();
            if let Some(connection) = &mut view.connection {
                connection.status = if message.starts_with("Permission denied") {
                    "revoked_or_expired"
                } else {
                    "reconnecting"
                }
                .into();
            }
        }
        view.message = Some(message);
        view.expression.generation += 1;
        view.expression.observed_at_ms = now_ms();
        view.orb = orb(&view.link, view.current.as_ref(), &view.voice);
        view.clone()
    }
    pub fn fail_request(&self, message: String) -> View {
        let kind = if message.starts_with("Permission denied") {
            FeedbackKind::Denied
        } else if message.starts_with("Core unavailable") || message.contains("outcome UNKNOWN") {
            FeedbackKind::Unknown
        } else {
            FeedbackKind::Rejected
        };
        self.fail(message.clone());
        let mut view = self.view.lock().unwrap_or_else(|p| p.into_inner());
        view.feedback = Some(RequestFeedback {
            kind,
            message,
            observed_at_ms: now_ms(),
        });
        view.expression.generation += 1;
        view.expression.observed_at_ms = now_ms();
        view.clone()
    }
    fn voice_request(&self, payload: Value) -> Result<View, String> {
        let content_revision = self.content_revision.load(Ordering::SeqCst);
        let revision = self.voice_revision.fetch_add(1, Ordering::SeqCst) + 1;
        let epoch = self.view().expression.epoch;
        let operation = payload["operation"].as_str().unwrap_or_default().to_owned();
        let value = self.client()?.request("voice", payload)?;
        let value = if matches!(
            operation.as_str(),
            "settings" | "configure" | "mute" | "listen"
        ) && value["muted"].is_boolean()
        {
            json!({"voice_settings":value})
        } else if operation == "devices" && value["devices"].is_array() {
            json!({"voice_devices":value["devices"]})
        } else {
            value
        };
        self.response_fenced(value, Some((revision, epoch)), Some(content_revision))
    }
    #[cfg(test)]
    fn response(&self, value: Value) -> Result<View, String> {
        self.response_fenced(value, None, None)
    }
    fn response_fenced(
        &self,
        value: Value,
        voice_fence: Option<(u64, String)>,
        content_fence: Option<u64>,
    ) -> Result<View, String> {
        let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
        if content_fence
            .is_some_and(|revision| revision != self.content_revision.load(Ordering::SeqCst))
        {
            return Ok(view.clone());
        }
        if let Some((revision, epoch)) = voice_fence
            && (revision != self.voice_revision.load(Ordering::SeqCst)
                || epoch != view.expression.epoch)
        {
            return Ok(view.clone());
        }
        view.message = value["message"].as_str().map(str::to_owned);
        if let Some(settings) = value.get("voice_settings") {
            let settings: VoiceSettingsView = serde_json::from_value(settings.clone())
                .map_err(|_| "invalid Core audio settings")?;
            if settings.input_device.is_some_and(|device| device > 1024)
                || settings.output_device.is_some_and(|device| device > 1024)
            {
                return Err("Core audio device exceeds bound".into());
            }
            view.voice_support.persistent_mute = if settings.persisted {
                AwarenessAvailability::Available
            } else {
                AwarenessAvailability::Unavailable
            };
            view.voice_support.wake_word =
                if settings.continuous_available && settings.continuous_granted {
                    AwarenessAvailability::Available
                } else {
                    AwarenessAvailability::Unavailable
                };
            view.voice_settings = Some(settings);
        }
        if let Some(devices) = value["voice_devices"].as_array() {
            if devices.len() > 256 {
                return Err("audio inventory exceeds bound".into());
            }
            let devices: Vec<AudioDeviceView> = serde_json::from_value(json!(devices))
                .map_err(|_| "invalid Core audio inventory")?;
            if devices
                .iter()
                .any(|device| device.id > 1024 || device.name.len() > 640)
            {
                return Err("Core audio inventory field exceeds bound".into());
            }
            view.voice_devices = devices;
        }
        if let Some(connections) = value.get("connections") {
            view.connections = Some(connections.clone());
        }
        if !self.hide_private.load(Ordering::Acquire) {
            if let Some(brief) = value.get("day_brief") {
                view.day_brief = Some(brief.clone());
            }
            if let Some(executive) = value.get("executive") {
                view.executive = Some(executive.clone());
            }
            if let Some(assistance) = value.get("assistance") {
                if let Some(executive) = &mut view.executive {
                    executive["management"] = assistance.clone();
                }
            }
        }
        if let Some(authority) = value.get("authority") {
            if let Some(executive) = &mut view.executive {
                executive["management"]["authority"] = authority.clone();
            }
            if let Some(operating) = &mut view.operating {
                operating["access"] = json!(match authority["mode"].as_str() {
                    Some("full") => "Full Access",
                    Some("secure") => "Secure",
                    _ => "Ask",
                });
            }
        }
        if value["task_id"].is_string() {
            view.feedback = None;
            view.expression.current_observed_at_ms = now_ms();
            view.current =
                Some(serde_json::from_value(value.clone()).map_err(|_| "invalid Core task")?);
            if self.hide_private.load(Ordering::Acquire)
                && let Some(task) = &mut view.current
            {
                task.response = None;
                task.value = None;
                task.source_event_ids.clear();
                task.artifacts.clear();
            }
        }
        if value["preview_id"].is_string() && !self.hide_private.load(Ordering::Acquire) {
            view.preview =
                Some(serde_json::from_value(value.clone()).map_err(|_| "invalid preview")?);
            view.feedback = None;
        }
        if value["state"] == "blocked" && !value["task_id"].is_string() {
            view.current = None;
            view.orb = "unavailable".into();
            view.feedback = Some(RequestFeedback {
                kind: if value["reason"] == "permission_denied" {
                    FeedbackKind::Denied
                } else {
                    FeedbackKind::Blocked
                },
                message: value["message"]
                    .as_str()
                    .unwrap_or("Core blocked this request. Inspect the current state.")
                    .into(),
                observed_at_ms: now_ms(),
            });
        }
        if value["state"] == "verified"
            && value["value"].is_string()
            && !value["task_id"].is_string()
        {
            view.feedback = None;
            view.message = Some(format!(
                "VERIFIED · OSCAR surface only: {}",
                value["value"].as_str().unwrap_or_default()
            ));
            view.preview = None;
        }
        let voice_state = value["voice_state"].as_str().or_else(|| {
            if value["task_id"].is_string() {
                None
            } else {
                value["state"].as_str()
            }
        });
        if matches!(
            voice_state,
            Some(
                "idle"
                    | "listening"
                    | "processing"
                    | "speaking"
                    | "muted"
                    | "interrupted"
                    | "cancelled"
                    | "aware"
                    | "off"
            )
        ) {
            view.voice = voice_state.unwrap_or_default().into();
            view.expression.voice_observed_at_ms = now_ms();
        }
        if value["preview_id"].is_string() || value["state"] == "blocked" {
            view.voice = "idle".into();
        }
        if value["state"] == "cancelled" && !value["task_id"].is_string() {
            view.preview = None;
        }
        if view.current.is_some() {
            view.orb = orb(&view.link, view.current.as_ref(), &view.voice);
        }
        view.expression.generation += 1;
        view.expression.observed_at_ms = now_ms();
        Ok(view.clone())
    }
    pub fn execute<F: FnOnce(&ReviewView) -> bool>(
        &self,
        cmd: Command,
        owner_review: F,
    ) -> Result<View, String> {
        let revision = if matches!(cmd, Command::Ready | Command::Refresh) {
            None
        } else {
            Some(self.content_revision.fetch_add(1, Ordering::SeqCst) + 1)
        };
        let result = self.execute_at(cmd, owner_review, revision);
        if revision.is_some_and(|revision| revision != self.content_revision.load(Ordering::SeqCst))
        {
            return Ok(self.view());
        }
        result
    }
    fn execute_at<F: FnOnce(&ReviewView) -> bool>(
        &self,
        cmd: Command,
        owner_review: F,
        revision: Option<u64>,
    ) -> Result<View, String> {
        if matches!(cmd, Command::Ready) {
            return Ok(self.view());
        }
        if matches!(cmd, Command::Discard) {
            self.hide_private.store(true, Ordering::Release);
            let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
            view.context = None;
            view.preview = None;
            view.review = None;
            view.conversation = ConversationView::default();
            view.adaptive_views.clear();
            view.executive = None;
            view.day_brief = None;
            view.voice_settings = None;
            view.voice_devices.clear();
            view.voice_support = VoiceSupport::default();
            for task in &mut view.tasks {
                task.response = None;
                task.value = None;
                task.source_event_ids.clear();
                task.artifacts.clear();
            }
            if let Some(task) = &mut view.current {
                task.response = None;
                task.value = None;
                task.source_event_ids.clear();
                task.artifacts.clear();
            }
            view.message = None;
            view.feedback = None;
            drop(view);
            let acknowledged = if let Ok(client) = self.client() {
                client.invalidate_reviews();
                client.request("discard", json!({})).is_ok()
            } else {
                false
            };
            let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
            view.message = if acknowledged {
                None
            } else {
                Some("Local content discarded; Core acknowledgement unavailable".into())
            };
            view.expression.generation += 1;
            return Ok(view.clone());
        }
        if matches!(
            cmd,
            Command::Interact { .. }
                | Command::Act { .. }
                | Command::Capture { .. }
                | Command::VoiceStart { .. }
        ) {
            self.hide_private.store(false, Ordering::Release);
        }
        let client = self.client()?;
        let value = match cmd {
            Command::CancelRemote { task_id } => {
                let value = client.remote_request("cancel", json!({"task_id":task_id}))?;
                crate::remote::task(&value)?
            }
            Command::Refresh => return self.refresh(),
            Command::DayBrief => {
                self.hide_private.store(false, Ordering::Release);
                self.view
                    .lock()
                    .map_err(|_| "native state unavailable")?
                    .day_brief = None;
                client.request("day_brief", json!({}))?
            }
            Command::History { before } => {
                let page: ConversationView = serde_json::from_value(
                    client.request("conversation", json!({"before":before}))?,
                )
                .map_err(|_| "invalid Core conversation page")?;
                let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                if revision != Some(self.content_revision.load(Ordering::SeqCst))
                    || self.hide_private.load(Ordering::Acquire)
                {
                    return Ok(view.clone());
                }
                for turn in page.turns {
                    if !view
                        .conversation
                        .turns
                        .iter()
                        .any(|prior| prior.id == turn.id)
                    {
                        view.conversation.turns.push(turn);
                    }
                }
                view.conversation
                    .turns
                    .sort_by(|a, b| a.occurred_at.total_cmp(&b.occurred_at));
                view.conversation.before = page.before;
                view.conversation.persistence = page.persistence;
                view.conversation.revision = page.revision;
                return Ok(view.clone());
            }
            Command::Interact {
                mode,
                text,
                context_id,
            } => {
                bound(&text, 4096)?;
                bound(&context_id, 80)?;
                let result = client.request(
                    "interact",
                    json!({"mode":mode,"text":text,"context_id":context_id}),
                )?;
                if let Some(proposal) = result.get("assistance_proposal") {
                    if proposal.as_object().is_none_or(|p| p.len() != 3)
                        || proposal["operation"] != "create_natural"
                        || proposal["id"] != "new"
                        || !proposal["value"].is_object()
                    {
                        return Err("invalid responsibility proposal".into());
                    }
                    if revision != Some(self.content_revision.load(Ordering::SeqCst)) {
                        return Ok(self.view());
                    }
                    client.invalidate_reviews();
                    let review = client.review_change(
                        "new",
                        ControlOperation::Approve,
                        "assistance_challenge",
                        "assistance_complete",
                        Some(proposal.clone()),
                    )?;
                    let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                    if revision == Some(self.content_revision.load(Ordering::SeqCst)) {
                        view.review = Some(review);
                        view.expression.generation += 1;
                    }
                    return Ok(view.clone());
                }
                result
            }
            Command::Act {
                capability_id,
                form,
            } => client.request("act", form.core_payload(&capability_id)?)?,
            Command::Inspect { task_id } => {
                bound(&task_id, 80)?;
                client.invalidate_reviews();
                self.view
                    .lock()
                    .map_err(|_| "native state unavailable")?
                    .review = None;
                client.request("inspect", json!({"task_id":task_id}))?
            }
            Command::Capture { source } => {
                if matches!(source, ContextChoice::None) {
                    return Err("choose an explicit context source".into());
                }
                let payload = if client.reference
                    && matches!(source, ContextChoice::Focused | ContextChoice::Selection)
                {
                    if let Some(target) = &client.reference_target {
                        json!({"source":source,"target":target})
                    } else {
                        json!({"source":source})
                    }
                } else {
                    json!({"source":source})
                };
                let value = client.request("capture", payload)?;
                let context: ContextView = serde_json::from_value(value)
                    .map_err(|_| "Context unavailable or not permitted".to_string())?;
                let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                if revision == Some(self.content_revision.load(Ordering::SeqCst)) {
                    view.context = Some(context);
                    view.feedback = None;
                    view.expression.generation += 1;
                }
                return Ok(view.clone());
            }
            Command::Preview { task_id } => {
                bound(&task_id, 80)?;
                client.request("preview", json!({"task_id":task_id}))?
            }
            Command::Apply {
                preview_id,
                destination,
            } => {
                bound(&preview_id, 80)?;
                let result = client.request(
                    "apply",
                    json!({"preview_id":preview_id,"destination":destination}),
                )?;
                let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                if revision == Some(self.content_revision.load(Ordering::SeqCst))
                    && (result["task_id"].is_string()
                        || result["state"] == "verified"
                        || result["preview_consumed"] == true)
                {
                    view.preview = None;
                }
                drop(view);
                result
            }
            command @ (Command::ManageConnection { .. }
            | Command::ManageAssistance { .. }
            | Command::SetAccess { .. }) => {
                let (id, family, payload) = match command {
                    Command::ManageConnection {
                        operation,
                        id,
                        value,
                    } => {
                        bound(&operation, 40)?;
                        bound(&id, 80)?;
                        bound(&value, 20000)?;
                        (
                            id.clone(),
                            "management",
                            json!({"operation":operation,"id":id,"value":value}),
                        )
                    }
                    Command::ManageAssistance {
                        operation,
                        id,
                        value,
                    } => {
                        bound(&operation, 40)?;
                        bound(&id, 80)?;
                        (
                            id.clone(),
                            "assistance",
                            json!({"operation":operation,"id":id,"value":value}),
                        )
                    }
                    Command::SetAccess {
                        relationship_id,
                        value,
                    } => {
                        bound(&relationship_id, 80)?;
                        (relationship_id, "authority", value)
                    }
                    _ => unreachable!(),
                };
                if serde_json::to_vec(&payload)
                    .map_err(|_| "invalid management request")?
                    .len()
                    > 24000
                {
                    return Err("management request too large".into());
                }
                client.invalidate_reviews();
                let review = client.review_change(
                    &id,
                    ControlOperation::Approve,
                    &format!("{family}_challenge"),
                    &format!("{family}_complete"),
                    Some(payload),
                )?;
                let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                if revision == Some(self.content_revision.load(Ordering::SeqCst)) {
                    view.review = Some(review);
                    view.expression.generation += 1;
                }
                return Ok(view.clone());
            }
            Command::RevokeAccess => {
                client.invalidate_reviews();
                client.request("authority_revoke", json!({}))?
            }
            Command::Review { task_id, operation } => {
                client.invalidate_reviews();
                let review = client.review(&task_id, operation)?;
                let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                if revision == Some(self.content_revision.load(Ordering::SeqCst)) {
                    view.review = Some(review);
                    view.expression.generation += 1;
                }
                return Ok(view.clone());
            }
            Command::Confirm { review_id, accept } => {
                let mut result = client.confirm(&review_id, accept, owner_review)?;
                client.start_oauth(&mut result)?;
                let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
                if revision == Some(self.content_revision.load(Ordering::SeqCst)) {
                    view.review = None;
                }
                drop(view);
                result
            }
            Command::VoiceStart { context_id, mode } => {
                bound(&context_id, 80)?;
                return self.voice_request(
                    json!({"operation":"start","context_id":context_id,"mode":mode}),
                );
            }
            Command::VoiceSettings {} => {
                return self.voice_request(json!({"operation":"settings"}));
            }
            Command::VoiceDevices {} => return self.voice_request(json!({"operation":"devices"})),
            Command::VoiceListen {} => return self.voice_request(json!({"operation":"listen"})),
            Command::VoiceMute {} => return self.voice_request(json!({"operation":"mute"})),
            Command::VoiceConfigure {
                muted,
                input_device,
                output_device,
            } => {
                if input_device > 1024 || output_device.is_some_and(|device| device > 1024) {
                    return Err("audio device index exceeds bound".into());
                }
                return self.voice_request(json!({"operation":"configure", "muted":muted,
                    "input_device":input_device, "output_device":output_device}));
            }
            Command::VoiceStop => return self.voice_request(json!({"operation":"stop"})),
            Command::VoiceCancel => return self.voice_request(json!({"operation":"cancel"})),
            _ => return Err("native window command requires native handling".into()),
        };
        self.response_fenced(value, None, revision)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn audio_projection_is_current_bounded_and_withdrawn_after_connection_loss() {
        let bridge = Bridge::new();
        let settings = json!({"muted":true,"input_device":2,"output_device":null,
            "continuous_available":true,"continuous_active":false,
            "continuous_granted":true,"persisted":true});
        let view = bridge
            .response(json!({"voice_settings":settings,
            "voice_devices":[{"id":2,"name":"Synthetic input","input":true,"output":false}]}))
            .unwrap();
        assert!(view.voice_settings.unwrap().muted);
        assert_eq!(view.voice_devices.len(), 1);
        assert!(matches!(
            view.voice_support.persistent_mute,
            AwarenessAvailability::Available
        ));
        assert!(
            bridge
                .response(json!({"voice_settings":{"muted":false}}))
                .is_err()
        );
        let offline = bridge.fail("Core unavailable; synthetic disconnect".into());
        assert!(offline.voice_settings.is_none());
        assert!(offline.voice_devices.is_empty());
    }
    #[test]
    fn speech_lifecycle_preserves_issued_task_truth() {
        let bridge = Bridge::new();
        for speech in ["speaking", "cancelled", "idle"] {
            let view = bridge.response(json!({"task_id":"issued","state":"verified","target":"fixture","voice_state":speech})).unwrap();
            assert_eq!(view.voice, speech);
            assert_eq!(view.current.unwrap().state, "verified");
        }
    }
    #[test]
    #[ignore = "requires scripts.software_voice_reference synthetic local Core fixture"]
    fn synthetic_voice_loopback_bridge() {
        let path =
            std::env::var("OSCAR_VOICE_REFERENCE_BOOTSTRAP").expect("synthetic bootstrap required");
        let bytes = std::fs::read(path).expect("synthetic bootstrap readable");
        assert!(bytes.len() < 32768);
        let bootstrap: Bootstrap =
            serde_json::from_slice(&bytes).expect("bounded synthetic bootstrap");
        assert!(bootstrap.reference && bootstrap.url.starts_with("http://127.0.0.1:"));
        let client = CoreClient::new(bootstrap, Arc::new(Signer::new().unwrap())).unwrap();
        let bridge = Bridge::new();
        bridge.replace_client(Some(Arc::new(client))).unwrap();
        assert!(bridge.refresh().unwrap().voice_available);
        let proposed = bridge
            .execute(
                Command::Interact {
                    mode: InteractionMode::Ask,
                    text: "every day for 3 runs: 2 + 3".into(),
                    context_id: String::new(),
                },
                |_| false,
            )
            .unwrap();
        let review = proposed
            .review
            .expect("conversation must open exact responsibility review");
        assert!(review.review.contains("math.add"));
        bridge
            .execute(
                Command::Confirm {
                    review_id: review.review_id,
                    accept: false,
                },
                |_| false,
            )
            .unwrap();
        bridge
            .execute(
                Command::VoiceStart {
                    context_id: String::new(),
                    mode: VoiceMode::Ask,
                },
                |_| false,
            )
            .unwrap();
        let deadline = std::time::Instant::now() + std::time::Duration::from_secs(60);
        let task_id = loop {
            assert!(
                std::time::Instant::now() < deadline,
                "synthetic Ask voice timed out"
            );
            let view = bridge.refresh().unwrap();
            if view.voice == "idle" {
                let task = view.current.expect("Ask reached canonical task admission");
                assert_eq!(task.state, "planned");
                assert!(task.actions.contains(&"approve".into()));
                break task.task_id;
            }
            std::thread::sleep(std::time::Duration::from_millis(100));
        };
        let cancelled = bridge.execute(Command::VoiceCancel, |_| false).unwrap();
        assert_eq!(cancelled.voice, "cancelled");
        assert_eq!(cancelled.current.as_ref().unwrap().state, "planned");
        bridge
            .execute(
                Command::VoiceStart {
                    context_id: String::new(),
                    mode: VoiceMode::Dictate,
                },
                |_| false,
            )
            .unwrap();
        let deadline = std::time::Instant::now() + std::time::Duration::from_secs(60);
        loop {
            assert!(
                std::time::Instant::now() < deadline,
                "synthetic Dictate voice timed out"
            );
            let view = bridge.refresh().unwrap();
            if view.preview.is_some() {
                assert_eq!(view.current.unwrap().task_id, task_id);
                break;
            }
            std::thread::sleep(std::time::Duration::from_millis(100));
        }
    }
    #[test]
    fn discarded_or_obsolete_content_cannot_reappear_from_late_response() {
        let bridge = Bridge::new();
        bridge.content_revision.store(2, Ordering::SeqCst);
        let old = bridge.response_fenced(json!({"task_id":"old","state":"partially_verified","target":"fixture","response":"private sentinel"}), None, Some(1)).unwrap();
        assert!(old.current.is_none());
        bridge.hide_private.store(true, Ordering::Release);
        let hidden = bridge.response_fenced(json!({"task_id":"same","state":"partially_verified","target":"fixture","response":"private sentinel","value":"private sentinel"}), None, Some(2)).unwrap();
        let task = hidden.current.unwrap();
        assert!(task.response.is_none());
        assert!(task.value.is_none());
        let preview = bridge.response_fenced(json!({"preview_id":"late","before":"private sentinel","after":"private sentinel","epistemic":"REPORTED","expires":99,"destinations":["surface"]}), None, Some(2)).unwrap();
        assert!(preview.preview.is_none());
    }
    #[test]
    fn connection_replacement_fences_old_content() {
        let bridge = Bridge::new();
        let revision = bridge.content_revision.load(Ordering::SeqCst);
        assert!(bridge.replace_client(None).unwrap().is_none());
        let late = bridge.response_fenced(
            json!({"task_id":"old-core","state":"reported","response":"prior connection content"}),
            None,
            Some(revision),
        ).unwrap();
        assert!(late.current.is_none());
        assert!(late.tasks.is_empty());
    }
    #[test]
    fn connection_and_public_state_cannot_export_secrets() {
        let bootstrap = |url: &str| Bootstrap {
            url: url.into(),
            node: "node".into(),
            session: "session".into(),
            token: "native-secret-bearer-token-value".into(),
            reference: false,
            reference_target: None,
        };
        let signer = Arc::new(Signer::new().expect("native CNG"));
        for url in [
            "http://localhost:42",
            "http://127.0.0.1:42/path",
            "http://user@127.0.0.1:42",
            "https://evil.example",
        ] {
            assert!(CoreClient::new(bootstrap(url), signer.clone()).is_err());
        }
        let bridge = Bridge::new();
        let serialized = serde_json::to_string(&bridge.view()).expect("view");
        for secret in ["token", "signing_payload", "private_key", "session"] {
            assert!(!serialized.contains(secret));
        }
        assert!(bridge.execute(Command::Refresh, |_| true).is_err());
        assert_eq!(bridge.view().orb, "unavailable");
    }
    #[test]
    fn voice_readback_is_fenced_and_disconnect_clears_activity() {
        let bridge = Bridge::new();
        let epoch = bridge.view().expression.epoch;
        bridge.voice_revision.store(2, Ordering::SeqCst);
        let stale = bridge
            .response_fenced(json!({"state":"listening"}), Some((1, epoch.clone())), None)
            .unwrap();
        assert_eq!(stale.voice, "idle");
        let live = bridge
            .response_fenced(json!({"state":"listening"}), Some((2, epoch.clone())), None)
            .unwrap();
        assert_eq!(live.voice, "listening");
        assert!(live.expression.voice_observed_at_ms > 0);
        bridge.view.lock().unwrap().link = "online".into();
        let offline = bridge.fail("Core unavailable; fixture".into());
        assert_ne!(offline.expression.epoch, epoch);
        assert_eq!(offline.voice, "idle");
        assert_eq!(offline.expression.voice_observed_at_ms, 0);
        let stale = bridge
            .response_fenced(json!({"state":"speaking"}), Some((2, epoch)), None)
            .unwrap();
        assert_eq!(stale.voice, "idle");
        assert_eq!(stale.expression.generation, offline.expression.generation);
    }
    #[test]
    fn stale_reviews_and_offline_discard_fail_closed() {
        let client = CoreClient::new(
            Bootstrap {
                url: "http://127.0.0.1:9".into(),
                node: "node".into(),
                session: "session".into(),
                token: "native-reference-token-only".into(),
                reference: false,
                reference_target: None,
            },
            Arc::new(Signer::new().expect("CNG")),
        )
        .expect("client");
        let view = ReviewView {
            review_id: "stale".into(),
            task_id: "fixture".into(),
            operation: "approve".into(),
            description: "fixture".into(),
            target: "worker".into(),
            capability: "file_write".into(),
            reason: "fixture".into(),
            consequence: "fixture".into(),
            policy_reason: "fixture".into(),
            evidence_state: "planned".into(),
            review: "fixture".into(),
            expires_at_ms: 0,
        };
        client.pending.lock().expect("pending").insert(
            "stale".into(),
            Pending {
                complete_operation: "complete".into(),
                challenge_id: "challenge".into(),
                body: vec![],
                view: view.clone(),
            },
        );
        assert!(
            client
                .confirm("stale", true, |_| panic!(
                    "stale review must never reach owner dialog"
                ))
                .is_err()
        );
        assert!(client.confirm("stale", true, |_| true).is_err());
        let fresh = ReviewView {
            expires_at_ms: now_ms() + 30000,
            ..view
        };
        client.pending.lock().unwrap().insert(
            "fresh".into(),
            Pending {
                complete_operation: "complete".into(),
                challenge_id: "challenge".into(),
                body: vec![],
                view: fresh.clone(),
            },
        );
        assert!(client.review_needs_task("fresh"));
        assert!(client.review_needs_task("missing"));
        for operation in [
            "management_complete",
            "assistance_complete",
            "authority_complete",
        ] {
            client
                .pending
                .lock()
                .unwrap()
                .get_mut("fresh")
                .unwrap()
                .complete_operation = operation.into();
            assert!(!client.review_needs_task("fresh"));
        }
        client
            .pending
            .lock()
            .unwrap()
            .get_mut("fresh")
            .unwrap()
            .complete_operation = "complete".into();
        let switching = Bridge::new();
        *switching.client.lock().unwrap() = Some(Arc::new(client));
        switching.view.lock().unwrap().review = Some(fresh);
        assert!(
            switching
                .execute(
                    Command::Inspect {
                        task_id: "other".into()
                    },
                    |_| panic!("inspection grants no consent")
                )
                .is_err()
        );
        assert!(switching.view().review.is_none());
        assert!(
            switching
                .client()
                .unwrap()
                .pending
                .lock()
                .unwrap()
                .is_empty()
        );
        let bridge = Bridge::new();
        bridge.view.lock().expect("view").current = Some(TaskView {
            task_id: "known".into(),
            state: "verified".into(),
            response: Some("private fixture".into()),
            source_event_ids: vec!["private-source".into()],
            artifacts: vec![ArtifactView {
                id: "private-artifact".into(),
                kind: "file".into(),
                status: "REPORTED".into(),
                content_hash: None,
            }],
            ..Default::default()
        });
        let discarded = bridge
            .execute(Command::Discard, |_| false)
            .expect("local discard");
        assert_eq!(
            discarded.current.as_ref().expect("shared task").state,
            "verified"
        );
        assert!(
            discarded
                .current
                .as_ref()
                .unwrap()
                .source_event_ids
                .is_empty()
        );
        assert!(discarded.current.as_ref().unwrap().artifacts.is_empty());
        assert!(
            discarded
                .current
                .as_ref()
                .expect("shared task")
                .response
                .is_none()
        );
        let blocked = bridge
            .response(json!({"state":"blocked","message":"capability withdrawn"}))
            .expect("response");
        assert!(blocked.current.is_none());
        assert_eq!(blocked.orb, "unavailable");
    }
    #[test]
    fn request_feedback_is_specific_fresh_and_never_fabricates_a_task() {
        let bridge = Bridge::new();
        bridge.view.lock().unwrap().link = "online".into();
        let blocked = bridge.response(json!({"state":"blocked","reason":"capability_unavailable","message":"Worker unavailable; nothing executed"})).unwrap();
        assert!(matches!(
            blocked.feedback.unwrap().kind,
            FeedbackKind::Blocked
        ));
        assert!(blocked.current.is_none());
        let denied = bridge.response(json!({"state":"blocked","reason":"permission_denied","message":"Policy denies this request"})).unwrap();
        assert!(matches!(
            denied.feedback.unwrap().kind,
            FeedbackKind::Denied
        ));
        let revision = denied.expression.generation;
        let unknown = bridge
            .fail_request("Core request timed out; outcome UNKNOWN; inspect before retry".into());
        assert!(matches!(
            unknown.feedback.unwrap().kind,
            FeedbackKind::Unknown
        ));
        assert!(unknown.expression.generation > revision);
        assert!(unknown.current.is_none());
        let resolved = bridge.response(json!({"task_id":"exact","state":"planned","target":"fixture","actions":["approve"]})).unwrap();
        assert!(resolved.feedback.is_none());
        assert_eq!(resolved.current.unwrap().state, "planned");
    }
    #[test]
    fn http_permission_rejection_and_uncertain_server_failure_remain_distinct() {
        use std::net::TcpListener;
        for (status, body, expected) in [
            (
                403,
                r#"{"error":"permission_denied","message":"Core denied permission"}"#,
                "Permission denied by Core",
            ),
            (
                403,
                r#"{"error":"request rejected; refresh trusted Core state"}"#,
                "Core rejected interact",
            ),
            (503, r#"{"error":"Core unavailable"}"#, "outcome UNKNOWN"),
        ] {
            let listener = TcpListener::bind("127.0.0.1:0").unwrap();
            let url = format!("http://{}", listener.local_addr().unwrap());
            let server = std::thread::spawn(move || {
                use std::io::Write;
                let (mut connection, _) = listener.accept().unwrap();
                let mut request = [0; 4096];
                assert!(connection.read(&mut request).unwrap() > 0);
                write!(connection, "HTTP/1.1 {status} Fixture\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}", body.len()).unwrap();
            });
            let client = CoreClient::new(
                Bootstrap {
                    url,
                    node: "fixture".into(),
                    session: "fixture".into(),
                    token: "disposable-reference-token-only".into(),
                    reference: true,
                    reference_target: None,
                },
                Arc::new(Signer::new().unwrap()),
            )
            .unwrap();
            let error = client.request("interact", json!({})).unwrap_err();
            assert!(error.contains(expected), "{error}");
            server.join().unwrap();
        }
    }
    #[test]
    fn older_snapshot_preserves_new_task_and_fresh_completion_retires_review() {
        use std::{io::Write, net::TcpListener};
        let base = now_ms().saturating_sub(2000);
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let url = format!("http://{}", listener.local_addr().unwrap());
        let server = std::thread::spawn(move || {
            let responses = [
                json!({"tasks":[],"observed_at_ms":base+200}),
                json!({"capabilities":[]}),
                json!({"tasks":[{"task_id":"new","state":"verified","target":"fixture","actions":[]}],"observed_at_ms":base+600}),
                json!({"capabilities":[]}),
            ];
            for response in responses {
                let (mut connection, _) = listener.accept().unwrap();
                let mut request = [0; 4096];
                assert!(connection.read(&mut request).unwrap() > 0);
                let body = response.to_string();
                write!(
                    connection,
                    "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
                    body.len()
                )
                .unwrap();
            }
        });
        let client = Arc::new(
            CoreClient::new(
                Bootstrap {
                    url,
                    node: "fixture".into(),
                    session: "fixture".into(),
                    token: "disposable-reference-token-only".into(),
                    reference: true,
                    reference_target: None,
                },
                Arc::new(Signer::new().unwrap()),
            )
            .unwrap(),
        );
        let bridge = Bridge::new();
        *bridge.client.lock().unwrap() = Some(client);
        {
            let mut view = bridge.view.lock().unwrap();
            view.observed_at_ms = base;
            view.expression.current_observed_at_ms = base + 400;
            view.current = Some(TaskView {
                task_id: "new".into(),
                state: "planned".into(),
                actions: vec!["approve".into()],
                ..Default::default()
            });
            view.review = Some(ReviewView {
                review_id: "review".into(),
                task_id: "new".into(),
                operation: "approve".into(),
                description: "Fixture".into(),
                target: "fixture".into(),
                capability: "math.add".into(),
                reason: "Owner review".into(),
                consequence: "Add integers".into(),
                policy_reason: "Fixture".into(),
                evidence_state: "planned".into(),
                review: "2+3".into(),
                expires_at_ms: now_ms() + 30000,
            });
        }
        let older = bridge.refresh().unwrap();
        assert_eq!(older.current.unwrap().state, "planned");
        assert!(older.review.is_some());
        assert_eq!(older.expression.current_observed_at_ms, base + 400);
        let fresh = bridge.refresh().unwrap();
        assert_eq!(fresh.current.unwrap().state, "verified");
        assert!(fresh.review.is_none());
        server.join().unwrap();
    }
}
