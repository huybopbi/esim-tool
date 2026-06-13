import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock

import bot as botmod
from bot_constants import (
    WAITING_BULK_LIST,
    WAITING_BULK_SM_DP_CUSTOM,
    WAITING_BULK_SMDP_CHOICE,
)
from esim_storage import eSIMStorage
from telegram.ext import ConversationHandler

# Khớp với ADMIN_IDS mặc định trong config.example.py
ADMIN_ID = 123456789


def make_callback_update(data, user_id=ADMIN_ID):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.username = "admin"
    update.message = None
    query = update.callback_query
    query.data = data
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    query.delete_message = AsyncMock()
    query.message.reply_text = AsyncMock()
    query.message.reply_photo = AsyncMock()
    update.effective_message = query.message
    return update


def make_message_update(text, user_id=ADMIN_ID):
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.username = "admin"
    update.callback_query = None
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
    update.effective_message = update.message
    return update


def make_context():
    context = MagicMock()
    context.user_data = {}
    return context


class BulkFlowIntegrationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        self.storage = eSIMStorage(db_path=self.db_path)
        self._original_storage = botmod.esim_storage
        botmod.esim_storage = self.storage
        self.bot = botmod.eSIMBot()

    def tearDown(self):
        botmod.esim_storage = self._original_storage
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    async def test_full_bulk_flow_with_preset_sm_dp(self):
        context = make_context()

        # Bước 1: vào menu thêm hàng loạt
        state = await self.bot.start_bulk_add_esim(
            make_callback_update("bulk_add_esim"), context
        )
        self.assertEqual(state, WAITING_BULK_SMDP_CHOICE)

        # Bước 2: chọn preset rsp.esim.exchange
        state = await self.bot.handle_bulk_smdp_choice(
            make_callback_update("bulk_smdp_1"), context
        )
        self.assertEqual(state, WAITING_BULK_LIST)
        self.assertEqual(context.user_data["bulk_sm_dp"], "rsp.esim.exchange")

        # Bước 3: dán danh sách đúng định dạng người dùng
        bulk_text = (
            "Activation Code:OZ8NB-X9008-G1LB2-xxxxx\n"
            "ICCID:89851000000010674211\n"
            "\n"
            "Activation Code:QRQNB-W2108-J1JE3-xxxx\n"
            "ICCID:89851000000010674213\n"
        )
        state = await self.bot.handle_bulk_list(
            make_message_update(bulk_text), context
        )
        self.assertEqual(state, ConversationHandler.END)

        available = self.storage.get_available_esims()
        self.assertEqual(len(available), 2)
        smdps = {e.sm_dp_address for e in available}
        self.assertEqual(smdps, {"rsp.esim.exchange"})
        iccids = {e.iccid for e in available}
        self.assertEqual(iccids, {"89851000000010674211", "89851000000010674213"})

    async def test_custom_sm_dp_flow(self):
        context = make_context()

        await self.bot.start_bulk_add_esim(
            make_callback_update("bulk_add_esim"), context
        )

        state = await self.bot.handle_bulk_smdp_choice(
            make_callback_update("bulk_smdp_custom"), context
        )
        self.assertEqual(state, WAITING_BULK_SM_DP_CUSTOM)

        state = await self.bot.handle_bulk_smdp_custom(
            make_message_update("rsp.custom-provider.com"), context
        )
        self.assertEqual(state, WAITING_BULK_LIST)
        self.assertEqual(context.user_data["bulk_sm_dp"], "rsp.custom-provider.com")

        state = await self.bot.handle_bulk_list(
            make_message_update("Activation Code:ABC-1\nICCID:777\n"), context
        )
        self.assertEqual(state, ConversationHandler.END)

        available = self.storage.get_available_esims()
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].sm_dp_address, "rsp.custom-provider.com")
        self.assertEqual(
            available[0].lpa_string, "LPA:1$rsp.custom-provider.com$ABC-1"
        )

    async def test_invalid_custom_sm_dp_stays_in_state(self):
        context = make_context()
        context.user_data["bulk_sm_dp"] = ""

        state = await self.bot.handle_bulk_smdp_custom(
            make_message_update("not-a-domain"), context
        )
        self.assertEqual(state, WAITING_BULK_SM_DP_CUSTOM)

    async def test_non_admin_cannot_start_bulk(self):
        context = make_context()
        update = make_callback_update("bulk_add_esim", user_id=999)

        state = await self.bot.start_bulk_add_esim(update, context)
        self.assertEqual(state, ConversationHandler.END)


class UseEsimNoteFlowTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        self.storage = eSIMStorage(db_path=self.db_path)
        self._original_storage = botmod.esim_storage
        botmod.esim_storage = self.storage
        self.bot = botmod.eSIMBot()
        self.esim_id = self.storage.add_esim_from_lpa(
            "LPA:1$rsp.esim.exchange$CODE-1"
        )

    def tearDown(self):
        botmod.esim_storage = self._original_storage
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    async def test_select_then_note_marks_used_with_note(self):
        from bot_constants import WAITING_USE_ESIM_NOTE

        context = make_context()

        state = await self.bot.handle_esim_selection(
            make_callback_update(f"select_esim_{self.esim_id}"), context
        )
        self.assertEqual(state, WAITING_USE_ESIM_NOTE)
        self.assertEqual(context.user_data["use_esim_id"], self.esim_id)

        state = await self.bot.handle_use_esim_note(
            make_message_update("Nguyễn Văn A - 0901234567"), context
        )
        self.assertEqual(state, ConversationHandler.END)

        entry = self.storage.get_esim_by_id(self.esim_id)
        self.assertEqual(entry.status, "used")
        self.assertEqual(entry.used_note, "Nguyễn Văn A - 0901234567")

    async def test_skip_note_marks_used_without_note(self):
        context = make_context()

        await self.bot.handle_esim_selection(
            make_callback_update(f"select_esim_{self.esim_id}"), context
        )
        state = await self.bot.skip_use_esim_note(
            make_callback_update("skip_use_note"), context
        )
        self.assertEqual(state, ConversationHandler.END)

        entry = self.storage.get_esim_by_id(self.esim_id)
        self.assertEqual(entry.status, "used")
        self.assertEqual(entry.used_note, "")

    async def test_cancel_use_keeps_esim_available(self):
        context = make_context()

        await self.bot.handle_esim_selection(
            make_callback_update(f"select_esim_{self.esim_id}"), context
        )
        state = await self.bot.cancel_use_esim_callback(
            make_callback_update("cancel_use_esim"), context
        )
        self.assertEqual(state, ConversationHandler.END)

        entry = self.storage.get_esim_by_id(self.esim_id)
        self.assertEqual(entry.status, "available")


if __name__ == "__main__":
    unittest.main()
