//! Only this Windows account can decrypt a saved connection; WebViews never receive it.
use std::{
    fs,
    io::{Read, Write},
    path::Path,
    ptr,
};
use windows_sys::Win32::{Foundation::LocalFree, Security::Cryptography::*};
use zeroize::{Zeroize, Zeroizing};

fn protect(bytes: &[u8], encrypt: bool) -> Result<Zeroizing<Vec<u8>>, String> {
    if bytes.is_empty() || bytes.len() > 32768 {
        return Err("native connection exceeds boundary".into());
    }
    let input = CRYPT_INTEGER_BLOB {
        cbData: bytes.len() as u32,
        pbData: bytes.as_ptr() as *mut u8,
    };
    let mut output = CRYPT_INTEGER_BLOB {
        cbData: 0,
        pbData: ptr::null_mut(),
    };
    // SAFETY: DPAPI allocates output; it is copied, cleared and freed before returning.
    let success = unsafe {
        if encrypt {
            CryptProtectData(
                &input,
                ptr::null(),
                ptr::null(),
                ptr::null(),
                ptr::null(),
                CRYPTPROTECT_UI_FORBIDDEN,
                &mut output,
            )
        } else {
            CryptUnprotectData(
                &input,
                ptr::null_mut(),
                ptr::null(),
                ptr::null(),
                ptr::null(),
                CRYPTPROTECT_UI_FORBIDDEN,
                &mut output,
            )
        }
    };
    if success == 0 {
        return Err("native connection cannot be unlocked; enroll again".into());
    }
    // SAFETY: successful DPAPI output owns cbData initialized bytes until LocalFree.
    let value = unsafe {
        let allocated = std::slice::from_raw_parts_mut(output.pbData, output.cbData as usize);
        let value = Zeroizing::new(allocated.to_vec());
        allocated.zeroize();
        LocalFree(output.pbData as _);
        value
    };
    if value.len() > 32768 {
        return Err("native connection exceeds boundary".into());
    }
    Ok(value)
}

pub fn load(path: &Path) -> Result<Option<Zeroizing<Vec<u8>>>, String> {
    let file = match fs::File::open(path) {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err("saved Core connection unavailable".into()),
    };
    let mut bytes = Vec::new();
    file.take(32769)
        .read_to_end(&mut bytes)
        .map_err(|_| "saved Core connection unavailable")?;
    protect(&bytes, false).map(Some)
}

pub fn save(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let encrypted = protect(bytes, true)?;
    let parent = path
        .parent()
        .ok_or("native connection directory unavailable")?;
    fs::create_dir_all(parent).map_err(|_| "native connection directory unavailable")?;
    let temporary = path.with_extension(format!("{}.tmp", uuid::Uuid::new_v4().simple()));
    let result = (|| -> std::io::Result<()> {
        let mut file = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary)?;
        file.write_all(&encrypted)?;
        file.sync_all()?;
        fs::rename(&temporary, path)
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temporary);
        return Err("Core connection was not saved; reconnect before continuing".into());
    }
    Ok(())
}

pub fn remove(path: &Path) -> Result<(), String> {
    match fs::remove_file(path) {
        Ok(()) => Ok(()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(_) => Err("saved Core connection could not be removed".into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn saved_connection_is_encrypted_reopenable_replaceable_and_removable() {
        let directory =
            std::env::temp_dir().join(format!("oscar-connection-{}", uuid::Uuid::new_v4()));
        let path = directory.join("connection.dat");
        assert!(load(&path).unwrap().is_none());
        save(&path, b"synthetic-session-secret").unwrap();
        assert!(
            !fs::read(&path)
                .unwrap()
                .windows(24)
                .any(|w| w == b"synthetic-session-secret")
        );
        assert_eq!(
            &**load(&path).unwrap().as_ref().unwrap(),
            b"synthetic-session-secret"
        );
        save(&path, b"rotated-session").unwrap();
        assert_eq!(
            &**load(&path).unwrap().as_ref().unwrap(),
            b"rotated-session"
        );
        fs::write(&path, b"damaged encrypted state").unwrap();
        assert!(load(&path).is_err());
        remove(&path).unwrap();
        remove(&path).unwrap();
        fs::remove_dir(directory).unwrap();
    }
}
