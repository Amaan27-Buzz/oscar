//! Provider callbacks stay native; codes never enter the webview.
use reqwest::Url;
use serde_json::Value;
use std::{
    cell::RefCell,
    collections::HashMap,
    io::{Read, Write},
    net::{IpAddr, TcpListener, TcpStream},
    time::{Duration, Instant},
};

pub struct Enrollment {
    pub id: String,
    pub expires_at: u64,
    authorization: Url,
    redirect: Url,
    state: String,
    issuer: Option<String>,
    issuer_required: bool,
    received_issuer: RefCell<Option<String>>,
}
impl Enrollment {
    pub fn parse(value: &Value, now: u64) -> Result<Self, String> {
        let text = |key: &str| {
            value[key]
                .as_str()
                .filter(|s| !s.is_empty() && s.len() <= 8192 && !s.chars().any(char::is_control))
                .ok_or("invalid account enrollment")
        };
        let id = text("id")?.to_owned();
        if id.len() > 128 {
            return Err("invalid account enrollment".into());
        }
        let expiry = value["expires_at"]
            .as_f64()
            .filter(|at| at.is_finite() && *at > now as f64 && *at <= (now + 600) as f64)
            .ok_or("expired account enrollment")?;
        let expires_at = expiry.floor() as u64;
        let authorization = Url::parse(text("url")?).map_err(|_| "invalid provider URL")?;
        let resource_grant = value["authorization_kind"] == "mcp-resource";
        let issuer = if resource_grant {
            Some(text("issuer")?.to_owned())
        } else {
            None
        };
        let redirect = Url::parse(text("redirect_uri")?).map_err(|_| "invalid callback URL")?;
        redirect
            .host_str()
            .and_then(|h| h.trim_matches(['[', ']']).parse::<IpAddr>().ok())
            .filter(IpAddr::is_loopback)
            .ok_or("loopback callback required")?;
        if redirect.scheme() != "http"
            || redirect.port().is_none()
            || redirect.query().is_some()
            || redirect.fragment().is_some()
            || !redirect.username().is_empty()
            || redirect.password().is_some()
            || redirect.path().len() > 200
        {
            return Err("exact loopback callback required".into());
        }
        if authorization.scheme() != "https"
            || !resource_grant && authorization.port_or_known_default() != Some(443)
            || authorization.fragment().is_some()
            || !authorization.username().is_empty()
            || authorization.password().is_some()
            || !if resource_grant {
                let mut endpoint = authorization.clone();
                endpoint.set_query(None);
                endpoint.as_str() == text("authorization_endpoint")?
            } else {
                match authorization.host_str() {
                    Some("accounts.google.com") => authorization.path() == "/o/oauth2/v2/auth",
                    Some("login.microsoftonline.com") => {
                        authorization.path().ends_with("/oauth2/v2.0/authorize")
                    }
                    _ => false,
                }
            }
        {
            return Err("verified provider authorization endpoint required".into());
        }
        let query = pairs(&authorization)?;
        if resource_grant
            && (query.get("resource").map(String::as_str) != Some(text("resource")?)
                || query.get("code_challenge_method").map(String::as_str) != Some("S256"))
        {
            return Err("MCP resource and PKCE binding required".into());
        }
        let state = query
            .get("state")
            .filter(|s| (24..=512).contains(&s.len()))
            .ok_or("bounded OAuth state required")?
            .clone();
        if query.get("redirect_uri") != Some(&redirect.to_string()) {
            return Err("provider callback binding rejected".into());
        }
        Ok(Self {
            id,
            expires_at,
            authorization,
            redirect,
            state,
            issuer,
            issuer_required: value["issuer_required"].as_bool().unwrap_or(false),
            received_issuer: RefCell::new(None),
        })
    }
    pub fn bind(&self) -> Result<TcpListener, String> {
        let address = self
            .redirect
            .socket_addrs(|| None)
            .map_err(|_| "invalid native callback address")?
            .into_iter()
            .next()
            .ok_or("missing native callback address")?;
        if !address.ip().is_loopback() {
            return Err("loopback callback required".into());
        }
        let listener = TcpListener::bind(address).map_err(
            |_| "Account callback port is in use; close the other enrollment and retry.",
        )?;
        listener
            .set_nonblocking(true)
            .map_err(|_| "native callback unavailable")?;
        Ok(listener)
    }
    pub fn open(&self) -> Result<(), String> {
        use windows_sys::Win32::UI::Shell::ShellExecuteW;
        let url: Vec<u16> = self
            .authorization
            .as_str()
            .encode_utf16()
            .chain(Some(0))
            .collect();
        let verb: Vec<u16> = "open".encode_utf16().chain(Some(0)).collect();
        let result = unsafe {
            ShellExecuteW(
                std::ptr::null_mut(),
                verb.as_ptr(),
                url.as_ptr(),
                std::ptr::null(),
                std::ptr::null(),
                1,
            )
        };
        if result as isize <= 32 {
            return Err("Your browser could not open the provider authorization page.".into());
        }
        Ok(())
    }
    fn callback(&self, request: &str) -> Result<String, String> {
        let mut lines = request.split("\r\n");
        let first: Vec<_> = lines
            .next()
            .ok_or("invalid callback request")?
            .split(' ')
            .collect();
        if first.len() != 3
            || first[0] != "GET"
            || first[2] != "HTTP/1.1"
            || !first[1].starts_with('/')
            || first[1].starts_with("//")
        {
            return Err("invalid callback request".into());
        }
        let headers: Vec<_> = lines.take_while(|s| !s.is_empty()).collect();
        let hosts: Vec<_> = headers
            .iter()
            .filter_map(|s| s.split_once(':'))
            .filter(|(key, _)| key.eq_ignore_ascii_case("host"))
            .map(|(_, v)| v.trim())
            .collect();
        let expected = format!(
            "{}:{}",
            self.redirect.host_str().unwrap_or_default(),
            self.redirect.port().unwrap_or_default()
        );
        if hosts.len() != 1 || hosts[0] != expected {
            return Err("callback host rejected".into());
        }
        let callback = self
            .redirect
            .join(first[1])
            .map_err(|_| "invalid callback URL")?;
        if callback.origin() != self.redirect.origin()
            || callback.path() != self.redirect.path()
            || callback.fragment().is_some()
        {
            return Err("callback path rejected".into());
        }
        let query = pairs(&callback)?;
        if let Some(expected) = &self.issuer {
            if query.get("iss").is_some_and(|actual| actual != expected)
                || self.issuer_required && !query.contains_key("iss")
            {
                return Err("MCP callback issuer rejected".into());
            }
        }
        if query.get("state") != Some(&self.state) {
            return Err("callback state rejected".into());
        }
        if query.contains_key("error") {
            return Err("Provider authorization was declined.".into());
        }
        *self.received_issuer.borrow_mut() = query.get("iss").cloned();
        query
            .get("code")
            .filter(|code| {
                !code.is_empty() && code.len() <= 4096 && !code.chars().any(char::is_control)
            })
            .cloned()
            .ok_or_else(|| "missing authorization code".into())
    }
    pub fn wait(
        &self,
        listener: TcpListener,
        current: impl Fn() -> bool,
    ) -> Result<String, String> {
        let deadline = Instant::now() + Duration::from_secs(600);
        while current()
            && crate::core::now_ms() / 1000 < self.expires_at
            && Instant::now() < deadline
        {
            match listener.accept() {
                Ok((mut stream, address)) => {
                    if !address.ip().is_loopback() {
                        continue;
                    }
                    let result =
                        read_request(&mut stream).and_then(|request| self.callback(&request));
                    let accepted = result.is_ok();
                    let body = if accepted {
                        "Authorization received. Return to OSCAR to check the account connection."
                    } else {
                        "This callback was not accepted. Return to OSCAR and check the enrollment."
                    };
                    let _ = stream.set_write_timeout(Some(Duration::from_secs(2)));
                    let _ = write!(
                        stream,
                        "HTTP/1.1 {}\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {}\r\nCache-Control: no-store\r\nReferrer-Policy: no-referrer\r\nContent-Security-Policy: default-src 'none'; frame-ancestors 'none'\r\nConnection: close\r\n\r\n{}",
                        if accepted {
                            "200 OK"
                        } else {
                            "400 Bad Request"
                        },
                        body.len(),
                        body
                    );
                    if let Ok(code) = result {
                        if current() {
                            return Ok(code);
                        } else {
                            break;
                        }
                    }
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    std::thread::sleep(Duration::from_millis(100))
                }
                Err(_) => return Err("native callback listener failed".into()),
            }
        }
        Err("Account enrollment expired or was cancelled. Start a new connection.".into())
    }
    pub fn state(&self) -> &str {
        &self.state
    }
    pub fn response_issuer(&self) -> Option<String> {
        self.received_issuer.borrow().clone()
    }
}
fn pairs(url: &Url) -> Result<HashMap<String, String>, String> {
    let mut result = HashMap::new();
    for (key, value) in url.query_pairs() {
        if result
            .insert(key.into_owned(), value.into_owned())
            .is_some()
        {
            return Err("duplicate OAuth parameter".into());
        }
    }
    Ok(result)
}
fn read_request(stream: &mut TcpStream) -> Result<String, String> {
    let deadline = Instant::now() + Duration::from_secs(2);
    let mut bytes = Vec::new();
    while bytes.len() < 8192 {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return Err("callback read deadline exceeded".into());
        }
        stream
            .set_read_timeout(Some(remaining))
            .map_err(|_| "callback unavailable")?;
        let mut buffer = [0; 1024];
        let count = stream
            .read(&mut buffer)
            .map_err(|_| "callback read failed")?;
        if count == 0 {
            break;
        }
        bytes.extend_from_slice(&buffer[..count]);
        if bytes.windows(4).any(|w| w == b"\r\n\r\n") {
            return String::from_utf8(bytes).map_err(|_| "invalid callback encoding".into());
        }
    }
    Err("bounded callback headers required".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    #[test]
    fn mcp_resource_callback_preserves_exact_issuer_and_resource() {
        let value = json!({"id":"pending","expires_at":120,
            "authorization_kind":"mcp-resource","issuer":"https://auth.example.com/tenant",
            "issuer_required":true,"resource":"https://mcp.example.com/mcp",
            "authorization_endpoint":"https://auth.example.com/authorize",
            "redirect_uri":"http://127.0.0.1:48123/oauth/callback",
            "url":"https://auth.example.com/authorize?state=synthetic-state-with-32-characters&redirect_uri=http%3A%2F%2F127.0.0.1%3A48123%2Foauth%2Fcallback&resource=https%3A%2F%2Fmcp.example.com%2Fmcp&code_challenge_method=S256"});
        let e = Enrollment::parse(&value, 100).unwrap();
        let request = "GET /oauth/callback?state=synthetic-state-with-32-characters&code=x&iss=https%3A%2F%2Fauth.example.com%2Ftenant HTTP/1.1\r\nHost: 127.0.0.1:48123\r\n\r\n";
        assert_eq!(e.callback(request).unwrap(), "x");
        assert_eq!(
            e.response_issuer().as_deref(),
            Some("https://auth.example.com/tenant")
        );
        assert!(
            e.callback(&request.replace("auth.example.com", "attacker.test"))
                .is_err()
        );
        assert!(
            e.callback(&request.replace("&iss=https%3A%2F%2Fauth.example.com%2Ftenant", ""))
                .is_err()
        );
    }
    fn enrollment() -> Enrollment {
        Enrollment::parse(&json!({"id":"pending","url":"https://accounts.google.com/o/oauth2/v2/auth?redirect_uri=http%3A%2F%2F127.0.0.1%3A48123%2Foauth%2Fcallback&state=synthetic-state-with-32-characters","redirect_uri":"http://127.0.0.1:48123/oauth/callback","expires_at":120}),100).unwrap()
    }
    #[test]
    fn exact_callback_excludes_cross_origin_duplicate_and_wrong_state_requests() {
        let e = enrollment();
        let request = "GET /oauth/callback?state=synthetic-state-with-32-characters&code=synthetic-code HTTP/1.1\r\nHost: 127.0.0.1:48123\r\n\r\n";
        assert_eq!(e.callback(request).unwrap(), "synthetic-code");
        for bad in [
            request.replace("127.0.0.1:48123", "attacker.test"),
            request.replace("/oauth/callback?", "/wrong?"),
            request.replace("&code=", "&state=duplicate&code="),
            request.replace("synthetic-state-with-32-characters", "wrong"),
            request.replace("GET ", "POST "),
        ] {
            assert!(e.callback(&bad).is_err());
        }
    }
    #[test]
    fn enrollment_never_opens_an_arbitrary_url() {
        for url in [
            "https://attacker.test/",
            "file:///private",
            "https://accounts.google.com/other",
            "https://user:password@accounts.google.com/o/oauth2/v2/auth",
        ] {
            assert!(Enrollment::parse(&json!({"id":"pending","url":url,"redirect_uri":"http://127.0.0.1:48123/oauth/callback","expires_at":120}),100).is_err());
        }
    }
    #[test]
    fn expired_and_non_loopback_redirects_fail_closed() {
        let e = enrollment();
        for (redirect, expiry) in [
            ("http://192.0.2.1:48123/oauth/callback", 120),
            ("http://127.0.0.1:48123/oauth/callback", 99),
        ] {
            assert!(Enrollment::parse(&json!({"id":"pending","url":e.authorization.as_str(),"redirect_uri":redirect,"expires_at":expiry}),100).is_err());
        }
    }
    #[test]
    fn actual_loopback_listener_delivers_code_and_cancel_stops_waiting() {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        listener.set_nonblocking(true).unwrap();
        let address = listener.local_addr().unwrap();
        let mut e = enrollment();
        e.redirect.set_port(Some(address.port())).unwrap();
        e.expires_at = crate::core::now_ms() / 1000 + 60;
        let sender = std::thread::spawn(move || {
            let mut stream = TcpStream::connect(address).unwrap();
            stream
                .set_read_timeout(Some(Duration::from_secs(5)))
                .unwrap();
            write!(stream, "GET /oauth/callback?state=synthetic-state-with-32-characters&code=synthetic-code HTTP/1.1\r\nHost: {address}\r\n\r\n").unwrap();
            let mut response = String::new();
            stream.read_to_string(&mut response).unwrap();
            assert!(response.starts_with("HTTP/1.1 200 OK"));
            assert!(!response.contains("synthetic-code"));
        });
        assert_eq!(e.wait(listener, || true).unwrap(), "synthetic-code");
        sender.join().unwrap();
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        listener.set_nonblocking(true).unwrap();
        assert!(e.wait(listener, || false).is_err());
    }
}
