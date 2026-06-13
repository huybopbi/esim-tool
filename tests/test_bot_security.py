import unittest
from types import SimpleNamespace

from bot_constants import PUBLIC_CALLBACKS
from bot_keyboards import (
    build_guide_menu_keyboard,
    build_main_menu_keyboard,
    build_result_actions_keyboard,
    build_storage_result_keyboard,
)
from bot_user_info import format_user_id_response


def callback_data(markup):
    return [
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
    ]


class BotSecurityTest(unittest.TestCase):
    def test_main_menu_hides_storage_for_non_admin(self):
        data = callback_data(build_main_menu_keyboard(is_admin=False))

        self.assertIn("create_link_qr", data)
        self.assertIn("guide_menu", data)
        self.assertNotIn("check_iccid", data)
        self.assertNotIn("storage_menu", data)

    def test_main_menu_shows_storage_for_admin(self):
        data = callback_data(build_main_menu_keyboard(is_admin=True))

        self.assertIn("storage_menu", data)

    def test_guide_menu_exposes_public_help_actions(self):
        data = callback_data(build_guide_menu_keyboard())

        self.assertIn("iphone_guide", data)
        self.assertIn("android_guide", data)
        self.assertIn("check_device", data)
        self.assertIn("support", data)
        self.assertIn("back_to_menu", data)

    def test_guide_callbacks_are_public(self):
        self.assertTrue({
            "guide_menu",
            "iphone_guide",
            "android_guide",
            "check_device",
            "support",
        }.issubset(PUBLIC_CALLBACKS))

    def test_result_actions_for_non_admin_are_public_only(self):
        data = callback_data(build_result_actions_keyboard(is_admin=False, can_save=True))

        self.assertIn("create_link_qr", data)
        self.assertIn("guide_menu", data)
        self.assertIn("back_to_menu", data)
        self.assertNotIn("check_iccid", data)
        self.assertNotIn("save_last_esim", data)
        self.assertNotIn("storage_menu", data)

    def test_result_actions_for_admin_include_storage_actions(self):
        data = callback_data(build_result_actions_keyboard(is_admin=True, can_save=True))

        self.assertIn("save_last_esim", data)
        self.assertIn("storage_menu", data)

    def test_storage_result_actions_keep_admin_workflow_shortcuts(self):
        data = callback_data(build_storage_result_keyboard())

        self.assertIn("add_esim", data)
        self.assertIn("view_available", data)
        self.assertIn("use_esim", data)
        self.assertIn("storage_menu", data)
        self.assertIn("back_to_menu", data)

    def test_myid_response_does_not_leak_admin_ids_to_non_admin(self):
        user = SimpleNamespace(
            id=200,
            username="normal_user",
            first_name="Normal",
            last_name=None,
        )

        response = format_user_id_response(user, [100, 101])

        self.assertIn("User ID", response)
        self.assertIn("❌ No", response)
        self.assertNotIn("Admin IDs configured", response)
        self.assertNotIn("100", response)
        self.assertNotIn("101", response)

    def test_myid_response_keeps_admin_details_for_admin(self):
        user = SimpleNamespace(
            id=100,
            username="admin_user",
            first_name="Admin",
            last_name="Owner",
        )

        response = format_user_id_response(user, [100, 101])

        self.assertIn("Admin IDs configured", response)
        self.assertIn("✅ Yes", response)
        self.assertIn("Owner", response)


if __name__ == "__main__":
    unittest.main()
