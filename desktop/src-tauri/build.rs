fn main() {
    tauri_build::try_build(tauri_build::Attributes::new().app_manifest(
        tauri_build::AppManifest::new().commands(&["desktop_command", "presence_window"]),
    ))
    .expect("Tauri desktop manifest");
}
