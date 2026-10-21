import unittest

from oscar.android_worker import ANDROID_CAPABILITIES, android_readback, validate_android


class AndroidAdmissionTests(unittest.TestCase):
    def test_exact_selected_app_and_readback_never_replay_mutation(self):
        parameters = {
            "package": "example.synthetic",
            "target": "example.synthetic:id/input",
            "value": "agenda",
        }
        self.assertEqual(validate_android("android_ui_set_text", parameters), parameters)
        self.assertEqual(
            android_readback(parameters),
            {"package": "example.synthetic", "target": "", "value": ""},
        )
        self.assertEqual(len(ANDROID_CAPABILITIES), 20)

    def test_hidden_parameters_bad_targets_and_unsafe_links_fail_closed(self):
        base = {
            "package": "example.synthetic",
            "target": "example.synthetic.Form",
            "value": "https://example.test",
        }
        for changed in (
            {**base, "hidden": "intent"},
            {**base, "target": "example.other.Form"},
            {**base, "value": "file:///private"},
            {**base, "value": "https://user:secret@example.test"},
        ):
            with self.assertRaises(ValueError):
                validate_android("android_link_open", changed)

    def test_drafts_and_gestures_are_typed_bounded_and_not_arbitrary_actions(self):
        base = {
            "package": "example.synthetic",
            "target": "example.synthetic:id/list",
            "value": "up",
        }
        self.assertEqual(validate_android("android_ui_gesture", base), base)
        with self.assertRaises(ValueError):
            validate_android("android_ui_gesture", {**base, "value": "0,0,9999,9999"})
        with self.assertRaises(ValueError):
            validate_android(
                "android_message_compose",
                {
                    **base,
                    "target": "example.synthetic.Form",
                    "value": '{"number":"+123","text":"draft","send":true}',
                },
            )
        with self.assertRaises(ValueError):
            validate_android(
                "android_calendar_insert",
                {
                    **base,
                    "target": "example.synthetic.Form",
                    "value": '{"title":"Meeting","begin_ms":true,"end_ms":2}',
                },
            )
