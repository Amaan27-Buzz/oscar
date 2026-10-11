use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Bootstrap {
    pub url: String,
    pub node: String,
    pub session: String,
    pub token: String,
    #[serde(default)]
    pub reference: bool,
    #[serde(default)]
    pub reference_target: Option<Value>,
}

#[derive(Clone, Copy, Deserialize, Serialize, Default, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum WindowMode {
    #[default]
    Compact,
    Interaction,
    Approval,
    Activity,
    Reading,
    Tools,
    Actions,
}

#[derive(Clone, Copy, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum ContextChoice {
    None,
    Selection,
    Focused,
    Foreground,
}

#[derive(Deserialize)]
#[serde(tag = "operation", rename_all = "snake_case", deny_unknown_fields)]
pub enum ActForm {
    WriteFile { path: String, text: String },
    ReadFile { path: String },
    ListFiles,
    FindFiles { pattern: String },
    GitStatus,
    GitDiff,
    GitLog,
    GitBranches,
    GitBranch { name: String },
    PsEnvironment,
    PsFileHash { path: String },
    PsWriteUtf8 { path: String, text: String },
    ProgramVersion { program_id: String },
    InspectPage { url: String },
    ListApps,
    LaunchApp { app_id: String },
    WorkerTools,
}
impl ActForm {
    pub fn core_payload(&self, capability_id: &str) -> Result<Value, String> {
        let (operation, fields) = match self {
            Self::WriteFile { path, text } => ("write_file", json!({"path":path,"text":text})),
            Self::ReadFile { path } => ("read_file", json!({"path":path})),
            Self::ListFiles => ("list_files", json!({})),
            Self::FindFiles { pattern } => ("find_files", json!({"pattern":pattern})),
            Self::GitStatus => ("git_status", json!({})),
            Self::GitDiff => ("git_diff", json!({})),
            Self::GitLog => ("git_log", json!({})),
            Self::GitBranches => ("git_branches", json!({})),
            Self::GitBranch { name } => ("git_branch", json!({"name":name})),
            Self::PsEnvironment => ("ps_environment", json!({})),
            Self::PsFileHash { path } => ("ps_file_hash", json!({"path":path})),
            Self::PsWriteUtf8 { path, text } => ("ps_write_utf8", json!({"path":path,"text":text})),
            Self::ProgramVersion { program_id } => {
                ("program_version", json!({"program_id":program_id}))
            }
            Self::InspectPage { url } => ("inspect_page", json!({"url":url})),
            Self::ListApps => ("list_apps", json!({})),
            Self::LaunchApp { app_id } => ("launch_app", json!({"app_id":app_id})),
            Self::WorkerTools => ("worker_tools", json!({})),
        };
        bound(capability_id, 256)?;
        for (name, value) in fields.as_object().ok_or("invalid form")? {
            let text = value.as_str().ok_or("invalid field")?;
            bound(text, if name == "text" { 4096 } else { 500 })?;
            if name == "path" {
                relative_path(text)?;
            }
        }
        Ok(json!({"capability_id":capability_id,"operation":operation,"fields":fields}))
    }
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Command {
    Ready,
    Refresh,
    Window {
        mode: WindowMode,
    },
    CaptureChoice {
        source: ContextChoice,
    },
    Capture {
        source: ContextChoice,
    },
    Discard,
    Interact {
        mode: InteractionMode,
        text: String,
        context_id: String,
    },
    Act {
        capability_id: String,
        form: ActForm,
    },
    Inspect {
        task_id: String,
    },
    Review {
        task_id: String,
        operation: ControlOperation,
    },
    Confirm {
        review_id: String,
        accept: bool,
    },
    Preview {
        task_id: String,
    },
    Apply {
        preview_id: String,
        destination: Destination,
    },
    VoiceStart {
        context_id: String,
    },
    VoiceStop,
    VoiceCancel,
    Shortcut {
        accelerator: String,
    },
}
#[derive(Deserialize, Serialize)]
pub enum InteractionMode {
    Ask,
    Dictate,
    Edit,
}
#[derive(Deserialize, Serialize, Clone, Copy)]
#[serde(rename_all = "lowercase")]
pub enum ControlOperation {
    Approve,
    Deny,
    Cancel,
}
#[derive(Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Destination {
    Surface,
    Focused,
    Clipboard,
}

pub fn bound(value: &str, limit: usize) -> Result<(), String> {
    if value.chars().count() > limit || value.contains('\0') {
        Err("input exceeds boundary".into())
    } else {
        Ok(())
    }
}
pub fn relative_path(value: &str) -> Result<(), String> {
    bound(value, 200)?;
    if value.is_empty()
        || value.contains([':', '\\'])
        || value.starts_with('/')
        || value
            .split('/')
            .any(|p| p.is_empty() || matches!(p, ".." | "."))
    {
        return Err("relative workspace path required".into());
    }
    Ok(())
}

#[derive(Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct TaskView {
    pub task_id: String,
    pub state: String,
    #[serde(default)]
    pub description: String,
    pub target: String,
    #[serde(default)]
    pub blocker: Option<String>,
    #[serde(default)]
    pub actions: Vec<String>,
    #[serde(default)]
    pub generation: u32,
    #[serde(default)]
    pub evidence_ids: Vec<String>,
    #[serde(default)]
    pub response: Option<String>,
    #[serde(default)]
    pub response_status: Option<String>,
    #[serde(default)]
    pub value: Option<String>,
    #[serde(default)]
    pub epistemic: Option<String>,
    #[serde(default)]
    pub progress: Option<Progress>,
    #[serde(default)]
    pub mode: String,
    #[serde(default)]
    pub response_truncated: bool,
    #[serde(default)]
    pub source_event_ids: Vec<String>,
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
pub struct Progress {
    pub fraction: f64,
    pub step: String,
    pub status: String,
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
pub struct ContextView {
    pub id: String,
    pub source: String,
    pub timestamp: f64,
    #[serde(default)]
    pub expires_at: Option<f64>,
    pub scope: String,
    pub provenance: String,
    pub permission: String,
    pub freshness: String,
    pub text: Option<String>,
    pub retained: bool,
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
pub struct Choice {
    pub id: String,
    pub name: String,
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
pub struct CapabilityView {
    pub id: String,
    pub node: String,
    pub kind: String,
    pub label: String,
    pub summary: String,
    pub risk: String,
    #[serde(default)]
    pub permissions: Vec<String>,
    pub operations: Vec<String>,
    pub programs: Vec<Choice>,
    pub applications: Vec<Choice>,
}
#[derive(Clone, Serialize, Deserialize, PartialEq)]
pub struct PreviewView {
    pub preview_id: String,
    pub before: Option<String>,
    pub after: String,
    pub epistemic: String,
    pub expires: f64,
    pub destinations: Vec<String>,
    #[serde(default)]
    pub focused_before: Option<String>,
    #[serde(default)]
    pub focused_after: Option<String>,
    #[serde(default)]
    pub mode: String,
}
#[derive(Clone, Serialize, PartialEq)]
pub struct ReviewView {
    pub review_id: String,
    pub task_id: String,
    pub operation: String,
    pub description: String,
    pub target: String,
    pub capability: String,
    pub reason: String,
    pub consequence: String,
    pub policy_reason: String,
    pub evidence_state: String,
    pub review: String,
    pub expires_at_ms: u64,
}
#[derive(Clone, Serialize, Default, PartialEq)]
pub struct ExpressionReadback {
    pub epoch: String,
    pub generation: u64,
    pub observed_at_ms: u64,
    pub voice_observed_at_ms: u64,
    pub tasks_observed_at_ms: u64,
    pub current_observed_at_ms: u64,
}
#[derive(Clone, Serialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum FeedbackKind {
    Blocked,
    Denied,
    Unknown,
    Rejected,
}
#[derive(Clone, Serialize, PartialEq)]
pub struct RequestFeedback {
    pub kind: FeedbackKind,
    pub message: String,
    pub observed_at_ms: u64,
}
#[derive(Clone, Serialize, Default, PartialEq)]
pub struct View {
    pub expression: ExpressionReadback,
    pub link: String,
    pub orb: String,
    pub window: WindowMode,
    pub window_revision: u64,
    pub tasks: Vec<TaskView>,
    pub capabilities: Vec<CapabilityView>,
    pub context: Option<ContextView>,
    pub preview: Option<PreviewView>,
    pub review: Option<ReviewView>,
    pub current: Option<TaskView>,
    pub message: Option<String>,
    pub feedback: Option<RequestFeedback>,
    pub voice: String,
    pub shortcut: String,
    pub observed_at_ms: u64,
    pub reference: bool,
}
pub fn orb(link: &str, task: Option<&TaskView>, voice: &str) -> String {
    if link != "online" {
        return "unavailable".into();
    }
    if matches!(voice, "listening" | "speaking") {
        return voice.into();
    }
    match task.map(|t| t.state.as_str()) {
        Some("planned") => "waiting",
        Some("executing" | "awaiting_result" | "verifying" | "result_received") => "thinking",
        Some("failed" | "blocked" | "unknown") => "error",
        Some(_) => "attentive",
        None => "idle",
    }
    .into()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn malformed_frontend_never_becomes_native_authority() {
        for v in [
            json!({"kind":"execute","command":"whoami"}),
            json!({"kind":"confirm","review_id":"x","accept":true,"private_key":"x"}),
            json!({"kind":"interact","mode":"Act","text":"{}","context_id":""}),
        ] {
            assert!(serde_json::from_value::<Command>(v).is_err());
        }
        let form = ActForm::ReadFile {
            path: "C:/private.txt".into(),
        };
        assert!(form.core_payload("cap").is_err());
        assert!(
            ActForm::ReadFile {
                path: "../secret".into()
            }
            .core_payload("cap")
            .is_err()
        );
        assert!(
            ActForm::WriteFile {
                path: "a.txt".into(),
                text: "x".repeat(4097)
            }
            .core_payload("cap")
            .is_err()
        );
    }
    #[test]
    fn state_mapping_is_truthful() {
        assert_eq!(orb("offline", None, "listening"), "unavailable");
        assert_eq!(
            orb(
                "online",
                Some(&TaskView {
                    state: "unknown".into(),
                    ..Default::default()
                }),
                "idle"
            ),
            "error"
        );
        assert_eq!(
            orb(
                "online",
                Some(&TaskView {
                    state: "planned".into(),
                    ..Default::default()
                }),
                "idle"
            ),
            "waiting"
        );
    }
}
