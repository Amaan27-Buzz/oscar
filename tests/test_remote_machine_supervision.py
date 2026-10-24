import io
import unittest
from threading import Event

from oscar.remote_machine import supervise_stop, supervised_scope


class NativeSupervisionTests(unittest.TestCase):
    def test_scope_is_one_bounded_object_before_any_execution(self):
        self.assertEqual(
            supervised_scope(io.StringIO('{"workspace_id":"synthetic"}\nstop\n')),
            {"workspace_id": "synthetic"},
        )
        for value in ("{}", "[]\n", '{"x":"' + "x" * 16000 + '"}\n'):
            with self.assertRaises(ValueError):
                supervised_scope(io.StringIO(value))

    def test_stop_eof_and_malformed_parent_input_all_withdraw_local_grant(self):
        for value in ("stop\n", "", "unexpected\n", "x" * 100):
            stop = Event()
            supervise_stop(io.StringIO(value), stop)
            self.assertTrue(stop.is_set())


if __name__ == "__main__":
    unittest.main()
