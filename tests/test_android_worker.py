import json
import unittest

from oscar.android_worker import (
    ANDROID_CAPABILITIES,
    android_readback,
    platform_readback_matches,
    validate_android,
)


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


class AndroidPlatformReadbackTests(unittest.TestCase):
    def test_exact_document_and_clipboard_destination_readback(self):
        for kind, target, resource in (
            ("android_files_write", "agenda.txt", "agenda.txt"),
            ("android_clipboard_write", "", "android.clipboard.read"),
        ):
            parameters = {"package": "example.synthetic", "target": target, "value": "Agenda"}
            observed = {
                "package": "example.synthetic",
                "observations": [{"resource_id": resource, "text": "Agenda"}],
            }
            self.assertTrue(platform_readback_matches(kind, parameters, observed))
            for changed in (
                {**observed, "package": "example.other"},
                {**observed, "observations": [{"resource_id": resource, "text": "different"}]},
                {**observed, "observations": observed["observations"] * 2},
                {**observed, "observations": [{"resource_id": "other", "text": "Agenda"}]},
            ):
                self.assertFalse(platform_readback_matches(kind, parameters, changed))

    def test_media_readback_checks_state_and_leaves_skip_objective_unknown(self):
        parameters = {"package": "example.synthetic", "target": "", "value": "pause"}

        def observation(package="example.synthetic", state=2):
            return {
                "package": "example.synthetic",
                "observations": [
                    {
                        "resource_id": "android.media.inspect",
                        "text": json.dumps({"package": package, "state": state, "position_ms": 10}),
                    }
                ],
            }

        self.assertTrue(
            platform_readback_matches("android_media_control", parameters, observation())
        )
        self.assertFalse(
            platform_readback_matches("android_media_control", parameters, observation(state=3))
        )
        self.assertFalse(
            platform_readback_matches(
                "android_media_control", parameters, observation(package="example.other")
            )
        )
        self.assertIsNone(
            platform_readback_matches(
                "android_media_control", {**parameters, "value": "next"}, observation()
            )
        )
        self.assertIsNone(platform_readback_matches("android_ui_click", parameters, observation()))


class AndroidConversationTests(unittest.TestCase):
    def test_exact_text_resource_and_optional_device_selection(self):
        from oscar.android_worker import conversation_android

        cases = (
            (
                "Copy Exact  Text to clipboard in example.editor",
                "android_clipboard_write",
                "",
                "Exact  Text",
            ),
            (
                "type Exact  Text into example.editor:id/input",
                "android_ui_set_text",
                "example.editor:id/input",
                "Exact  Text",
            ),
            (
                "write phone file agenda.txt in example.editor with text Exact  Text  ",
                "android_files_write",
                "agenda.txt",
                "Exact  Text  ",
            ),
            ("PAUSE media in example.editor", "android_media_control", "", "pause"),
        )
        for text, kind, target, value in cases:
            with self.subTest(kind=kind):
                expected = {"package": "example.editor", "target": target, "value": value}
                self.assertEqual((None, kind, expected), conversation_android(text))
                self.assertEqual(
                    ("phone-1", kind, expected), conversation_android("On device phone-1: " + text)
                )

    def test_invalid_native_contracts_never_reach_an_executor(self):
        from oscar.android_worker import conversation_android

        for text in (
            "pause media in player",
            "read phone file ../private.txt in example.editor",
            "copy " + "x" * 2001 + " to clipboard in example.editor",
            "open app example.editor component other.editor.MainActivity",
        ):
            with self.subTest(command=text[:40]), self.assertRaises(ValueError):
                conversation_android(text)

    def test_app_and_argument_identity_is_never_inferred(self):
        from oscar.android_worker import conversation_android

        for text in (
            "pause music",
            "open Spotify",
            "click the right button",
            "type text into password",
            "send an unreviewed message",
        ):
            self.assertIsNone(conversation_android(text))
