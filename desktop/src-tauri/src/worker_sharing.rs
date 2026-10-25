//! Local process supervision; the enrolled Core still owns every execution grant.
use crate::remote::Connection;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{
    io::{Read, Write},
    os::windows::{io::AsRawHandle, process::CommandExt},
    path::{Path, PathBuf},
    process::{Child, ChildStdin, Command, Stdio},
    sync::{Arc, Mutex},
    thread,
    time::{Duration, Instant},
};
use windows_sys::Win32::{
    Foundation::{CloseHandle, HANDLE, INVALID_HANDLE_VALUE},
    System::{
        Diagnostics::ToolHelp::{
            CreateToolhelp32Snapshot, TH32CS_SNAPTHREAD, THREADENTRY32, Thread32First, Thread32Next,
        },
        JobObjects::{
            AssignProcessToJobObject, CreateJobObjectW, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
            JOBOBJECT_EXTENDED_LIMIT_INFORMATION, JobObjectExtendedLimitInformation,
            SetInformationJobObject,
        },
        Threading::{OpenThread, ResumeThread, THREAD_SUSPEND_RESUME},
    },
};

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Config {
    pub python: String,
    pub workspace: String,
    pub capabilities: Vec<String>,
    pub trusted_host_execution: bool,
    pub allowed_executables: Vec<String>,
    pub desktop_app_ids: Vec<String>,
}

pub fn permissions(capability: &str) -> Option<&'static [&'static str]> {
    Some(match capability {
        "machine.files.read"
        | "machine.files.list"
        | "machine.files.search"
        | "machine.executables" => &["files:read"],
        "machine.files.write" => &["files:write"],
        "machine.desktop" | "machine.apps" => &["machine:host", "desktop:control"],
        "machine.clipboard" => &["machine:host", "desktop:control", "desktop:clipboard"],
        "machine.visual" => &["machine:host", "desktop:control", "desktop:capture"],
        "machine.controls" => &[
            "machine:host",
            "desktop:control",
            "desktop:capture",
            "screen:retain",
        ],
        "machine.screen" => &[
            "machine:host",
            "desktop:control",
            "desktop:capture",
            "screen:retain",
            "files:write",
        ],
        "machine.browser" => &["machine:host", "browser:control"],
        "machine.command"
        | "machine.git"
        | "machine.repository"
        | "machine.powershell"
        | "machine.agent.codex"
        | "machine.agent.claude-code"
        | "machine.agent.opencode"
        | "machine.agent.gemini-cli" => &["machine:host"],
        _ => return None,
    })
}

fn existing(value: &str, directory: bool) -> Result<PathBuf, String> {
    if value.is_empty() || value.len() > 2048 || value.chars().any(char::is_control) {
        return Err("Existing absolute local paths required".into());
    }
    let path = Path::new(value);
    if !path.is_absolute() || (directory && !path.is_dir()) || (!directory && !path.is_file()) {
        return Err("Existing absolute local paths required".into());
    }
    let resolved = path
        .canonicalize()
        .map_err(|_| "Local path cannot be resolved")?;
    let value = resolved.to_str().ok_or("Local path is not valid text")?;
    // Rust canonicalization adds a verbatim prefix; scoped files deliberately accept local drive paths.
    let value = value.strip_prefix(r"\\?\").unwrap_or(value);
    if value.as_bytes().get(1) != Some(&b':') || value.as_bytes().get(2) != Some(&b'\\') {
        return Err("A local Windows drive path is required".into());
    }
    Ok(PathBuf::from(value))
}

impl Config {
    pub fn scope(&self, connection: &Connection, data: &Path) -> Result<Value, String> {
        let session = connection
            .session
            .as_ref()
            .ok_or("Enroll this Desktop first")?;
        let workspace_id = connection
            .workspace
            .as_ref()
            .filter(|v| !v.is_empty() && v.len() <= 128)
            .ok_or("Reconnect with a new invitation to bind the execution workspace")?;
        if !session.scopes.iter().any(|s| s == "execute") {
            return Err("This enrollment does not permit Desktop execution".into());
        }
        let workspace = existing(&self.workspace, true)?;
        let python = existing(&self.python, false)?;
        if !python
            .file_name()
            .and_then(|v| v.to_str())
            .is_some_and(|v| matches!(v.to_lowercase().as_str(), "python.exe" | "python3.exe"))
        {
            return Err("Select an installed Python executable with OSCAR installed".into());
        }
        let data = existing(data.to_str().ok_or("Invalid native execution path")?, true)?;
        if data.starts_with(&workspace) {
            return Err(
                "Shared workspace must exclude OSCAR's private configuration and journal".into(),
            );
        }
        if self.capabilities.is_empty()
            || self.capabilities.len() > 20
            || self.allowed_executables.len() > 16
            || self.desktop_app_ids.len() > 32
        {
            return Err("Choose a bounded explicit execution scope".into());
        }
        let mut seen = std::collections::HashSet::new();
        for capability in &self.capabilities {
            let required = permissions(capability).ok_or("Unsupported Desktop capability")?;
            if !seen.insert(capability)
                || !required
                    .iter()
                    .all(|p| session.scopes.iter().any(|s| s == p))
            {
                return Err("Selected capability exceeds this enrollment".into());
            }
            if required.contains(&"machine:host") && !self.trusted_host_execution {
                return Err("Host execution needs an explicit local grant".into());
            }
        }
        let executables = self
            .allowed_executables
            .iter()
            .map(|v| existing(v, false))
            .collect::<Result<Vec<_>, _>>()?;
        if self.capabilities.iter().any(|v| v == "machine.command") && executables.is_empty() {
            return Err("Commands need an exact executable allowlist".into());
        }
        if self.desktop_app_ids.iter().any(|v| {
            v.is_empty()
                || v.len() > 80
                || !v
                    .chars()
                    .all(|c| c.is_ascii_alphanumeric() || "-_.".contains(c))
        }) {
            return Err("Use exact registered application IDs".into());
        }
        let has = |id: &str| self.capabilities.iter().any(|v| v == id);
        let scope = json!({"workspace":workspace,"workspace_id":workspace_id,
            "journal":data.join("worker-execution.sqlite"),"capabilities":self.capabilities,
            "trusted_host_execution":self.trusted_host_execution,"allowed_executables":executables,
            "desktop":has("machine.desktop")||has("machine.apps")||has("machine.clipboard")||has("machine.screen")||has("machine.visual")||has("machine.controls"),
            "browser":has("machine.browser"),"desktop_app_ids":self.desktop_app_ids,
            "profile_root":if has("machine.browser") {Some(data.join("worker-browser-profiles"))}else{None}});
        if serde_json::to_vec(&scope)
            .map_err(|_| "Invalid local scope")?
            .len()
            > 16000
        {
            return Err("Local scope exceeds the native review boundary".into());
        }
        Ok(scope)
    }
}

struct Job(HANDLE);
// SAFETY: the owned kernel job handle may be closed or used from any thread.
unsafe impl Send for Job {}
impl Job {
    fn attach(child: &Child) -> Result<Self, String> {
        // SAFETY: a fresh job owns the initialized limits; child is a live process handle.
        unsafe {
            let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
            if handle.is_null() {
                return Err("Desktop execution containment unavailable".into());
            }
            let job = Self(handle);
            let mut limits: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            if SetInformationJobObject(
                handle,
                JobObjectExtendedLimitInformation,
                &limits as *const _ as _,
                std::mem::size_of_val(&limits) as u32,
            ) == 0
                || AssignProcessToJobObject(handle, child.as_raw_handle() as _) == 0
            {
                return Err("Desktop execution containment unavailable".into());
            }
            Ok(job)
        }
    }
}
impl Drop for Job {
    fn drop(&mut self) {
        unsafe {
            CloseHandle(self.0);
        }
    }
}

fn contained_spawn(command: &mut Command) -> Result<(Child, Job), String> {
    // Suspend before the first instruction; even runtime imports cannot spawn outside the job.
    command.creation_flags(0x08000000 | 0x00000004);
    let mut child = command
        .spawn()
        .map_err(|_| "Installed Python runtime unavailable")?;
    let result = Job::attach(&child).and_then(|job| resume_child(&child).map(|()| job));
    match result {
        Ok(job) => Ok((child, job)),
        Err(error) => {
            let _ = child.kill();
            let _ = child.wait();
            Err(error)
        }
    }
}

fn resume_child(child: &Child) -> Result<(), String> {
    // SAFETY: only the retained, just-created suspended child's thread may be resumed.
    unsafe {
        let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        if snapshot == INVALID_HANDLE_VALUE {
            return Err("Native suspended process unavailable".into());
        }
        let mut entry: THREADENTRY32 = std::mem::zeroed();
        entry.dwSize = std::mem::size_of::<THREADENTRY32>() as u32;
        let mut found = Thread32First(snapshot, &mut entry);
        let mut resumed = false;
        while found != 0 {
            if entry.th32OwnerProcessID == child.id() {
                let thread = OpenThread(THREAD_SUSPEND_RESUME, 0, entry.th32ThreadID);
                if !thread.is_null() {
                    resumed = ResumeThread(thread) != u32::MAX;
                    CloseHandle(thread);
                }
                break;
            }
            found = Thread32Next(snapshot, &mut entry);
        }
        CloseHandle(snapshot);
        if resumed {
            Ok(())
        } else {
            Err("Native suspended process could not resume".into())
        }
    }
}

#[derive(Clone, Serialize, Default, PartialEq)]
pub struct WorkerView {
    pub status: String,
    pub workspace: String,
    pub capabilities: Vec<String>,
    pub message: String,
}
struct Running {
    child: Child,
    input: Option<ChildStdin>,
    job: Option<Job>,
    status: Arc<Mutex<String>>,
    started: Instant,
}
impl Running {
    fn stop(&mut self) {
        if let Some(mut input) = self.input.take() {
            let _ = input.write_all(b"stop\n");
            let _ = input.flush();
        }
        let until = Instant::now() + Duration::from_secs(3);
        while Instant::now() < until {
            if self.child.try_wait().ok().flatten().is_some() {
                break;
            }
            thread::sleep(Duration::from_millis(50));
        }
        self.job.take();
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}
impl Drop for Running {
    fn drop(&mut self) {
        self.stop();
    }
}

#[derive(Default)]
pub struct Sharing {
    running: Option<Running>,
    view: WorkerView,
}
impl Sharing {
    pub fn snapshot(&mut self) -> WorkerView {
        if let Some(running) = &mut self.running {
            if let Ok(status) = running.status.lock() {
                self.view.status = status.clone();
            }
            if running.child.try_wait().ok().flatten().is_some() {
                self.view.status = if self.view.status == "stopped" {
                    "stopped"
                } else {
                    "unavailable"
                }
                .into();
                self.view.message = "Execution stopped. Inspect runtime installation and enrollment before restarting.".into();
                self.running.take();
            } else if self.view.status == "protocol_error"
                || (self.view.status == "starting"
                    && running.started.elapsed() > Duration::from_secs(15))
            {
                self.stop();
                self.view.status = "unavailable".into();
                self.view.message =
                    "The installed runtime did not provide a valid bounded execution status."
                        .into();
            }
        }
        if self.view.status.is_empty() {
            self.view.status = "stopped".into();
        }
        self.view.clone()
    }
    pub fn start(&mut self, config: Config, scope: Value, connection: &Path) -> Result<(), String> {
        self.snapshot();
        if self.running.is_some() {
            return Err("Stop Desktop sharing before changing its scope".into());
        }
        let mut command = child_command(&config.python, connection);
        let (mut child, job) = contained_spawn(&mut command)?;
        let mut input = child
            .stdin
            .take()
            .ok_or("Native execution input unavailable")?;
        let output = child
            .stdout
            .take()
            .ok_or("Native execution status unavailable")?;
        let status = Arc::new(Mutex::new("starting".to_owned()));
        let mut running = Running {
            child,
            input: None,
            job: Some(job),
            status: status.clone(),
            started: Instant::now(),
        };
        let mut body = serde_json::to_vec(&scope).map_err(|_| "Invalid local scope")?;
        body.push(b'\n');
        input
            .write_all(&body)
            .and_then(|()| input.flush())
            .map_err(|_| "Runtime could not accept the reviewed scope")?;
        running.input = Some(input);
        thread::spawn(move || read_status(output, status));
        self.view = WorkerView { status: "starting".into(), workspace: config.workspace,
            capabilities: config.capabilities, message: "Only installed, enrolled capabilities in this reviewed scope may run. Core authority is checked for every action.".into() };
        self.running = Some(running);
        Ok(())
    }
    pub fn stop(&mut self) {
        self.running.take();
        self.view.status = "stopped".into();
        self.view.message =
            "Local execution stopped. Uncertain actions are not automatically replayed.".into();
    }
}

fn child_command(python: &str, connection: &Path) -> Command {
    let mut command = Command::new(python);
    command
        .args(["-I", "-u", "-m", "oscar.remote_machine", "--connection"])
        .arg(connection)
        .arg("--scope-stdin")
        .creation_flags(0x08000000)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    command
}

fn read_status(mut output: impl Read, status: Arc<Mutex<String>>) {
    loop {
        let mut line = Vec::new();
        let mut byte = [0u8; 1];
        loop {
            match output.read(&mut byte) {
                Ok(0) | Err(_) => return,
                Ok(_) if byte[0] == b'\n' => break,
                Ok(_) => line.push(byte[0]),
            }
            if line.len() > 512 {
                if let Ok(mut state) = status.lock() {
                    *state = "protocol_error".into();
                }
                return;
            }
        }
        let value: Value = match serde_json::from_slice(&line) {
            Ok(v) => v,
            Err(_) => {
                if let Ok(mut state) = status.lock() {
                    *state = "protocol_error".into();
                }
                return;
            }
        };
        let next = value["status"].as_str().filter(|v| {
            matches!(
                *v,
                "offline"
                    | "online"
                    | "degraded"
                    | "revoked_or_expired"
                    | "stopped"
                    | "unavailable"
            )
        });
        if let Some(next) = next {
            if let Ok(mut state) = status.lock() {
                *state = next.into();
            }
        } else {
            if let Ok(mut state) = status.lock() {
                *state = "protocol_error".into();
            }
            return;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bounded_child_status_never_exposes_arbitrary_output() {
        let state = Arc::new(Mutex::new("starting".into()));
        read_status(
            &b"{\"status\":\"online\"}\n{\"status\":\"degraded\"}\n"[..],
            state.clone(),
        );
        assert_eq!(*state.lock().unwrap(), "degraded");
        read_status(&b"private process output\n"[..], state.clone());
        assert_eq!(*state.lock().unwrap(), "protocol_error");
        read_status(&[b'x'; 513][..], state.clone());
        assert_eq!(*state.lock().unwrap(), "protocol_error");
    }
    #[test]
    fn old_connections_cannot_invent_a_workspace_or_execution_scope() {
        let connection: Connection = serde_json::from_value(
            json!({"url":"https://core.example","installation_id":"synthetic","session":null}),
        )
        .unwrap();
        assert!(connection.workspace.is_none());
        let config = Config {
            python: "python.exe".into(),
            workspace: ".".into(),
            capabilities: vec!["machine.files.read".into()],
            trusted_host_execution: false,
            allowed_executables: vec![],
            desktop_app_ids: vec![],
        };
        assert!(config.scope(&connection, Path::new(".")).is_err());
        assert!(permissions("machine.unknown").is_none());
        assert!(
            permissions("machine.controls")
                .unwrap()
                .contains(&"screen:retain")
        );
        assert!(
            !permissions("machine.controls")
                .unwrap()
                .contains(&"files:write")
        );
        assert_eq!(
            permissions("machine.clipboard").unwrap(),
            &["machine:host", "desktop:control", "desktop:clipboard"]
        );
        assert!(
            permissions("machine.screen")
                .unwrap()
                .contains(&"screen:retain")
        );
        assert!(
            !permissions("machine.visual")
                .unwrap()
                .contains(&"screen:retain")
        );
    }
    #[test]
    fn job_close_terminates_a_real_synthetic_child() {
        let mut command = Command::new("cmd.exe");
        command
            .args(["/c", "ping -n 30 127.0.0.1 > nul"])
            .creation_flags(0x08000000)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        let (mut child, job) = contained_spawn(&mut command).unwrap();
        assert!(child.try_wait().unwrap().is_none());
        drop(job);
        let until = Instant::now() + Duration::from_secs(3);
        while child.try_wait().unwrap().is_none() && Instant::now() < until {
            thread::sleep(Duration::from_millis(20));
        }
        assert!(child.try_wait().unwrap().is_some());
    }
    #[test]
    fn reviewed_scope_is_pinned_to_the_actual_enrollment_and_private_state_stays_outside() {
        let root = std::env::temp_dir().join(format!("oscar-sharing-{}", uuid::Uuid::new_v4()));
        let workspace = root.join("artifacts");
        let private = root.join("private");
        std::fs::create_dir_all(&workspace).unwrap();
        std::fs::create_dir_all(&private).unwrap();
        let python = root.join("python.exe");
        std::fs::write(
            &python,
            b"synthetic path validation fixture; never executed",
        )
        .unwrap();
        let mut connection: Connection = serde_json::from_value(json!({"url":"https://core.example","installation_id":"synthetic","workspace":"enrolled-exact","session":{"version":2,"core_id":"core","node_id":"desktop","session_id":"session","token":"synthetic-not-a-live-credential","expires_at_ms":9999999999999u64,"scopes":["execute","files:read"]}})).unwrap();
        let mut config = Config {
            python: python.to_string_lossy().into(),
            workspace: workspace.to_string_lossy().into(),
            capabilities: vec!["machine.files.read".into()],
            trusted_host_execution: false,
            allowed_executables: vec![],
            desktop_app_ids: vec![],
        };
        let scope = config.scope(&connection, &private).unwrap();
        assert_eq!(scope["workspace_id"], "enrolled-exact");
        assert!(!scope["workspace"].as_str().unwrap().starts_with(r"\\?\"));
        assert!(
            !Path::new(scope["journal"].as_str().unwrap())
                .starts_with(workspace.canonicalize().unwrap())
        );
        assert!(config.scope(&connection, &workspace).is_err());
        config.capabilities.push("machine.files.read".into());
        assert!(config.scope(&connection, &private).is_err());
        config.capabilities = vec!["machine.command".into()];
        assert!(config.scope(&connection, &private).is_err());
        connection.workspace = None;
        assert!(config.scope(&connection, &private).is_err());
        std::fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn native_arguments_are_shell_free_and_never_include_the_credential_or_scope() {
        let command = child_command(
            "C:\\trusted\\python.exe",
            Path::new("C:\\native\\connection.dat"),
        );
        let args = command
            .get_args()
            .map(|v| v.to_str().unwrap())
            .collect::<Vec<_>>();
        assert_eq!(
            args,
            vec![
                "-I",
                "-u",
                "-m",
                "oscar.remote_machine",
                "--connection",
                "C:\\native\\connection.dat",
                "--scope-stdin"
            ]
        );
    }
    #[test]
    fn cooperative_stop_closes_the_parent_pipe_before_forced_termination() {
        let mut command = Command::new("cmd.exe");
        command
            .args(["/c", "set /p line="])
            .creation_flags(0x08000000)
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        let (mut child, job) = contained_spawn(&mut command).unwrap();
        let input = child.stdin.take();
        let mut running = Running {
            child,
            input,
            job: Some(job),
            status: Arc::new(Mutex::new("online".into())),
            started: Instant::now(),
        };
        let before = Instant::now();
        running.stop();
        assert!(before.elapsed() < Duration::from_secs(2));
        assert!(running.child.try_wait().unwrap().is_some());
    }
    #[test]
    fn closing_job_also_terminates_a_synthetic_descendant() {
        use std::io::{BufRead, BufReader};
        use windows_sys::Win32::System::Threading::{OpenProcess, WaitForSingleObject};
        let mut command = Command::new("powershell.exe");
        command.args(["-NoProfile","-NonInteractive","-Command",
            "$null=[Console]::ReadLine();$p=Start-Process -FilePath cmd.exe -ArgumentList '/c ping -n 30 127.0.0.1 > nul' -PassThru -WindowStyle Hidden;[Console]::WriteLine($p.Id);Start-Sleep -Seconds 30"])
            .creation_flags(0x08000000).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null());
        let (mut child, job) = contained_spawn(&mut command).unwrap();
        child.stdin.as_mut().unwrap().write_all(b"begin\n").unwrap();
        let mut pid = String::new();
        BufReader::new(child.stdout.take().unwrap())
            .read_line(&mut pid)
            .unwrap();
        let pid = pid.trim().parse::<u32>().unwrap();
        // SAFETY: SYNCHRONIZE only observes termination of the synthetic descendant.
        unsafe {
            let descendant = OpenProcess(0x00100000, 0, pid);
            assert!(!descendant.is_null());
            drop(job);
            assert_eq!(WaitForSingleObject(descendant, 3000), 0);
            CloseHandle(descendant);
        }
        child.wait().unwrap();
    }
}
