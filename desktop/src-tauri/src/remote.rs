//! Grid v2 transport and projection adapter. Core remains the only history/task authority.
use crate::{core::now_ms, protocol::*, secure_connection, signing::Signer};
use base64::{Engine, engine::general_purpose::STANDARD};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    io::Read,
    path::Path,
    sync::{Arc, Mutex},
    time::Duration,
};
use zeroize::{Zeroize, Zeroizing};

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Session {
    pub version: u32,
    pub core_id: String,
    pub node_id: String,
    pub session_id: String,
    pub token: String,
    pub expires_at_ms: u64,
    pub scopes: Vec<String>,
}
impl Drop for Session {
    fn drop(&mut self) {
        self.token.zeroize();
    }
}
#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Connection {
    pub url: String,
    pub installation_id: String,
    pub session: Option<Session>,
}
impl Connection {
    pub fn load(path: &Path) -> Result<Option<Self>, String> {
        secure_connection::load(path)?
            .map(|bytes| {
                serde_json::from_slice(&bytes)
                    .map_err(|_| "saved connection invalid; enroll again".into())
            })
            .transpose()
    }
    pub fn save(&self, path: &Path) -> Result<(), String> {
        let bytes = Zeroizing::new(serde_json::to_vec(self).map_err(|_| "connection invalid")?);
        secure_connection::save(path, &bytes)
    }
    pub fn prepare(url: String, path: &Path) -> Result<ConnectionView, String> {
        endpoint(&url)?;
        if let Some(saved) = Self::load(path)? {
            if saved.session.is_some() {
                return Err(
                    "Disconnect the current device before preparing another connection".into(),
                );
            }
            if saved.url == url {
                return saved.view("awaiting_enrollment");
            }
            return Err("Disconnect the prepared device before changing its Core".into());
        }
        let value = Self {
            url,
            installation_id: uuid::Uuid::new_v4().to_string(),
            session: None,
        };
        let view = value.view("awaiting_enrollment")?;
        value.save(path)?;
        Ok(view)
    }
    pub fn view(&self, status: &str) -> Result<ConnectionView, String> {
        let transport = Signer::persistent(&format!("{}-transport", self.installation_id))?;
        let owner = Signer::persistent(&format!("{}-owner", self.installation_id))?;
        Ok(ConnectionView {
            endpoint: self.url.clone(),
            installation_id: self.installation_id.clone(),
            node_id: self.session.as_ref().map(|s| s.node_id.clone()),
            status: status.into(),
            public_key: STANDARD.encode(transport.public_der()?),
            owner_public_key: STANDARD.encode(owner.public_der()?),
        })
    }
    pub fn enroll(&mut self, invitation: &str) -> Result<(), String> {
        self.enroll_using(invitation, &http()?)
    }
    fn enroll_using(&mut self, invitation: &str, client: &Client) -> Result<(), String> {
        bound(invitation, 16384)?;
        let value: Value =
            serde_json::from_str(invitation).map_err(|_| "invalid enrollment invitation")?;
        let signer = Signer::persistent(&format!("{}-transport", self.installation_id))?;
        let expires = value["expires_at_ms"]
            .as_u64()
            .ok_or("invalid enrollment expiry")?;
        if value["version"] != 2
            || value["role"] != "desktop"
            || value["installation_id"] != self.installation_id
            || value["public_key"] != STANDARD.encode(signer.public_der()?)
            || expires <= now_ms()
            || expires > now_ms() + 301000
        {
            return Err("invitation does not match this device or is expired".into());
        }
        let body = STANDARD
            .decode(
                value["signing_payload"]
                    .as_str()
                    .ok_or("missing enrollment proof")?,
            )
            .map_err(|_| "invalid enrollment proof")?;
        if body.len() > 16384 {
            return Err("enrollment proof exceeds boundary".into());
        }
        let claim: Value = serde_json::from_slice(&body).map_err(|_| "invalid enrollment claim")?;
        let owner = Signer::persistent(&format!("{}-owner", self.installation_id))?;
        if claim["version"] != 2
            || claim["owner_public_key"] != STANDARD.encode(owner.public_der()?)
            || claim["workspace"] != value["workspace"]
        {
            return Err("enrollment authority binding rejected".into());
        }
        for field in [
            "core_id",
            "node_id",
            "installation_id",
            "role",
            "challenge_id",
            "expires_at_ms",
            "public_key",
        ] {
            if claim[field] != value[field] {
                return Err("enrollment proof binding rejected".into());
            }
        }
        let response = post(
            client,
            &self.url,
            "/v2/grid/enroll",
            &serde_json::to_vec(&json!({"version":2,"challenge_id":value["challenge_id"],
                "signature":STANDARD.encode(signer.sign(&body)?)}))
            .map_err(|_| "invalid enrollment")?,
            None,
        )?;
        let session: Session =
            serde_json::from_value(response).map_err(|_| "invalid enrolled session")?;
        if session.version != 2
            || session.node_id != value["node_id"]
            || session.core_id != value["core_id"]
            || session.session_id.is_empty()
            || session.token.len() < 32
            || session.expires_at_ms <= now_ms()
        {
            return Err("Core enrollment identity mismatch".into());
        }
        self.session = Some(session);
        Ok(())
    }
}

pub fn endpoint(value: &str) -> Result<(), String> {
    let url = reqwest::Url::parse(value).map_err(|_| "trusted HTTPS Core origin required")?;
    if url.scheme() != "https"
        || url.host_str().is_none()
        || url.path() != "/"
        || url.query().is_some()
        || url.fragment().is_some()
        || !url.username().is_empty()
        || url.password().is_some()
        || value.ends_with('/')
        || value.len() > 2048
    {
        return Err("trusted HTTPS Core origin required".into());
    }
    Ok(())
}
fn http() -> Result<Client, String> {
    Client::builder()
        .no_proxy()
        .redirect(reqwest::redirect::Policy::none())
        .connect_timeout(Duration::from_secs(3))
        .timeout(Duration::from_secs(8))
        .build()
        .map_err(|_| "native HTTPS client unavailable".into())
}
fn post(
    client: &Client,
    url: &str,
    path: &str,
    bytes: &[u8],
    auth: Option<(&Session, &Signer)>,
) -> Result<Value, String> {
    if bytes.len() > 32768 {
        return Err("Grid request exceeds boundary".into());
    }
    let mut request = client
        .post(format!("{url}{path}"))
        .header("Content-Type", "application/json")
        .body(bytes.to_vec());
    if let Some((session, signer)) = auth {
        if session.expires_at_ms <= now_ms() {
            return Err("Permission denied: Core credential expired; enroll again".into());
        }
        let nonce = uuid::Uuid::new_v4().simple().to_string();
        let instant = now_ms().to_string();
        let proof = format!(
            "OSCAR-GRID-2\nPOST\n/v2/grid/request\n{}\n{}\n{nonce}\n{instant}\n{:x}",
            session.node_id,
            session.session_id,
            Sha256::digest(bytes)
        );
        request = request
            .bearer_auth(&session.token)
            .header("X-Oscar-Node", &session.node_id)
            .header("X-Oscar-Session", &session.session_id)
            .header("X-Oscar-Nonce", nonce)
            .header("X-Oscar-Time", instant)
            .header(
                "X-Oscar-Signature",
                STANDARD.encode(signer.sign(proof.as_bytes())?),
            );
    }
    let response = request
        .send()
        .map_err(|_| "Core unavailable; outcome UNKNOWN; inspect before retry")?;
    let status = response.status();
    let mut bytes = Vec::new();
    response
        .take(262145)
        .read_to_end(&mut bytes)
        .map_err(|_| "Core response unavailable")?;
    if bytes.len() > 262144 {
        return Err("Core response exceeds boundary".into());
    }
    if !status.is_success() {
        return Err(match status.as_u16() {
            401 => "Permission denied: Core credential revoked or expired",
            403 => "This action is denied; inspect current authority",
            500..=599 => "Core unavailable; outcome UNKNOWN; inspect before retry",
            _ => "Core rejected request; inspect before retry",
        }
        .into());
    }
    if let Some((session, _)) = auth
        && bytes
            .windows(session.token.len())
            .any(|window| window == session.token.as_bytes())
    {
        return Err("Core credential cannot enter presentation".into());
    }
    serde_json::from_slice(&bytes).map_err(|_| "invalid Core response".into())
}

#[derive(Default)]
struct Projection {
    cursor: u64,
    archive_generation: Option<String>,
    capabilities: Vec<Value>,
    nodes: Vec<Value>,
    conversation: ConversationView,
}
impl Projection {
    fn apply_events(&mut self, snapshot: &Value) -> Result<(), String> {
        let reset = snapshot["reset"].as_bool().ok_or("invalid archive reset")?;
        let cursor = snapshot["cursor"].as_u64().ok_or("invalid Core cursor")?;
        let generation = string(snapshot, "archive_generation")?;
        if !reset
            && (cursor < self.cursor
                || self
                    .archive_generation
                    .as_ref()
                    .is_some_and(|previous| previous != &generation))
        {
            return Err("Core archive cursor regressed".into());
        }
        let mut sequence = if reset { 0 } else { self.cursor };
        let mut turns = Vec::new();
        for event in snapshot["events"].as_array().ok_or("invalid Core events")? {
            let next = event["sequence"].as_u64().ok_or("invalid event sequence")?;
            if next <= sequence
                || next > cursor
                || !matches!(event["speaker"].as_str(), Some("owner" | "oscar"))
            {
                return Err("Core archive event order rejected".into());
            }
            let turn = ConversationTurn {
                id: string(event, "event_id")?,
                task_id: if event["task_id"].is_null() {
                    String::new()
                } else {
                    string(event, "task_id")?
                },
                role: string(event, "speaker")?,
                text: string(event, "text")?,
                status: string(event, "status")?,
                occurred_at: event["occurred_at"].as_f64().ok_or("invalid event time")?,
                retained: true,
            };
            if turns
                .iter()
                .any(|prior: &ConversationTurn| prior.id == turn.id)
                || (!reset
                    && self
                        .conversation
                        .turns
                        .iter()
                        .any(|prior| prior.id == turn.id))
            {
                return Err("Core archive event identity reused".into());
            }
            turns.push(turn);
            sequence = next;
        }
        if reset {
            self.conversation.turns.clear();
            self.conversation.revision += 1;
        }
        // Core sequence is authoritative even when events share a timestamp.
        self.conversation.turns.extend(turns);
        if self.conversation.turns.len() > 500 {
            let excess = self.conversation.turns.len() - 500;
            self.conversation.turns.drain(..excess);
        }
        self.cursor = cursor;
        self.archive_generation = Some(generation);
        Ok(())
    }
}
pub struct RemoteClient {
    pub endpoint: String,
    pub session: Session,
    signer: Arc<Signer>,
    client: Client,
    projection: Mutex<Projection>,
}
impl RemoteClient {
    pub fn new(connection: &Connection) -> Result<Self, String> {
        endpoint(&connection.url)?;
        let session = connection
            .session
            .clone()
            .ok_or("Core enrollment required")?;
        if session.version != 2
            || session.token.len() < 24
            || session.token.len() > 256
            || session.node_id.is_empty()
            || session.session_id.is_empty()
        {
            return Err("invalid Core enrollment".into());
        }
        Ok(Self {
            endpoint: connection.url.clone(),
            session,
            signer: Arc::new(Signer::persistent(&format!(
                "{}-transport",
                connection.installation_id
            ))?),
            client: http()?,
            projection: Mutex::new(Projection::default()),
        })
    }
    pub fn request(&self, operation: &str, payload: Value) -> Result<Value, String> {
        let bytes = serde_json::to_vec(&json!({"version":2,"request_id":uuid::Uuid::new_v4().simple().to_string(),"operation":operation,"payload":payload}))
            .map_err(|_| "invalid Grid request")?;
        post(
            &self.client,
            &self.endpoint,
            "/v2/grid/request",
            &bytes,
            Some((&self.session, &self.signer)),
        )
    }
    pub fn compatible(&self, operation: &str, payload: Value) -> Result<Value, String> {
        match operation {
            "snapshot" => {
                let mut projection = self
                    .projection
                    .lock()
                    .map_err(|_| "native synchronization unavailable")?;
                let mut payload = json!({"cursor":projection.cursor});
                if let Some(generation) = &projection.archive_generation {
                    payload["archive_generation"] = json!(generation);
                }
                let snapshot = self.request("snapshot", payload)?;
                if snapshot["version"] != 2
                    || snapshot["core_id"] != self.session.core_id
                    || snapshot["node_id"] != self.session.node_id
                {
                    return Err("Core synchronization identity mismatch".into());
                }
                let nodes = snapshot["nodes"]
                    .as_array()
                    .ok_or("invalid Core devices")?
                    .clone();
                let tasks: Vec<Value> = snapshot["tasks"]
                    .as_array()
                    .ok_or("invalid Core tasks")?
                    .iter()
                    .map(task)
                    .collect::<Result<_, _>>()?;
                projection.apply_events(&snapshot)?;
                projection.conversation.persistence =
                    if self.session.scopes.iter().any(|s| s == "archive:read") {
                        "authorized"
                    } else {
                        "unavailable"
                    }
                    .into();
                projection.conversation.retention =
                    self.session.scopes.iter().any(|s| s == "archive:retain");
                projection.capabilities = capabilities(&nodes);
                projection.nodes = nodes;
                Ok(
                    json!({"tasks":tasks,"nodes":projection.nodes,"conversation":projection.conversation,
                    "presence":snapshot["presence"],
                    "observed_at_ms":snapshot["observed_at_ms"],"voice_available":false,
                    "operating":{"access":"Ask","secure":"unavailable","full_access":"unavailable"}}),
                )
            }
            "catalog" => Ok(
                json!({"capabilities":self.projection.lock().map_err(|_| "native synchronization unavailable")?.capabilities}),
            ),
            "interact" => {
                if payload["mode"] != "Ask" || payload["context_id"] != "" {
                    return Err("This remote capability is unavailable".into());
                }
                let result = self.request("submit", json!({"text":payload["text"],"kind":"text","target":self.session.core_id,"parameters":{},"retain":true}))?;
                task(&result)
            }
            "act" => {
                let capability = string(&payload, "capability_id")?;
                let projection = self
                    .projection
                    .lock()
                    .map_err(|_| "native synchronization unavailable")?;
                let selected = projection
                    .capabilities
                    .iter()
                    .find(|c| c["id"] == capability)
                    .ok_or("connected capability unavailable")?;
                let (kind, parameters) = match payload["operation"].as_str() {
                    Some("read_file") => ("file_read", json!({"path":payload["fields"]["path"]})),
                    Some("write_file") => (
                        "file_write",
                        json!({"path":payload["fields"]["path"],"content":payload["fields"]["text"]}),
                    ),
                    _ => return Err("This remote capability is unavailable".into()),
                };
                let target = selected["node"].clone();
                drop(projection);
                let result = self.request("submit", json!({"text":format!("{kind}: {}", parameters["path"].as_str().unwrap_or("")),"kind":kind,"target":target,"parameters":parameters,"retain":true}))?;
                task(&result)
            }
            "inspect" | "complete" => task(&self.request(operation, payload)?),
            "challenge" if payload["operation"] == "cancel" => {
                Err("Use Cancel request for remote cancellation".into())
            }
            "challenge" => self.request(operation, payload),
            "discard" => Ok(json!({"discarded":true})),
            _ => Err("This remote capability is unavailable".into()),
        }
    }
}
fn string(value: &Value, key: &str) -> Result<String, String> {
    value[key]
        .as_str()
        .map(str::to_owned)
        .ok_or_else(|| format!("invalid Core {key}"))
}
pub fn task(value: &Value) -> Result<Value, String> {
    let state = string(value, "state")?;
    let retained = value["retained_available"]
        .as_bool()
        .ok_or("invalid retained availability")?;
    let task_id = string(value, "task_id")?;
    let correlation = string(value, "correlation_id")?;
    let action = string(value, "action_id")?;
    let evidence = value["evidence"]
        .as_array()
        .ok_or("invalid task evidence")?;
    let approval = value["approval_required"]
        .as_bool()
        .ok_or("invalid task approval")?;
    if evidence.len() > 100
        || (!retained && (!evidence.is_empty() || !value["result"].is_null() || approval))
    {
        return Err("redacted task exposed retained material".into());
    }
    let mut verified = false;
    for receipt in evidence {
        if receipt["task_id"] != task_id
            || receipt["correlation_id"] != correlation
            || (!receipt["matches"].is_null() && !receipt["matches"].is_boolean())
            || !matches!(
                receipt["status"].as_str(),
                Some("VERIFIED" | "REPORTED" | "UNKNOWN" | "INFERRED" | "KNOWN" | "RECALLED")
            )
        {
            return Err("task evidence correlation rejected".into());
        }
        verified |= receipt["matches"] == true && receipt["status"] == "VERIFIED";
    }
    if !value["result"].is_null() {
        let result = &value["result"];
        if result["task_id"] != task_id
            || result["correlation_id"] != correlation
            || result["action_id"] != action
            || result["status"] != "REPORTED"
            || !result["success"].is_boolean()
            || (state == "verified" && result["success"] != true)
            || (!result["value"].is_null()
                && result["value"]
                    .as_str()
                    .is_none_or(|text| text.len() > 8192))
        {
            return Err("task result correlation rejected".into());
        }
    }
    if retained && state == "verified" && (!verified || value["result"].is_null()) {
        return Err("verified task lacks correlated result and evidence".into());
    }
    let mut actions = Vec::new();
    if value["approval_required"] == true {
        actions.push("approve");
    }
    if matches!(state.as_str(), "planned" | "executing" | "awaiting_result") {
        actions.push("cancel");
    }
    Ok(
        json!({"task_id":task_id,"state":state,"retained_available":retained,"description":value["description"],"generation":value["generation"].as_u64().unwrap_or(0),
        "target":value["target"],"blocker":if retained {value["blocker"].clone()} else {json!("Retained result and evidence are unavailable")},"actions":actions,"value":if retained {value["result"]["value"].clone()} else {Value::Null},
        "evidence":evidence.iter().map(|e|json!({"id":e["id"],"source":e["source"],"method":e["method"],"observed_at":e["observed_at"],"matches":e["matches"],"status":e["status"]})).collect::<Vec<_>>(),
        "mode":"Ask","epistemic":if !retained {"UNKNOWN"} else if state=="verified" {"VERIFIED"} else {"REPORTED"}}),
    )
}
fn capabilities(nodes: &[Value]) -> Vec<Value> {
    nodes.iter().filter(|node| matches!(node["status"].as_str(),Some("online"|"degraded")))
        .flat_map(|node| node["capabilities"].as_array().into_iter().flatten().map(move |cap| json!({
            "id":format!("{}:{}",node["id"].as_str().unwrap_or(""),cap["id"].as_str().unwrap_or("")),
            "node":node["id"],"kind":cap["input_kind"],"label":cap["name"],"summary":cap["summary"],"risk":cap["risk"],"permissions":cap["permissions"],
            "operations":match cap["id"].as_str() {Some("machine.files.read")=>vec!["read_file"],Some("machine.files.write")=>vec!["write_file"],_=>vec![]},"programs":[],"applications":[] }))).collect()
}

#[cfg(debug_assertions)]
pub fn fixture_cli(arguments: &[String]) -> Result<bool, String> {
    let Some(operation) = arguments
        .get(1)
        .filter(|value| value.starts_with("--grid-fixture-"))
    else {
        return Ok(false);
    };
    let state = Path::new(arguments.get(2).ok_or("fixture state path required")?);
    if operation == "--grid-fixture-identity" {
        if state.exists() {
            return Err("new disposable fixture state required".into());
        }
        let url = arguments.get(3).ok_or("fixture Core URL required")?.clone();
        endpoint(&url)?;
        let value = Connection {
            url,
            installation_id: format!("fixture-{}", uuid::Uuid::new_v4()),
            session: None,
        };
        value.save(state)?;
        println!(
            "{}",
            serde_json::to_string(&value.view("awaiting_enrollment")?)
                .map_err(|_| "invalid public fixture identity")?
        );
        return Ok(true);
    }
    let mut connection = Connection::load(state)?.ok_or("fixture identity missing")?;
    if !connection.installation_id.starts_with("fixture-") {
        return Err("synthetic fixture identity required".into());
    }
    if operation == "--grid-fixture-cleanup" {
        Signer::remove_persistent(&format!("{}-transport", connection.installation_id))?;
        Signer::remove_persistent(&format!("{}-owner", connection.installation_id))?;
        secure_connection::remove(state)?;
        println!("{{\"fixture_keys_removed\":true}}");
        return Ok(true);
    }
    let ca_index = if operation == "--grid-fixture-enroll" {
        4
    } else {
        3
    };
    let ca = std::fs::read(
        arguments
            .get(ca_index)
            .ok_or("trusted fixture CA required")?,
    )
    .map_err(|_| "fixture CA unavailable")?;
    let client = Client::builder()
        .no_proxy()
        .redirect(reqwest::redirect::Policy::none())
        .connect_timeout(Duration::from_secs(3))
        .timeout(Duration::from_secs(8))
        .add_root_certificate(
            reqwest::Certificate::from_pem(&ca).map_err(|_| "invalid fixture CA")?,
        )
        .build()
        .map_err(|_| "fixture TLS client unavailable")?;
    if operation == "--grid-fixture-enroll" {
        let invitation =
            std::fs::read_to_string(arguments.get(3).ok_or("fixture invitation required")?)
                .map_err(|_| "fixture invitation unavailable")?;
        connection.enroll_using(&invitation, &client)?;
        connection.save(state)?;
        println!("{{\"enrolled\":true}}");
        return Ok(true);
    }
    let mut remote = RemoteClient::new(&connection)?;
    remote.client = client;
    let core = crate::core::CoreClient::from_remote_transport(&connection, remote)?;
    let result = match operation.as_str() {
        "--grid-fixture-snapshot" => core.request("snapshot", json!({}))?,
        "--grid-fixture-approve" => {
            let task = arguments.get(4).ok_or("fixture task required")?;
            let review = core.review(task, ControlOperation::Approve)?;
            core.confirm(&review.review_id, true, |_| true)?
        }
        _ => return Err("unknown native fixture operation".into()),
    };
    println!(
        "{}",
        serde_json::to_string(&result).map_err(|_| "invalid fixture projection")?
    );
    Ok(true)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn production_origin_and_reported_task_boundary() {
        for value in [
            "http://127.0.0.1:4",
            "https://user@example.org",
            "https://example.org/a",
            "https://example.org?token=secret",
            "https://example.org/",
        ] {
            assert!(endpoint(value).is_err());
        }
        assert!(endpoint("https://core.example.org:8443").is_ok());
        let value = task(&json!({"task_id":"one","action_id":"action","correlation_id":"corr","state":"unknown","description":"test","target":"desktop","approval_required":false,"retained_available":true,"result":{"task_id":"one","action_id":"action","correlation_id":"corr","success":true,"status":"REPORTED","value":"reported"},"evidence":[]})).unwrap();
        assert_eq!(value["epistemic"], "REPORTED");
        assert_eq!(value["actions"], json!([]));
        let redacted = task(&json!({"task_id":"redacted","action_id":"action","correlation_id":"corr","state":"verified","description":"Task","target":"desktop","approval_required":false,"retained_available":false,"evidence":[]})).unwrap();
        assert_eq!(redacted["state"], "verified");
        assert_eq!(redacted["epistemic"], "UNKNOWN");
        assert!(redacted["value"].is_null());
    }
    #[test]
    fn same_timestamp_events_keep_core_sequence_and_reject_cursor_regression() {
        let mut projection = Projection::default();
        let event = |id: &str, sequence: u64, speaker: &str| json!({"event_id":id,"sequence":sequence,"turn_id":"turn","task_id":"task","speaker":speaker,"text":"synthetic","status":"REPORTED","occurred_at":42.0});
        projection.apply_events(&json!({"reset":false,"cursor":2,"archive_generation":"epoch","events":[event("z-owner",1,"owner"),event("a-result",2,"oscar")]})).unwrap();
        assert_eq!(
            projection
                .conversation
                .turns
                .iter()
                .map(|turn| turn.id.as_str())
                .collect::<Vec<_>>(),
            vec!["z-owner", "a-result"]
        );
        assert!(
            projection
                .apply_events(
                    &json!({"reset":false,"cursor":1,"archive_generation":"epoch","events":[]})
                )
                .is_err()
        );
        assert_eq!(projection.cursor, 2);
        assert!(projection.apply_events(&json!({"reset":false,"cursor":4,"archive_generation":"epoch","events":[event("four",4,"owner"),event("three",3,"oscar")]})).is_err());
        assert_eq!(projection.conversation.turns.len(), 2);
    }
    #[test]
    fn verified_projection_requires_correlated_result_and_matching_proof() {
        let mut value = json!({"task_id":"task","action_id":"action","correlation_id":"corr","state":"verified","description":"Task","target":"desktop","approval_required":false,"retained_available":true,"result":{"task_id":"task","action_id":"action","correlation_id":"corr","success":true,"status":"REPORTED","value":"readback"},"evidence":[{"id":"proof","task_id":"task","correlation_id":"corr","matches":true,"status":"VERIFIED"}]});
        assert_eq!(task(&value).unwrap()["epistemic"], "VERIFIED");
        value["evidence"][0]["correlation_id"] = json!("other");
        assert!(task(&value).is_err());
        value["evidence"][0]["correlation_id"] = json!("corr");
        value["evidence"][0]["matches"] = json!(false);
        assert!(task(&value).is_err());
        value["evidence"][0]["matches"] = json!(true);
        value["result"]["action_id"] = json!("other");
        assert!(task(&value).is_err());
    }
}
