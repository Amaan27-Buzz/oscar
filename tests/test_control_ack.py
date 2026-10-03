import json
import unittest
from time import time
from unittest.mock import patch

from oscar.contracts import Envelope
from oscar.grid import SessionHandle
from oscar.transport import HTTPTransport


class ControlAckTests(unittest.TestCase):
    def test_pause_qualifier_compatible_but_identity_and_schema_strict(self):
        envelope = Envelope("pause", "node", "session", "task", "correlation", "lease", {}, time())
        session = SessionHandle("session", "node", "synthetic-session-token")
        base = {"kind": "pause", "task_id": "task", "correlation_id": "correlation"}
        valid = [base, {**base, "pause_semantics": "before-next-subprocess"}]
        invalid = [
            {**base, "task_id": "different"},
            {**base, "unexpected": "extra"},
            {**base, "pause_semantics": "arbitrary-process-suspension"},
        ]
        with patch("oscar.transport.build_opener") as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            for data in valid:
                response.read.return_value = json.dumps(data).encode()
                self.assertEqual(
                    data, HTTPTransport("http://127.0.0.1:1").control(envelope, session)
                )
            for data in invalid:
                response.read.return_value = json.dumps(data).encode()
                with self.assertRaises(ValueError):
                    HTTPTransport("http://127.0.0.1:1").control(envelope, session)
