#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]
mod core;
mod preferences;
mod presence;
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
    menu::{CheckMenuItem, Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};
use windows_sys::Win32::UI::WindowsAndMessaging::{
    IDYES, MB_ICONQUESTION, MB_ICONWARNING, MB_OK, MB_YESNO, MessageBoxW,
};

struct Native {
    isolated_preferences: bool,
    preferences_lock: Mutex<()>,
    presence: bool,
    bridge: Arc<Bridge>,
    shortcut: Mutex<Option<Shortcut>>,
    ready: AtomicBool,
    stop: AtomicBool,
}
fn save_preferences(app: &tauri::AppHandle, state: &Native) -> Result<(), String> {
    if state.isolated_preferences || state.bridge.client().is_ok_and(|client| client.reference) {
        return Ok(());
    }
    let _guard = state
        .preferences_lock
        .lock()
        .map_err(|_| "Desktop preferences unavailable")?;
    let view = state.bridge.view();
    preferences::Preferences {
        theme: view.theme,
        shortcut: view.shortcut,
        shortcut_enabled: view.shortcut_enabled,
    }
    .write(
        &app.path()
            .app_config_dir()
            .map_err(|_| "Desktop preferences directory unavailable")?
            .join("desktop.json"),
    )
}
fn emit(app: &tauri::AppHandle, state: &Native) {
    let view = state.bridge.view();
    let _ = app.emit_to("main", "desktop-state", &view);
}
// Only operational metadata crosses into the Companion WebView.
fn companion_view(mut view: View) -> View {
    fn status(task: TaskView) -> TaskView {
        TaskView {
            state: task.state,
            actions: task.actions,
            ..Default::default()
        }
    }
    view.tasks = view.tasks.into_iter().map(status).collect();
    view.current = view.current.map(status);
    view.capabilities.clear();
    view.context = None;
    view.preview = None;
    view.review = None;
    view.message = None;
    view.feedback = None;
    view
}

#[derive(serde::Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum SurfaceCommand {
    Ready,
    CompanionMenu {},
    OpenWorkspace,
    OpenActivity,
    HideWorkspace,
    ShowCompanion,
    HideCompanion,
    ShortcutEnabled { enabled: bool },
    CancelListening,
    Theme { theme: ThemeChoice },
    Quit,
}
#[tauri::command]
async fn surface_command(
    app: tauri::AppHandle,
    window: tauri::WebviewWindow,
    state: tauri::State<'_, Native>,
    request: SurfaceCommand,
) -> Result<View, String> {
    if !matches!(window.label(), "main" | "companion") {
        return Err("unknown surface".into());
    }
    let saves = matches!(
        request,
        SurfaceCommand::Theme { .. } | SurfaceCommand::ShortcutEnabled { .. }
    );
    match request {
        SurfaceCommand::Ready => {}
        SurfaceCommand::CompanionMenu {} => {
            if window.label() != "companion" {
                return Err("Companion menu belongs to Companion".into());
            }
            companion_menu(&app, &window, &state)?;
        }
        SurfaceCommand::OpenWorkspace => show_workspace(&app)?,
        SurfaceCommand::OpenActivity => {
            window_mode(&app, &state, WindowMode::Activity)?;
        }
        SurfaceCommand::HideWorkspace => {
            app.get_webview_window("main")
                .ok_or("Workspace unavailable")?
                .hide()
                .map_err(|_| "hide failed")?;
        }
        SurfaceCommand::ShowCompanion => {
            app.get_webview_window("companion")
                .ok_or("Companion unavailable")?
                .show()
                .map_err(|_| "show failed")?;
        }
        SurfaceCommand::HideCompanion => {
            app.get_webview_window("companion")
                .ok_or("Companion unavailable")?
                .hide()
                .map_err(|_| "hide failed")?;
        }
        SurfaceCommand::ShortcutEnabled { enabled } => {
            shortcut_enabled(&app, &state, enabled)?;
        }
        SurfaceCommand::CancelListening => {
            let bridge = state.bridge.clone();
            tauri::async_runtime::spawn_blocking(move || {
                bridge.execute(Command::VoiceCancel, |_| false)
            })
            .await
            .map_err(|_| "voice cancellation unavailable")??;
        }
        SurfaceCommand::Quit => {
            if window.label() != "main" {
                return Err("Quit belongs to Workspace or tray".into());
            }
            app.exit(0);
        }
        SurfaceCommand::Theme { theme } => {
            if window.label() != "main" {
                return Err("Appearance belongs to Workspace".into());
            }
            window
                .set_theme(Some(match theme {
                    ThemeChoice::Light => tauri::Theme::Light,
                    ThemeChoice::Dark => tauri::Theme::Dark,
                }))
                .map_err(|_| "native appearance unavailable")?;
            let mut view = state
                .bridge
                .view
                .lock()
                .map_err(|_| "native state unavailable")?;
            view.theme = theme;
            view.expression.generation += 1;
        }
    }
    emit(&app, &state);
    if saves {
        save_preferences(&app, &state)?;
    }
    Ok(if window.label() == "companion" {
        companion_view(state.bridge.view())
    } else {
        state.bridge.view()
    })
}
fn shortcut_enabled(app: &tauri::AppHandle, state: &Native, enabled: bool) -> Result<(), String> {
    if enabled {
        let value = state.bridge.view().shortcut;
        register_shortcut(
            app,
            state,
            if value.starts_with("Ctrl+Alt+") {
                &value
            } else {
                "Ctrl+Alt+O"
            },
        )?;
    } else {
        let mut shortcut = state.shortcut.lock().map_err(|_| "shortcut unavailable")?;
        if let Some(value) = *shortcut {
            app.global_shortcut()
                .unregister(value)
                .map_err(|_| "shortcut unregister failed")?;
        }
        *shortcut = None;
        state
            .bridge
            .view
            .lock()
            .map_err(|_| "state unavailable")?
            .shortcut_enabled = false;
    }
    Ok(())
}
fn show_workspace(app: &tauri::AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("main")
        .ok_or("Workspace unavailable")?;
    window.show().map_err(|_| "Workspace show failed")?;
    window
        .set_focus()
        .map_err(|_| "Workspace focus failed".to_owned())
}
fn companion_menu(
    app: &tauri::AppHandle,
    window: &tauri::WebviewWindow,
    state: &Native,
) -> Result<(), String> {
    let view = state.bridge.view();
    let open = MenuItem::with_id(app, "companion_open", "Open OSCAR", true, None::<&str>);
    let shortcut = CheckMenuItem::with_id(
        app,
        "companion_shortcut",
        "Global shortcut",
        true,
        view.shortcut_enabled,
        None::<&str>,
    );
    let active = matches!(view.voice.as_str(), "listening" | "processing" | "speaking");
    let voice = MenuItem::with_id(
        app,
        "companion_cancel",
        if active {
            "Cancel voice turn"
        } else {
            "Mute — unavailable"
        },
        active,
        None::<&str>,
    );
    let trigger = CheckMenuItem::with_id(
        app,
        "companion_trigger",
        "On request",
        false,
        true,
        None::<&str>,
    );
    let sentry = MenuItem::with_id(
        app,
        "companion_sentry",
        "Sentry — unavailable",
        false,
        None::<&str>,
    );
    let hide = MenuItem::with_id(app, "companion_hide", "Hide Companion", true, None::<&str>);
    let (open, shortcut, voice, trigger, sentry, hide) = (
        open.map_err(|_| "menu unavailable")?,
        shortcut.map_err(|_| "menu unavailable")?,
        voice.map_err(|_| "menu unavailable")?,
        trigger.map_err(|_| "menu unavailable")?,
        sentry.map_err(|_| "menu unavailable")?,
        hide.map_err(|_| "menu unavailable")?,
    );
    let menu = Menu::with_items(app, &[&open, &shortcut, &voice, &trigger, &sentry, &hide])
        .map_err(|_| "menu unavailable")?;
    window
        .popup_menu(&menu)
        .map_err(|_| "menu unavailable".into())
}
fn companion_menu_action(app: &tauri::AppHandle, action: &str) {
    if !matches!(
        action,
        "companion_open" | "companion_shortcut" | "companion_cancel" | "companion_hide"
    ) {
        return;
    }
    let app = app.clone();
    let action = action.to_owned();
    thread::spawn(move || {
        let state = app.state::<Native>();
        let result = match action.as_str() {
            "companion_open" => show_workspace(&app),
            "companion_shortcut" => {
                shortcut_enabled(&app, &state, !state.bridge.view().shortcut_enabled)
                    .and_then(|()| save_preferences(&app, &state))
            }
            "companion_cancel" => state
                .bridge
                .execute(Command::VoiceCancel, |_| false)
                .map(|_| ()),
            "companion_hide" => app
                .get_webview_window("companion")
                .ok_or("Companion unavailable".to_owned())
                .and_then(|window| window.hide().map_err(|_| "hide failed".to_owned())),
            _ => return,
        };
        if let Err(error) = result {
            state.bridge.fail_request(error.clone());
            let message: Vec<u16> = error.encode_utf16().chain(Some(0)).collect();
            let title: Vec<u16> = "OSCAR control unavailable"
                .encode_utf16()
                .chain(Some(0))
                .collect();
            // SAFETY: bounded native control error and NUL-terminated strings; no signing material.
            unsafe {
                MessageBoxW(
                    std::ptr::null_mut(),
                    message.as_ptr(),
                    title.as_ptr(),
                    MB_OK | MB_ICONWARNING,
                );
            }
        }
        emit(&app, &state);
    });
}
fn window_mode(app: &tauri::AppHandle, state: &Native, mode: WindowMode) -> Result<View, String> {
    let window = app
        .get_webview_window("main")
        .ok_or("desktop window unavailable")?;
    if !state.presence {
        if mode == WindowMode::Compact {
            window.hide().map_err(|_| "Workspace hide failed")?;
        } else {
            window.show().map_err(|_| "Workspace show failed")?;
            window.set_focus().map_err(|_| "Workspace focus failed")?;
        }
        let mut view = state.bridge.view.lock().map_err(|_| "state unavailable")?;
        view.window = mode;
        view.window_revision += 1;
        view.expression.generation += 1;
        drop(view);
        emit(app, state);
        return Ok(state.bridge.view());
    }
    let (width, height) = match mode {
        WindowMode::Compact if state.presence => presence::COMPACT,
        WindowMode::Interaction if state.presence => presence::INTERACTION,
        WindowMode::Compact => (300., 126.),
        WindowMode::Interaction => (580., 760.),
        WindowMode::Approval => (620., 780.),
        WindowMode::Activity if state.presence => (620., 760.),
        WindowMode::Activity => (820., 780.),
        WindowMode::Reading => (540., 680.),
        WindowMode::Tools => (540., 720.),
        WindowMode::Actions => (540., 640.),
    };
    if state.presence {
        presence::resize(&window, (width, height), false)?;
    } else {
        window
            .set_size(tauri::LogicalSize::new(width, height))
            .map_err(|_| "native window unavailable")?;
    }
    let mut view = state
        .bridge
        .view
        .lock()
        .map_err(|_| "native state unavailable")?;
    view.window = mode;
    view.window_revision += 1;
    if state.presence {
        view.expression.generation += 1;
    }
    drop(view);
    Ok(state.bridge.view())
}
#[tauri::command]
fn presence_window(
    app: tauri::AppHandle,
    state: tauri::State<'_, Native>,
    action: presence::Action,
) -> Result<(), String> {
    if !cfg!(debug_assertions) || !state.presence {
        return Err("presence prototype is not enabled".into());
    }
    let window = app
        .get_webview_window("main")
        .ok_or("presence window unavailable")?;
    match action {
        presence::Action::Hide => window.hide().map_err(|_| "hide unavailable".into()),
        presence::Action::Pin => window
            .set_always_on_top(true)
            .map_err(|_| "pin unavailable".into()),
        presence::Action::Float => window
            .set_always_on_top(false)
            .map_err(|_| "float unavailable".into()),
        presence::Action::Edge => {
            let size = window
                .inner_size()
                .map_err(|_| "size unavailable")?
                .to_logical::<f64>(window.scale_factor().map_err(|_| "scale unavailable")?);
            presence::resize(&window, (size.width, size.height), true)
        }
    }
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
    state
        .bridge
        .view
        .lock()
        .map_err(|_| "native state unavailable")?
        .shortcut_enabled = true;
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
            state.bridge.fail_request(error);
        }
        let _ = window_mode(&app, &state, WindowMode::Interaction);
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.show();
            let _ = window.set_focus();
        }
        emit(&app, &state);
    });
}
fn tray_action(app: &tauri::AppHandle, action: &str) {
    match action {
        "reveal" => invoke_presence(app.clone()),
        "compact" if app.state::<Native>().presence => {
            let _ = window_mode(app, &app.state::<Native>(), WindowMode::Compact);
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }
            emit(app, &app.state::<Native>());
        }
        "compact" => {
            if let Some(window) = app.get_webview_window("companion") {
                let _ = window.show();
            }
        }
        "hide" => {
            let label = if app.state::<Native>().presence {
                "main"
            } else {
                "companion"
            };
            if let Some(window) = app.get_webview_window(label) {
                let _ = window.hide();
            }
        }
        "quit" => app.exit(0),
        _ => {}
    }
}

#[tauri::command]
async fn desktop_command(
    app: tauri::AppHandle,
    window: tauri::WebviewWindow,
    state: tauri::State<'_, Native>,
    request: Command,
) -> Result<View, String> {
    if window.label() != "main" {
        return Err("Workspace authority required".into());
    }
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
            state
                .bridge
                .view
                .lock()
                .map_err(|_| "native state unavailable")?
                .capture_choice = source;
            emit(&app, &state);
            return Ok(state.bridge.view());
        }
        Command::Shortcut { accelerator } => {
            let result = register_shortcut(&app, &state, &accelerator);
            emit(&app, &state);
            if result.is_ok() {
                save_preferences(&app, &state)?;
            }
            return result;
        }
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
        Err(error) => state.bridge.fail_request(error),
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
        return Err(format!(
            "reference UIA readback not verified: state={}, evidence={}",
            applied.state,
            applied.evidence_ids.len()
        ));
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
    let check = cfg!(debug_assertions) && std::env::args().any(|a| a == "--reference-check");
    let bootstrap_stdin = std::env::args().any(|a| a == "--bootstrap-stdin");
    let baseline = if cfg!(debug_assertions) {
        std::env::args().find(|a| {
            matches!(
                a.as_str(),
                "--baseline-menu" | "--baseline-dialog" | "--lifecycle-check"
            )
        })
    } else {
        None
    };
    let interaction = std::env::args().any(|a| a == "--interaction");
    let presence = cfg!(debug_assertions) && std::env::args().any(|a| a == "--living-presence");
    let bridge = Arc::new(Bridge::new());
    let native = Native {
        isolated_preferences: check
            || baseline.is_some()
            || presence
            || (cfg!(debug_assertions) && std::env::args().any(|a| a == "--isolated-preferences")),
        preferences_lock: Mutex::new(()),
        presence,
        bridge: bridge.clone(),
        shortcut: Mutex::new(None),
        ready: AtomicBool::new(false),
        stop: AtomicBool::new(false),
    };
    tauri::Builder::default().manage(native)
        .plugin(tauri_plugin_global_shortcut::Builder::new().with_handler(|app,_,event|{
            if event.state==ShortcutState::Pressed{invoke_presence(app.clone());}
        }).build())
        .invoke_handler(tauri::generate_handler![desktop_command, presence_window, surface_command])
        .setup(move|app| {
            let state=app.state::<Native>();
            let saved=if state.isolated_preferences {preferences::Preferences::default()} else {
                let path=app.path().app_config_dir()?.join("desktop.json");
                match preferences::Preferences::read(&path) {Ok(saved)=>saved,Err(error)=>{state.bridge.fail(error);preferences::Preferences::default()}}
            };
            {let mut view=state.bridge.view.lock().map_err(|_| "native state unavailable")?;view.theme=saved.theme;view.shortcut=saved.shortcut.clone();}
            let mut config=app.config().app.windows[0].clone();
            if presence { config.url=tauri::WebviewUrl::External("http://127.0.0.1:1420/?living".parse()?); }
            let mut builder=tauri::WebviewWindowBuilder::from_config(app, &config)?;
            if presence {
                builder=builder.transparent(true).shadow(false).inner_size(132.,148.).min_inner_size(132.,148.).resizable(false);
            }
            let window=builder
                .on_navigation(|url| url.scheme()=="tauri" || (url.scheme()=="http" && (url.host_str()==Some("tauri.localhost") ||
                    (cfg!(debug_assertions)&&url.host_str()==Some("127.0.0.1")&&url.port()==Some(1420)))))
                .build()?;
            if presence { presence::resize(&window,presence::COMPACT,true)?; }
            if !presence { window.set_theme(Some(match saved.theme {ThemeChoice::Light=>tauri::Theme::Light,ThemeChoice::Dark=>tauri::Theme::Dark}))?; }
            if !presence {
                let companion_config=&app.config().app.windows[1];
                let companion=tauri::WebviewWindowBuilder::from_config(app,companion_config)?
                    .on_navigation(|url| url.scheme()=="tauri" || (url.scheme()=="http" && (url.host_str()==Some("tauri.localhost") ||
                        (cfg!(debug_assertions)&&url.host_str()==Some("127.0.0.1")&&url.port()==Some(1420)))))
                    .build()?;
                presence::resize(&companion,(148.,164.),true)?;
                companion.on_menu_event(|window,event|{if window.label()=="companion" {companion_menu_action(window.app_handle(),event.id.as_ref());}});
            }
            let reveal=MenuItem::with_id(app,"reveal","Open OSCAR",true,None::<&str>)?;
            let compact=MenuItem::with_id(app,"compact","Show Companion",true,None::<&str>)?;
            let hide=MenuItem::with_id(app,"hide","Hide Companion",true,None::<&str>)?;
            let quit=MenuItem::with_id(app,"quit","Quit",true,None::<&str>)?;
            let menu=Menu::with_items(app,&[&reveal,&compact,&hide,&quit])?;
            TrayIconBuilder::new().icon(app.default_window_icon().ok_or("canonical tray icon missing")?.clone())
                .tooltip("OSCAR").menu(&menu).show_menu_on_left_click(false)
                .on_tray_icon_event(|tray,event|{if matches!(event,TrayIconEvent::Click{button:MouseButton::Left,button_state:MouseButtonState::Up,..}){invoke_presence(tray.app_handle().clone());}})
                .on_menu_event(|app,event|tray_action(app,event.id.as_ref())).build(app)?;
            let state=app.state::<Native>();
            if saved.shortcut_enabled && let Err(error)=register_shortcut(app.handle(),&state,&saved.shortcut){state.bridge.fail(error);}
            let handle=app.handle().clone();
            thread::spawn(move|| {
                if let Some(baseline)=baseline {
                    let state=handle.state::<Native>();
                    for _ in 0..100 {if state.ready.load(Ordering::Acquire){break;}thread::sleep(Duration::from_millis(100));}
                    if baseline=="--baseline-menu" {
                        if let Some(window)=handle.get_webview_window("main"){let _=window.popup_menu_at(&menu,tauri::LogicalPosition::new(30.,30.));}
                    }else if baseline=="--baseline-dialog" {
                        owner_review(&handle,&ReviewView {review_id:"synthetic-unusable".into(),task_id:"synthetic-unusable".into(),operation:"approve".into(),description:"Synthetic capture only".into(),target:"fixture-worker".into(),capability:"machine.files.write".into(),reason:"Development baseline capture".into(),consequence:"No action or signature is possible in this capture mode".into(),policy_reason:"Native presentation only; no Core or credentials".into(),evidence_state:"SIMULATED / unexecuted".into(),review:"notes/reference.txt\nSynthetic content only. This dialog cannot authorize work.".into(),expires_at_ms:0});
                    }else {
                        let window=handle.get_webview_window("main").expect("owned lifecycle window");
                        window.close().expect("close request");thread::sleep(Duration::from_millis(700));
                        assert!(!window.is_visible().expect("hidden"));
                        invoke_presence(handle.clone());thread::sleep(Duration::from_millis(700));
                        assert!(window.is_visible().expect("revealed"));
                        assert!(state.bridge.view().window==WindowMode::Interaction);
                        assert!(state.bridge.client().is_err());
                        let companion=handle.get_webview_window("companion").expect("owned Companion");
                        tray_action(&handle,"hide");
                        assert!(!companion.is_visible().expect("Companion hidden"));
                        tray_action(&handle,"compact");
                        assert!(companion.is_visible().expect("Companion shown"));
                        println!("LIFECYCLE_REFERENCE_PASS: uncommissioned, close/hide, tray reveal/hide/show, explicit quit");
                        tray_action(&handle,"quit");
                    }
                    return;
                }
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
                let client=if bootstrap_stdin {match start(){Ok(c)=>Some(c),Err(e)=>{state.bridge.fail(e);emit(&handle,&state);None}}}else{None};
                *state.bridge.client.lock().unwrap_or_else(|p|p.into_inner())=client.clone();
                let mut emitted=View::default();
                let mut shown=false;
                while !state.stop.load(Ordering::Acquire) {
                    if interaction && !shown && state.ready.load(Ordering::Acquire) {
                        let _=window_mode(&handle,&state,WindowMode::Interaction);shown=true;
                    }
                    if check && state.ready.load(Ordering::Acquire) {
                        let Some(client)=&client else{handle.exit(1);return;};
                        if !client.reference {handle.exit(1);return;}
                        if let Err(error)=reference_check(handle.clone(),client.clone()){eprintln!("reference failed: {error}");handle.exit(1);}
                        return;
                    }
                    let view=if client.is_some(){match state.bridge.refresh(){Ok(v)=>v,Err(e)=>state.bridge.fail(e)}}else{
                        if state.presence { let mut view=state.bridge.view.lock().unwrap_or_else(|p|p.into_inner());view.expression.generation+=1;view.expression.observed_at_ms=core::now_ms(); }
                        state.bridge.view()
                    };
                    if view!=emitted {emit(&handle,&state);emitted=view;}
                    thread::sleep(Duration::from_secs(2));
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!()).expect("native OSCAR shell")
        .run(|app,event|match event {
            tauri::RunEvent::WindowEvent{label,event:tauri::WindowEvent::CloseRequested{api,..},..}=>{
                api.prevent_close();if let Some(window)=app.get_webview_window(&label){let _=window.hide();}
            },
            tauri::RunEvent::ExitRequested{code:None,api,..}=>api.prevent_exit(),
            tauri::RunEvent::Exit=>{let _=app.global_shortcut().unregister_all();app.state::<Native>().stop.store(true,Ordering::Release);},
            _=>{}
        });
}

#[cfg(test)]
mod native_tests {
    use super::*;
    #[test]
    fn companion_never_receives_private_or_signing_material() {
        let mut view = View::default();
        view.current = Some(TaskView {
            description: "private request".into(),
            response: Some("private response".into()),
            value: Some("private value".into()),
            state: "planned".into(),
            actions: vec!["approve".into()],
            ..Default::default()
        });
        view.tasks = vec![view.current.clone().unwrap()];
        view.message = Some("private preview".into());
        let redacted = companion_view(view);
        let json = serde_json::to_string(&redacted).unwrap();
        assert!(!json.contains("private"));
        assert_eq!(redacted.current.unwrap().actions, vec!["approve"]);
        let capability = include_str!("../capabilities/companion-ui.json");
        assert!(!capability.contains("allow-desktop-command"));
        assert!(!capability.contains("allow-presence-window"));
        assert!(!capability.contains("core:event:"));
        assert!(
            serde_json::from_value::<SurfaceCommand>(
                serde_json::json!({"kind":"confirm","accept":true})
            )
            .is_err()
        );
    }
    #[test]
    fn companion_menu_request_cannot_supply_actions_or_signing_material() {
        assert!(
            serde_json::from_value::<SurfaceCommand>(serde_json::json!({"kind":"companion_menu"}))
                .is_ok()
        );
        for field in ["action", "review_id", "signature", "command"] {
            let request = serde_json::json!({"kind":"companion_menu",(field):"approve"});
            assert!(serde_json::from_value::<SurfaceCommand>(request).is_err());
        }
    }
    #[test]
    fn invocation_and_capabilities_are_bounded() {
        assert!(
            serde_json::from_value::<SurfaceCommand>(
                serde_json::json!({"kind":"theme","theme":"dark"})
            )
            .is_ok()
        );
        assert!(
            serde_json::from_value::<SurfaceCommand>(
                serde_json::json!({"kind":"theme","theme":"execute"})
            )
            .is_err()
        );
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
