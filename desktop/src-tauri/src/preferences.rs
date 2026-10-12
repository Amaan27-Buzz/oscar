use crate::protocol::ThemeChoice;
use serde::{Deserialize, Serialize};
use std::{fs, io::Read, path::Path};

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Preferences {
    pub theme: ThemeChoice,
    pub shortcut: String,
    pub shortcut_enabled: bool,
}
impl Default for Preferences {
    fn default() -> Self {
        Self {
            theme: ThemeChoice::Light,
            shortcut: "Ctrl+Alt+O".into(),
            shortcut_enabled: true,
        }
    }
}
impl Preferences {
    pub fn read(path: &Path) -> Result<Self, String> {
        let file = match fs::File::open(path) {
            Ok(file) => file,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                return Ok(Self::default());
            }
            Err(_) => {
                return Err("Desktop preferences could not be read; defaults are active".into());
            }
        };
        let mut bytes = Vec::new();
        file.take(1025)
            .read_to_end(&mut bytes)
            .map_err(|_| "Desktop preferences unavailable")?;
        if bytes.len() > 1024 {
            return Err("Desktop preferences exceed the supported boundary".into());
        }
        let value: Self = serde_json::from_slice(&bytes)
            .map_err(|_| "Desktop preferences invalid; defaults are active")?;
        crate::validate_shortcut(&value.shortcut)?;
        Ok(value)
    }
    pub fn write(&self, path: &Path) -> Result<(), String> {
        crate::validate_shortcut(&self.shortcut)?;
        let parent = path
            .parent()
            .ok_or("Desktop preferences directory unavailable")?;
        fs::create_dir_all(parent).map_err(|_| "Desktop preferences directory unavailable")?;
        let temporary = path.with_extension(format!("{}.tmp", uuid::Uuid::new_v4().simple()));
        let bytes = serde_json::to_vec(self).map_err(|_| "Desktop preferences invalid")?;
        let result = fs::write(&temporary, bytes).and_then(|_| fs::rename(&temporary, path));
        if result.is_err() {
            let _ = fs::remove_file(&temporary);
            return Err(
                "Runtime preference changed, but saving failed; inspect before retry".into(),
            );
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bounded_preferences_replace_only_their_owned_file() {
        let directory =
            std::env::temp_dir().join(format!("oscar-preferences-{}", uuid::Uuid::new_v4()));
        let path = directory.join("desktop.json");
        let mut value = Preferences::default();
        value.write(&path).unwrap();
        value.theme = ThemeChoice::Dark;
        value.shortcut = "Ctrl+Alt+P".into();
        value.shortcut_enabled = false;
        value.write(&path).unwrap();
        let read = Preferences::read(&path).unwrap();
        assert!(read.theme == ThemeChoice::Dark);
        assert_eq!(read.shortcut, "Ctrl+Alt+P");
        assert!(!read.shortcut_enabled);
        let text = fs::read_to_string(&path).unwrap();
        assert!(!text.contains("token") && !text.contains("task"));
        fs::write(&path, "x".repeat(1025)).unwrap();
        assert!(Preferences::read(&path).is_err());
        fs::write(
            &path,
            r#"{"theme":"dark","shortcut":"Alt+F4","shortcut_enabled":true}"#,
        )
        .unwrap();
        assert!(Preferences::read(&path).is_err());
        fs::remove_file(&path).unwrap();
        fs::remove_dir(&directory).unwrap();
    }
}
