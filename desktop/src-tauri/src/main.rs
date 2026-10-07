#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod core;
mod protocol;
mod signing;
use crate::{
    core::{Bridge, CoreClient},
    protocol::*,
};
use base64::{Engine, engine::general_purpose::STANDARD};
use std::{
    io::{self, BufRead, Read, Write},
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
    thread,
    time::Duration,
};
use tauri::{
    Emitter, Manager,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};
use windows_sys::Win32::UI::WindowsAndMessaging::{IDYES, MB_ICONQUESTION, MB_YESNO, MessageBoxW};

struct Native {
    bridge: Arc<Bridge>,
    shortcut: Mutex<Option<Shortcut>>,
    ready: AtomicBool,
    stop: AtomicBool,
}
fn emit(app: &tauri::AppHandle, state: &Native) {
    let _ = app.emit("desktop-state", state.bridge.view());
}
fn window_mode(app: &tauri::AppHandle, state: &Native, mode: WindowMode) -> Result<View, String> {
    let window = app
        .get_webview_window("main")
        .ok_or("desktop window unavailable")?;
    let (width, height) = match mode {
        WindowMode::Compact => (300., 126.),
        WindowMode::Interaction => (580., 760.),
        WindowMode::Approval => (620., 780.),
        WindowMode::Activity => (820., 780.),
    };
    window
        .set_size(tauri::LogicalSize::new(width, height))
        .map_err(|_| "native window unavailable")?;
    state
        .bridge
        .view
        .lock()
        .map_err(|_| "native state unavailable")?
        .window = mode;
    Ok(state.bridge.view())
}
fn register_shortcut(app: &tauri::AppHandle, state: &Native, value: &str) -> Result<View, String> {
    validate_shortcut(value)?;
    let shortcut = value.parse::<Shortcut>().map_err(|_| "invalid shortcut")?;
    let mut old = state.shortcut.lock().map_err(|_| "shortcut unavailable")?;
    if old.as_ref() == Some(&shortcut) {
        return Ok(state.bridge.view());
    }
    app.global_shortcut()
        .register(shortcut)
        .map_err(|_| "Shortcut collision; existing invocation retained")?;
    if let Some(previous) = old.take() {
        let _ = app.global_shortcut().unregister(previous);
    }
    *old = Some(shortcut);
    state
        .bridge
        .view
        .lock()
        .map_err(|_| "native state unavailable")?
        .shortcut = value.into();
    Ok(state.bridge.view())
}
fn validate_shortcut(value: &str) -> Result<(), String> {
    bound(value, 60)?;
    if !value.starts_with("Ctrl+Alt+")
        || value.len() != 10
        || !value.chars().last().is_some_and(|c| c.is_ascii_uppercase())
    {
        return Err("shortcut must be Ctrl+Alt+A through Z".into());
    }
    Ok(())
}
fn owner_review(app: &tauri::AppHandle, review: &ReviewView) -> bool {
    let text = format!(
        "Operation: {}\nTarget: {}\nCapability: {}\nReason: {}\nConsequence: {}\nPolicy: {}\nState: {}\n\n{}\n\nThis decision grants no permanent authority.",
        review.operation,
        review.target,
        review.capability,
        review.reason,
        review.consequence,
        review.policy_reason,
        review.evidence_state,
        review.review
    );
    let message: Vec<u16> = text.encode_utf16().chain(Some(0)).collect();
    let title: Vec<u16> = "OSCAR owner review".encode_utf16().chain(Some(0)).collect();
    let handle = app
        .get_webview_window("main")
        .and_then(|w| w.hwnd().ok())
        .map_or(std::ptr::null_mut(), |h| h.0 as _);
    // SAFETY: fixed native dialog, owned window handle and NUL-terminated review strings.
    unsafe {
        MessageBoxW(
            handle,
            message.as_ptr(),
            title.as_ptr(),
            MB_YESNO | MB_ICONQUESTION,
        ) == IDYES
    }
}
fn invoke_presence(app: tauri::AppHandle) {
    thread::spawn(move || {
        let state = app.state::<Native>();
        let choice = *state
            .bridge
            .capture_choice
            .lock()
            .unwrap_or_else(|p| p.into_inner());
        if !matches!(choice, ContextChoice::None)
            && let Err(error) = state
                .bridge
                .execute(Command::Capture { source: choice }, |_| false)
        {
            state.bridge.fail(error);
        }
        let _ = window_mode(&app, &state, WindowMode::Interaction);
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
        }
        emit(&app, &state);
    });
}

#[tauri::command]
async fn desktop_command(
    app: tauri::AppHandle,
    state: tauri::State<'_, Native>,
    request: Command,
) -> Result<View, String> {
    match request {
        Command::Ready => {
            state.ready.store(true, Ordering::Release);
            return Ok(state.bridge.view());
        }
        Command::Window { mode } => return window_mode(&app, &state, mode),
        Command::CaptureChoice { source } => {
            *state
                .bridge
                .capture_choice
                .lock()
                .map_err(|_| "native state unavailable")? = source;
            return Ok(state.bridge.view());
        }
        Command::Shortcut { accelerator } => return register_shortcut(&app, &state, &accelerator),
        _ => {}
    }
    let bridge = state.bridge.clone();
    let handle = app.clone();
    let view = tauri::async_runtime::spawn_blocking(move || {
        bridge.execute(request, |review| owner_review(&handle, review))
    })
    .await
    .map_err(|_| "native request failed; inspect before retry")?;
    let view = match view {
        Ok(v) => v,
        Err(error) => state.bridge.fail(error),
    };
    if view.review.is_some() {
        let _ = window_mode(&app, &state, WindowMode::Approval);
    }
    emit(&app, &state);
    Ok(state.bridge.view())
}

fn reference_check(app: tauri::AppHandle, client: Arc<CoreClient>) -> Result<(), String> {
    let bridge = &app.state::<Native>().bridge;
    let initial = bridge.refresh()?;
    let continued_tasks = initial.tasks.len();
    let window = window_mode(&app, &app.state::<Native>(), WindowMode::Interaction)?;
    if window.window != WindowMode::Interaction {
        return Err("native window state failed".into());
    }
    let current_shortcut = *app
        .state::<Native>()
        .shortcut
        .lock()
        .map_err(|_| "shortcut state unavailable")?;
    let collision = if let Some(shortcut) = current_shortcut {
        app.global_shortcut().register(shortcut).is_err()
    } else {
        true
    };
    if !collision {
        return Err("shortcut collision was not rejected".into());
    }
    let proposal = bridge.execute(
        Command::Interact {
            mode: InteractionMode::Ask,
            text: "2 + 3".into(),
            context_id: String::new(),
        },
        |_| false,
    )?;
    let id = proposal
        .current
        .as_ref()
        .ok_or("reference task unavailable")?
        .task_id
        .clone();
    let review = bridge
        .execute(
            Command::Review {
                task_id: id.clone(),
                operation: ControlOperation::Approve,
            },
            |_| false,
        )?
        .review
        .ok_or("review unavailable")?;
    let done = bridge.execute(
        Command::Confirm {
            review_id: review.review_id,
            accept: true,
        },
        |_| true,
    )?;
    if done
        .current
        .as_ref()
        .is_none_or(|t| t.state != "verified" || t.value.as_deref() != Some("5"))
    {
        return Err("reference Ask verification failed".into());
    }
    let discarded = bridge.execute(Command::Discard, |_| false)?;
    if discarded.context.is_some() {
        return Err("discard failed".into());
    }
    let dictate = bridge.execute(
        Command::Interact {
            mode: InteractionMode::Dictate,
            text: "Reference dictated text".into(),
            context_id: String::new(),
        },
        |_| false,
    )?;
    let dictated = dictate.preview.ok_or("Dictate preview unavailable")?;
    bridge.execute(
        Command::Apply {
            preview_id: dictated.preview_id,
            destination: Destination::Surface,
        },
        |_| false,
    )?;
    let cap = bridge
        .refresh()?
        .capabilities
        .into_iter()
        .find(|c| c.kind == "file_write" && c.node == "tauri-reference-worker")
        .ok_or("file capability unavailable")?;
    let action = bridge
        .execute(
            Command::Act {
                capability_id: cap.id,
                form: ActForm::WriteFile {
                    path: format!("native-{}.txt", uuid::Uuid::new_v4().simple()),
                    text: "Typed Tauri action fixture".into(),
                },
            },
            |_| false,
        )?
        .current
        .ok_or("Act task unavailable")?;
    let review = client.review(&action.task_id, ControlOperation::Approve)?;
    let written: TaskView =
        serde_json::from_value(client.confirm(&review.review_id, true, |_| true)?)
            .map_err(|_| "Act response invalid")?;
    if written.state != "verified" {
        return Err("Act file readback failed".into());
    }
    let native_target = client
        .reference_target
        .clone()
        .ok_or("registered reference field required")?;
    let context = client.request(
        "capture",
        serde_json::json!({"source":"focused","target":native_target}),
    )?;
    let context: ContextView =
        serde_json::from_value(context).map_err(|_| "reference context unavailable")?;
    bridge.view.lock().map_err(|_| "state unavailable")?.context = Some(context.clone());
    let edit = bridge.execute(
        Command::Interact {
            mode: InteractionMode::Edit,
            text: "reference transform".into(),
            context_id: context.id,
        },
        |_| false,
    )?;
    let task = edit.current.ok_or("Edit task unavailable")?;
    let review = client.review(&task.task_id, ControlOperation::Approve)?;
    client.confirm(&review.review_id, true, |_| true)?;
    let preview = bridge
        .execute(
            Command::Preview {
                task_id: task.task_id,
            },
            |_| false,
        )?
        .preview
        .ok_or("preview unavailable")?;
    let apply = bridge
        .execute(
            Command::Apply {
                preview_id: preview.preview_id,
                destination: Destination::Focused,
            },
            |_| false,
        )?
        .current
        .ok_or("apply task unavailable")?;
    let review = client.review(&apply.task_id, ControlOperation::Approve)?;
    let applied: TaskView =
        serde_json::from_value(client.confirm(&review.review_id, true, |_| true)?)
            .map_err(|_| "apply response invalid")?;
    if applied.state != "verified" || applied.evidence_ids.is_empty() {
        return Err("reference UIA readback not verified".into());
    }
    let task = bridge
        .execute(
            Command::Interact {
                mode: InteractionMode::Ask,
                text: "3 + 4".into(),
                context_id: String::new(),
            },
            |_| false,
        )?
        .current
        .ok_or("cancel task unavailable")?;
    let review = client.review(&task.task_id, ControlOperation::Cancel)?;
    let cancelled: TaskView =
        serde_json::from_value(client.confirm(&review.review_id, true, |_| true)?)
            .map_err(|_| "cancel response invalid")?;
    if cancelled.state != "cancelled" {
        return Err("cancel failed".into());
    }
    bridge.refresh()?;
    let known_tasks = bridge.view().tasks.len();
    *bridge
        .client
        .lock()
        .map_err(|_| "connection state unavailable")? = None;
    if bridge.execute(Command::Refresh, |_| false).is_ok() {
        return Err("disconnected Core accepted work".into());
    }
    *bridge
        .client
        .lock()
        .map_err(|_| "connection state unavailable")? = Some(client.clone());
    if bridge.refresh()?.tasks.len() != known_tasks {
        return Err("reconnect changed shared task truth".into());
    }
    let report = serde_json::json!({"evidence":"REFERENCE_TAURI_WINDOWS_CORE", "ask":"VERIFIED",
        "native_signing":"VERIFIED_CNG_PSS", "edit_transform":"SIMULATED / REPORTED",
        "application_readback":"VERIFIED", "cancellation":"VERIFIED", "webview_ready":true,
        "owner_acceptance":"OWNER_ACCEPTANCE_NOT_RUN", "microphone":"NOT_RUN", "dictate_preview":"VERIFIED",
        "typed_act_file":"VERIFIED", "hotkey_collision_rejection":"VERIFIED", "reconnect":"VERIFIED",
        "continued_tasks_seen":continued_tasks});
    println!("{report}");
    io::stdout()
        .flush()
        .map_err(|_| "reference output unavailable")?;
    app.exit(0);
    Ok(())
}

fn main() {
    let check = std::env::args().any(|a| a == "--reference-check");
    let interaction = std::env::args().any(|a| a == "--interaction");
    let bridge = Arc::new(Bridge::new());
    let native = Native {
        bridge: bridge.clone(),
        shortcut: Mutex::new(None),
        ready: AtomicBool::new(false),
        stop: AtomicBool::new(false),
    };
    tauri::Builder::default().manage(native)
        .plugin(tauri_plugin_global_shortcut::Builder::new().with_handler(|app,_,event|{
            if event.state==ShortcutState::Pressed{invoke_presence(app.clone());}
        }).build())
        .invoke_handler(tauri::generate_handler![desktop_command])
        .setup(move|app| {
            tauri::WebviewWindowBuilder::from_config(app, &app.config().app.windows[0])?
                .on_navigation(|url| url.scheme()=="tauri" || (url.scheme()=="http" && (url.host_str()==Some("tauri.localhost") ||
                    (cfg!(debug_assertions)&&url.host_str()==Some("127.0.0.1")&&url.port()==Some(1420)))))
                .build()?;
            let reveal=MenuItem::with_id(app,"reveal","Open OSCAR",true,None::<&str>)?;
            let compact=MenuItem::with_id(app,"compact","Compact presence",true,None::<&str>)?;
            let quit=MenuItem::with_id(app,"quit","Quit",true,None::<&str>)?;
            let menu=Menu::with_items(app,&[&reveal,&compact,&quit])?;
            TrayIconBuilder::new().icon(app.default_window_icon().ok_or("canonical tray icon missing")?.clone())
                .tooltip("OSCAR").menu(&menu).show_menu_on_left_click(false)
                .on_tray_icon_event(|tray,event|{if matches!(event,TrayIconEvent::Click{button:MouseButton::Left,button_state:MouseButtonState::Up,..}){invoke_presence(tray.app_handle().clone());}})
                .on_menu_event(|app,event|match event.id.as_ref(){"reveal"=>invoke_presence(app.clone()),
                    "compact"=>{let _=window_mode(app,&app.state::<Native>(),WindowMode::Compact);},"quit"=>app.exit(0),_=>{}}).build(app)?;
            let state=app.state::<Native>();
            if let Err(error)=register_shortcut(app.handle(),&state,"Ctrl+Alt+O"){state.bridge.fail(error);}
            let handle=app.handle().clone();
            thread::spawn(move|| {
                let start=||->Result<Arc<CoreClient>,String>{
                    let signer=Arc::new(signing::Signer::new()?);
                    println!("{}",serde_json::json!({"owner_public_key":STANDARD.encode(signer.public_der()?)}));
                    io::stdout().flush().map_err(|_|"native bootstrap unavailable")?;
                    let mut line=zeroize::Zeroizing::new(String::new());io::stdin().lock().take(32769).read_line(&mut line).map_err(|_|"native bootstrap unavailable")?;
                    if line.len()>32768{return Err("bootstrap exceeds boundary".into());}
                    let bootstrap:Bootstrap=serde_json::from_str(&line).map_err(|_|"native Core enrollment required")?;
                    Ok(Arc::new(CoreClient::new(bootstrap,signer)?))
                };
                let state=handle.state::<Native>();
                let client=match start(){Ok(c)=>c,Err(e)=>{state.bridge.fail(e);emit(&handle,&state);if check{handle.exit(1);}return;}};
                *state.bridge.client.lock().unwrap_or_else(|p|p.into_inner())=Some(client.clone());
                let mut emitted=View::default();
                let mut shown=false;
                while !state.stop.load(Ordering::Acquire) {
                    if interaction && !shown && state.ready.load(Ordering::Acquire) {
                        let _=window_mode(&handle,&state,WindowMode::Interaction);shown=true;
                    }
                    if check && state.ready.load(Ordering::Acquire) {
                        if !cfg!(debug_assertions) || !client.reference {handle.exit(1);return;}
                        if let Err(error)=reference_check(handle.clone(),client.clone()){eprintln!("reference failed: {error}");handle.exit(1);}
                        return;
                    }
                    let view=match state.bridge.refresh(){Ok(v)=>v,Err(e)=>state.bridge.fail(e)};
                    if view!=emitted {emit(&handle,&state);emitted=view;}
                    thread::sleep(Duration::from_secs(2));
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!()).expect("native OSCAR shell")
        .run(|app,event|{if matches!(event,tauri::RunEvent::Exit){app.state::<Native>().stop.store(true,Ordering::Release);}});
}

#[cfg(test)]
mod native_tests {
    use super::*;
    #[test]
    fn invocation_and_capabilities_are_bounded() {
        assert!(validate_shortcut("Ctrl+Alt+O").is_ok());
        assert!(validate_shortcut("Ctrl+Alt+keylogger").is_err());
        assert!(validate_shortcut("Alt+F4").is_err());
        let capability = include_str!("../capabilities/desktop-ui.json");
        for forbidden in [
            "shell:",
            "fs:",
            "global-shortcut:",
            "core:event:allow-emit",
            "remote",
        ] {
            assert!(!capability.contains(forbidden));
        }
        let config: serde_json::Value =
            serde_json::from_str(include_str!("../tauri.conf.json")).expect("config");
        let csp = config["app"]["security"]["csp"].as_str().expect("CSP");
        assert!(!csp.contains("unsafe-inline"));
        assert!(!csp.contains("unsafe-eval"));
        assert!(csp.contains("frame-src 'none'"));
    }
}
