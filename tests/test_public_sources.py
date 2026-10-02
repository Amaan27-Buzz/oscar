import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.request import Request, build_opener

from oscar.http_client import NoRedirects
from oscar.models import Failure, ProviderError
from oscar.public_sources import read_official_page


class OfficialPageTests(unittest.TestCase):
    """Loopback wire tests establish page-reader behavior, not live provider facts."""

    def setUp(self):
        self.body = (
            b"<main><p>Current text models support developer workloads with free account "
            b"access subject to published quota limits.</p></main>"
        )
        self.mime = "text/html; charset=utf-8"
        self.status = 200
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                outer.requests.append(
                    {
                        "path": self.path,
                        "authorization": bool(self.headers.get("Authorization")),
                        "cookie": bool(self.headers.get("Cookie")),
                        "user_agent": self.headers.get("User-Agent"),
                    }
                )
                self.send_response(outer.status)
                self.send_header("Content-Type", outer.mime)
                self.send_header("Content-Length", str(len(outer.body)))
                if outer.status == 302:
                    self.send_header("Location", "/redirected")
                self.end_headers()
                self.wfile.write(outer.body)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        destination = f"http://127.0.0.1:{self.server.server_port}"

        class LoopbackOpener:
            def open(self, request, timeout):
                headers = dict(request.header_items())
                replacement = Request(destination + "/page", headers=headers)
                return build_opener(NoRedirects()).open(replacement, timeout=timeout)

        self.opener = LoopbackOpener()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def read(self, url="https://console.groq.com/docs/models", **kwargs):
        return read_official_page(url, 2, opener=self.opener, **kwargs)

    def test_wire_reader_has_no_authentication_and_keeps_relevant_visible_text(self):
        self.body = (
            b"<script>models hidden script</script><style>free hidden style</style>"
            b"<nav><div>models hidden navigation</div></nav>"
            b"<header>free hidden header</header><footer>quota hidden footer</footer>"
            b"<svg>models hidden svg</svg><noscript>models hidden noscript</noscript>"
            b"<p>Current models provide free developer access subject to documented "
            b"account quota and request limits.</p>"
        )
        text = self.read()
        self.assertIn("free developer access", text)
        self.assertNotIn("hidden", text)
        self.assertFalse(self.requests[0]["authorization"])
        self.assertFalse(self.requests[0]["cookie"])
        self.assertEqual(self.requests[0]["user_agent"], "Mozilla/5.0")

    def test_allowlist_rejects_untrusted_or_credential_bearing_urls_without_network(self):
        urls = [
            "http://console.groq.com/docs/models",
            "https://console.groq.com.attacker.test/docs/models",
            "https://user:password@console.groq.com/docs/models",
            "https://console.groq.com:9443/docs/models",
            "https://console.groq.com/docs/models?token=example",
            "https://console.groq.com/docs/models#fragment",
        ]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ProviderError) as error:
                self.read(url)
            self.assertEqual(error.exception.category, Failure.CAPABILITY)
        self.assertEqual(self.requests, [])

    def test_body_bound_and_nontext_content_fail_safely(self):
        self.body = b"a" * 500_001
        with self.assertRaises(ProviderError) as error:
            self.read()
        self.assertEqual(error.exception.category, Failure.CAPABILITY)
        self.mime = "application/json"
        self.body = b'{"model":"example"}'
        with self.assertRaises(ProviderError):
            self.read()

    def test_redirect_is_not_followed_and_only_categorical_failure_is_exposed(self):
        self.status = 302
        self.body = b"untrusted raw failure text"
        with self.assertRaises(ProviderError) as error:
            self.read()
        self.assertEqual(error.exception.category, Failure.NETWORK)
        self.assertEqual(error.exception.http_status, 302)
        self.assertEqual(str(error.exception), Failure.NETWORK.value)
        self.assertEqual(len(self.requests), 1)

    def test_empty_challenge_and_boilerplate_pages_do_not_claim_current_evidence(self):
        for body in (
            b"",
            b"<main><h1>Models</h1><p>Loading</p></main>",
            b"<nav>Model navigation contains enough words to look like relevant "
            b"provider documentation but is only a menu.</nav>",
            b"<p>Verify you are human before accessing our model documentation "
            b"and developer quota or pricing pages.</p>",
        ):
            with self.subTest(body=body):
                self.body = body
                with self.assertRaises(ProviderError) as error:
                    self.read()
                self.assertEqual(error.exception.category, Failure.CAPABILITY)

    def test_excerpt_is_bounded_and_redaction_precedes_truncation(self):
        prefix = "Current models and free developer quota limits. " + "x" * 1430
        opaque = "synthetic-value-crossing-excerpt-boundary"
        self.body = ("<p>" + prefix + opaque + "</p>").encode()
        text = self.read(redact=lambda value: value.replace(opaque, "[REDACTED]"))
        self.assertLessEqual(len(text), 1500)
        self.assertIn("[REDACTED]", text)
        self.assertNotIn("synthetic-value", text)

    def test_plain_and_markdown_text_are_supported(self):
        self.body = (
            b"# Models\nCurrent models offer free developer access subject to "
            b"account-specific quotas and published request limits."
        )
        for mime in ("text/plain", "text/markdown"):
            with self.subTest(mime=mime):
                self.mime = mime
                self.assertIn("free developer access", self.read())
