//! Windows CNG holds the private key. Only the public DER and bounded signatures leave here.
use sha2::{Digest, Sha256};
use std::{ptr, sync::Mutex};
use windows_sys::Win32::Security::Cryptography::*;

pub struct Signer {
    handles: Mutex<(usize, usize)>,
}
impl Signer {
    pub fn new() -> Result<Self, String> {
        Self::open(None)
    }
    pub fn persistent(installation: &str) -> Result<Self, String> {
        if installation.is_empty()
            || installation.len() > 80
            || !installation
                .chars()
                .all(|c| c.is_ascii_alphanumeric() || c == '-')
        {
            return Err("invalid native installation identity".into());
        }
        let name: Vec<u16> = format!("Dawnlight.OSCAR.{installation}")
            .encode_utf16()
            .chain(Some(0))
            .collect();
        Self::open(Some(&name))
    }
    pub fn remove_persistent(installation: &str) -> Result<(), String> {
        let signer = Self::persistent(installation)?;
        let mut guard = signer
            .handles
            .lock()
            .map_err(|_| "native key unavailable")?;
        // SAFETY: only the exact OSCAR installation key is deleted; zero fences Drop.
        if unsafe { NCryptDeleteKey(guard.1, NCRYPT_SILENT_FLAG) } != 0 {
            return Err("native connection key could not be removed".into());
        }
        guard.1 = 0;
        Ok(())
    }
    fn open(name: Option<&[u16]>) -> Result<Self, String> {
        let mut provider = 0;
        let mut key = 0;
        // SAFETY: valid writable handles; CNG owns storage until Drop.
        unsafe {
            if NCryptOpenStorageProvider(&mut provider, MS_KEY_STORAGE_PROVIDER, 0) != 0 {
                return Err("native signing provider unavailable".into());
            }
            let key_name = name.map_or(ptr::null(), |value| value.as_ptr());
            let opened = name.is_some()
                && NCryptOpenKey(provider, &mut key, key_name, 0, NCRYPT_SILENT_FLAG) == 0;
            // No overwrite flag: an inaccessible existing key cannot silently rotate identity.
            if !opened
                && (NCryptCreatePersistedKey(
                    provider,
                    &mut key,
                    BCRYPT_RSA_ALGORITHM,
                    key_name,
                    0,
                    NCRYPT_SILENT_FLAG,
                ) != 0
                    || NCryptSetProperty(
                        key,
                        NCRYPT_LENGTH_PROPERTY,
                        2048u32.to_le_bytes().as_ptr(),
                        4,
                        0,
                    ) != 0
                    || NCryptFinalizeKey(key, NCRYPT_SILENT_FLAG) != 0)
            {
                if key != 0 {
                    NCryptFreeObject(key);
                }
                NCryptFreeObject(provider);
                return Err("native owner key unavailable".into());
            }
        }
        Ok(Self {
            handles: Mutex::new((provider, key)),
        })
    }
    pub fn public_der(&self) -> Result<Vec<u8>, String> {
        let guard = self.handles.lock().map_err(|_| "native key unavailable")?;
        let mut length = 0;
        // SAFETY: public export only, output buffer is sized by CNG first.
        unsafe {
            if NCryptExportKey(
                guard.1,
                0,
                BCRYPT_RSAPUBLIC_BLOB,
                ptr::null(),
                ptr::null_mut(),
                0,
                &mut length,
                0,
            ) != 0
            {
                return Err("public owner key unavailable".into());
            }
            let mut blob = vec![0; length as usize];
            if NCryptExportKey(
                guard.1,
                0,
                BCRYPT_RSAPUBLIC_BLOB,
                ptr::null(),
                blob.as_mut_ptr(),
                length,
                &mut length,
                0,
            ) != 0
            {
                return Err("public owner key unavailable".into());
            }
            public_blob_der(&blob)
        }
    }
    pub fn sign(&self, body: &[u8]) -> Result<Vec<u8>, String> {
        if body.len() > 32768 {
            return Err("signing envelope exceeds bound".into());
        }
        let guard = self.handles.lock().map_err(|_| "native key unavailable")?;
        let hash = Sha256::digest(body);
        let padding = BCRYPT_PSS_PADDING_INFO {
            pszAlgId: BCRYPT_SHA256_ALGORITHM,
            cbSalt: 32,
        };
        let mut size = 0;
        // SAFETY: immutable digest/padding and CNG-owned key, under the key lifetime mutex.
        unsafe {
            if NCryptSignHash(
                guard.1,
                &padding as *const _ as _,
                hash.as_ptr(),
                32,
                ptr::null_mut(),
                0,
                &mut size,
                NCRYPT_PAD_PSS_FLAG | NCRYPT_SILENT_FLAG,
            ) != 0
            {
                return Err("native signing unavailable".into());
            }
            let mut signature = vec![0; size as usize];
            if NCryptSignHash(
                guard.1,
                &padding as *const _ as _,
                hash.as_ptr(),
                32,
                signature.as_mut_ptr(),
                size,
                &mut size,
                NCRYPT_PAD_PSS_FLAG | NCRYPT_SILENT_FLAG,
            ) != 0
            {
                return Err("native signing unavailable".into());
            }
            Ok(signature)
        }
    }
}
impl Drop for Signer {
    fn drop(&mut self) {
        if let Ok(guard) = self.handles.lock() {
            // SAFETY: each owned CNG handle is released exactly once after users have dropped the Arc.
            unsafe {
                NCryptFreeObject(guard.1);
                NCryptFreeObject(guard.0);
            }
        }
    }
}
fn der(tag: u8, body: &[u8]) -> Vec<u8> {
    let mut value = vec![tag];
    if body.len() < 128 {
        value.push(body.len() as u8);
    } else {
        let bytes = (body.len() as u32).to_be_bytes();
        let used = bytes.iter().position(|x| *x != 0).unwrap_or(3);
        value.push(0x80 | (4 - used) as u8);
        value.extend(&bytes[used..]);
    }
    value.extend(body);
    value
}
fn integer(bytes: &[u8]) -> Vec<u8> {
    let mut value = Vec::new();
    if bytes.first().is_some_and(|x| x & 0x80 != 0) {
        value.push(0);
    }
    value.extend(bytes);
    der(2, &value)
}
fn public_blob_der(blob: &[u8]) -> Result<Vec<u8>, String> {
    if blob.len() < 24 || &blob[..4] != b"RSA1" {
        return Err("invalid native public key".into());
    }
    let exp =
        u32::from_le_bytes(blob[8..12].try_into().map_err(|_| "invalid public key")?) as usize;
    let modulus =
        u32::from_le_bytes(blob[12..16].try_into().map_err(|_| "invalid public key")?) as usize;
    if exp > 8 || modulus != 256 || blob.len() != 24 + exp + modulus {
        return Err("invalid public key size".into());
    }
    let mut rsa = integer(&blob[24 + exp..]);
    rsa.extend(integer(&blob[24..24 + exp]));
    let mut bitstring = vec![0];
    bitstring.extend(der(0x30, &rsa));
    let mut subject = vec![
        0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00,
    ];
    subject.extend(der(3, &bitstring));
    Ok(der(0x30, &subject))
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn public_export_is_transport_only() {
        assert!(public_blob_der(b"private").is_err());
        assert_eq!(integer(&[0x80]), vec![2, 2, 0, 0x80]);
        let signer = Signer::new().expect("Windows CNG");
        assert_eq!(
            &signer.public_der().expect("public DER")[..2],
            &[0x30, 0x82]
        );
        assert_eq!(
            signer
                .sign(b"reference challenge")
                .expect("native PSS")
                .len(),
            256
        );
    }
    #[test]
    fn persistent_key_reopens_without_exporting_private_material() {
        let installation = uuid::Uuid::new_v4().to_string();
        let first = Signer::persistent(&installation).unwrap();
        let public = first.public_der().unwrap();
        drop(first);
        let reopened = Signer::persistent(&installation).unwrap();
        assert_eq!(public, reopened.public_der().unwrap());
        assert_eq!(reopened.sign(b"restart proof").unwrap().len(), 256);
        let mut guard = reopened.handles.lock().unwrap();
        // SAFETY: remove this test's unique key only; zero prevents a second free.
        assert_eq!(unsafe { NCryptDeleteKey(guard.1, NCRYPT_SILENT_FLAG) }, 0);
        guard.1 = 0;
        assert!(Signer::persistent("../invalid").is_err());
    }
}
