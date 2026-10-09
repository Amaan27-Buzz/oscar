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
pub struct CoreClient {
    url: String,
    node: String,
    session: String,
    token: Zeroizing<String>,
    client: Client,
    signer: Arc<Signer>,
    pending: Mutex<HashMap<String, Pending>>,
    pub reference: bool,
    pub reference_target: Option<Value>,
}
struct Pending {
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
            url: bootstrap.url.trim_end_matches('/').into(),
            node: bootstrap.node,
            session: bootstrap.session,
            token: Zeroizing::new(bootstrap.token),
            client,
            signer,
            pending: Mutex::new(HashMap::new()),
            reference: bootstrap.reference,
            reference_target: bootstrap.reference_target,
        })
    }
    pub fn request(&self, operation: &str, payload: Value) -> Result<Value, String> {
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
            .map_err(|_| "Core unavailable; outcome UNKNOWN; inspect before retry")?;
        if !response.status().is_success() {
            return Err(format!(
                "Core rejected {operation}; refresh task/context or permission"
            ));
        }
        let mut bytes = Vec::new();
        response
            .take(65537)
            .read_to_end(&mut bytes)
            .map_err(|_| "Core response unavailable")?;
        if bytes.len() > 65536 {
            return Err("Core response exceeds boundary".into());
        }
        let value: Value = serde_json::from_slice(&bytes).map_err(|_| "invalid Core response")?;
        if serde_json::to_string(&value)
            .map_err(|_| "invalid Core response")?
            .contains(self.token.as_str())
        {
            return Err("Core credential cannot enter presentation".into());
        }
        Ok(value)
    }
    pub fn snapshot(&self) -> Result<(Vec<TaskView>, Vec<CapabilityView>, u64), String> {
        let value = self.request("snapshot", json!({}))?;
        let tasks =
            serde_json::from_value(value["tasks"].clone()).map_err(|_| "invalid Core task view")?;
        let catalog = self.request("catalog", json!({}))?;
        let caps = serde_json::from_value(catalog["capabilities"].clone())
            .map_err(|_| "invalid Core capability view")?;
        Ok((tasks, caps, value["observed_at_ms"].as_u64().unwrap_or(0)))
    }
    pub fn review(&self, task_id: &str, operation: ControlOperation) -> Result<ReviewView, String> {
        bound(task_id, 80)?;
        let value = self.request(
            "challenge",
            json!({"operation":operation,"task_id":task_id}),
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
            || body.len() > 16384
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
        let text = |name: &str| -> Result<String, String> {
            let text = value[name].as_str().ok_or("invalid Core review")?;
            bound(text, 12000)?;
            Ok(text.into())
        };
        let id = uuid::Uuid::new_v4().simple().to_string();
        let view = ReviewView {
            review_id: id.clone(),
            operation: text("operation")?,
            description: text("description")?,
            target: text("target")?,
            capability: text("capability")?,
            reason: text("reason")?,
            consequence: text("consequence")?,
            policy_reason: text("policy_reason")?,
            evidence_state: text("evidence_state")?,
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
            "complete",
            json!({"challenge_id":pending.challenge_id,"signature":STANDARD.encode(signature)}),
        )
    }
    pub fn invalidate_reviews(&self) {
        if let Ok(mut p) = self.pending.lock() {
            p.clear();
        }
    }
}

pub struct Bridge {
    pub client: Mutex<Option<Arc<CoreClient>>>,
    pub view: Mutex<View>,
    pub capture_choice: Mutex<ContextChoice>,
    hide_private: AtomicBool,
    voice_revision: AtomicU64,
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
    pub fn refresh(&self) -> Result<View, String> {
        let client = self.client()?;
        if matches!(
            self.view().voice.as_str(),
            "listening" | "processing" | "speaking"
        ) {
            self.voice_request(json!({"operation":"inspect"}))?;
        }
        let (mut tasks, caps, at) = client.snapshot()?;
        if self.hide_private.load(Ordering::Acquire) {
            for task in &mut tasks {
                task.response = None;
                task.value = None;
            }
        }
        let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
        if let Some(current) = &view.current {
            view.current = tasks.iter().find(|t| t.task_id == current.task_id).cloned();
        }
        if at < view.observed_at_ms {
            return Ok(view.clone());
        }
        if view.link != "online" {
            if view.voice != "muted" {
                view.voice = "idle".into();
            }
            view.expression.voice_observed_at_ms = 0;
        }
        view.expression.generation += 1;
        view.expression.observed_at_ms = at;
        view.expression.tasks_observed_at_ms = at;
        view.expression.current_observed_at_ms = at;
        view.tasks = tasks;
        view.capabilities = caps;
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
        if message.starts_with("Core unavailable") {
            if view.link == "online" {
                view.expression.epoch = uuid::Uuid::new_v4().simple().to_string();
            }
            if view.voice != "muted" {
                view.voice = "idle".into();
            }
            view.expression.voice_observed_at_ms = 0;
            view.expression.generation += 1;
            view.expression.observed_at_ms = now_ms();
            view.link = "unavailable".into();
            view.capabilities.clear();
        }
        view.message = Some(message);
        view.orb = orb(&view.link, view.current.as_ref(), &view.voice);
        view.clone()
    }
    fn voice_request(&self, payload: Value) -> Result<View, String> {
        let revision = self.voice_revision.fetch_add(1, Ordering::SeqCst) + 1;
        let epoch = self.view().expression.epoch;
        let value = self.client()?.request("voice", payload)?;
        self.response_fenced(value, Some((revision, epoch)))
    }
    fn response(&self, value: Value) -> Result<View, String> {
        self.response_fenced(value, None)
    }
    fn response_fenced(
        &self,
        value: Value,
        voice_fence: Option<(u64, String)>,
    ) -> Result<View, String> {
        let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
        if let Some((revision, epoch)) = voice_fence
            && (revision != self.voice_revision.load(Ordering::SeqCst)
                || epoch != view.expression.epoch)
        {
            return Ok(view.clone());
        }
        view.message = value["message"].as_str().map(str::to_owned);
        if value["task_id"].is_string() {
            view.expression.current_observed_at_ms = now_ms();
            view.current =
                Some(serde_json::from_value(value.clone()).map_err(|_| "invalid Core task")?);
        }
        if value["preview_id"].is_string() {
            view.preview =
                Some(serde_json::from_value(value.clone()).map_err(|_| "invalid preview")?);
        }
        if value["state"] == "blocked" && !value["task_id"].is_string() {
            view.current = None;
            view.orb = "unavailable".into();
        }
        if value["state"] == "verified"
            && value["value"].is_string()
            && !value["task_id"].is_string()
        {
            view.message = Some(format!(
                "VERIFIED · OSCAR surface only: {}",
                value["value"].as_str().unwrap_or_default()
            ));
            view.preview = None;
        }
        if matches!(
            value["state"].as_str(),
            Some(
                "idle"
                    | "listening"
                    | "processing"
                    | "speaking"
                    | "muted"
                    | "interrupted"
                    | "cancelled"
            )
        ) && !value["task_id"].is_string()
        {
            view.voice = value["state"].as_str().unwrap_or_default().into();
            view.expression.voice_observed_at_ms = now_ms();
        }
        if value["preview_id"].is_string() || value["state"] == "blocked" {
            view.voice = "idle".into();
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
        if matches!(cmd, Command::Ready) {
            return Ok(self.view());
        }
        if matches!(cmd, Command::Discard) {
            self.hide_private.store(true, Ordering::Release);
            let mut view = self.view.lock().map_err(|_| "native state unavailable")?;
            view.context = None;
            view.preview = None;
            view.review = None;
            for task in &mut view.tasks {
                task.response = None;
                task.value = None;
            }
            if let Some(task) = &mut view.current {
                task.response = None;
                task.value = None;
            }
            view.message = None;
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
            return Ok(view.clone());
        }
        if matches!(
            cmd,
            Command::Interact { .. } | Command::Act { .. } | Command::Capture { .. }
        ) {
            self.hide_private.store(false, Ordering::Release);
        }
        let client = self.client()?;
        let value = match cmd {
            Command::Refresh => return self.refresh(),
            Command::Interact {
                mode,
                text,
                context_id,
            } => {
                bound(&text, 4096)?;
                bound(&context_id, 80)?;
                client.request(
                    "interact",
                    json!({"mode":mode,"text":text,"context_id":context_id}),
                )?
            }
            Command::Act {
                capability_id,
                form,
            } => client.request("act", form.core_payload(&capability_id)?)?,
            Command::Inspect { task_id } => {
                bound(&task_id, 80)?;
                client.request("inspect", json!({"task_id":task_id}))?
            }
            Command::Capture { source } => {
                if matches!(source, ContextChoice::None) {
                    return Err("choose an explicit context source".into());
                }
                let value = client.request("capture", json!({"source":source}))?;
                let context: ContextView = serde_json::from_value(value)
                    .map_err(|_| "Context unavailable or not permitted".to_string())?;
                self.view
                    .lock()
                    .map_err(|_| "native state unavailable")?
                    .context = Some(context);
                return Ok(self.view());
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
                client.request(
                    "apply",
                    json!({"preview_id":preview_id,"destination":destination}),
                )?
            }
            Command::Review { task_id, operation } => {
                let review = client.review(&task_id, operation)?;
                self.view
                    .lock()
                    .map_err(|_| "native state unavailable")?
                    .review = Some(review);
                return Ok(self.view());
            }
            Command::Confirm { review_id, accept } => {
                let result = client.confirm(&review_id, accept, owner_review)?;
                self.view
                    .lock()
                    .map_err(|_| "native state unavailable")?
                    .review = None;
                result
            }
            Command::VoiceStart { context_id } => {
                bound(&context_id, 80)?;
                return self.voice_request(json!({"operation":"start","context_id":context_id}));
            }
            Command::VoiceStop => return self.voice_request(json!({"operation":"stop"})),
            _ => return Err("native window command requires native handling".into()),
        };
        self.response(value)
    }
}
#[cfg(test)]
mod tests {
    use super::*;
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
            .response_fenced(json!({"state":"listening"}), Some((1, epoch.clone())))
            .unwrap();
        assert_eq!(stale.voice, "idle");
        let live = bridge
            .response_fenced(json!({"state":"listening"}), Some((2, epoch.clone())))
            .unwrap();
        assert_eq!(live.voice, "listening");
        assert!(live.expression.voice_observed_at_ms > 0);
        bridge.view.lock().unwrap().link = "online".into();
        let offline = bridge.fail("Core unavailable; fixture".into());
        assert_ne!(offline.expression.epoch, epoch);
        assert_eq!(offline.voice, "idle");
        assert_eq!(offline.expression.voice_observed_at_ms, 0);
        let stale = bridge
            .response_fenced(json!({"state":"speaking"}), Some((2, epoch)))
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
                challenge_id: "challenge".into(),
                body: vec![],
                view,
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
        let bridge = Bridge::new();
        bridge.view.lock().expect("view").current = Some(TaskView {
            task_id: "known".into(),
            state: "verified".into(),
            response: Some("private fixture".into()),
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
}
