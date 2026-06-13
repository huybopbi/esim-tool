from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot_constants import (
    WAITING_ADD_ESIM_CODE,
    WAITING_ADD_ESIM_DESC,
    WAITING_ADD_ESIM_LPA,
    WAITING_ADD_ESIM_LPA_DESC,
    WAITING_ADD_ESIM_SM_DP,
    WAITING_ADD_ESIM_URL,
    WAITING_ADD_ESIM_URL_DESC,
    WAITING_BULK_LIST,
    WAITING_BULK_SM_DP_CUSTOM,
    WAITING_BULK_SMDP_CHOICE,
    WAITING_ESIM_SELECTION,
    WAITING_SM_DP_LINK,
)
from config import ADMIN_IDS


def setup_bot_handlers(bot):
    """Register Telegram handlers for an eSIMBot instance."""
    admin_filter = filters.User(user_id=ADMIN_IDS)

    bot.application.add_handler(CommandHandler("start", bot.start))
    bot.application.add_handler(
        CommandHandler("help", bot.help_command, filters=admin_filter)
    )
    bot.application.add_handler(CommandHandler("myid", bot.get_user_id))

    create_link_qr_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot.start_create_link_qr, pattern="^create_link_qr$")
        ],
        states={
            WAITING_SM_DP_LINK: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    bot.handle_create_link_qr_auto,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    add_esim_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot.start_add_esim, pattern="^add_esim$"),
            CallbackQueryHandler(bot.start_save_last_esim, pattern="^save_last_esim$"),
        ],
        states={
            WAITING_ADD_ESIM_SM_DP: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_sm_dp,
                )
            ],
            WAITING_ADD_ESIM_CODE: [
                CallbackQueryHandler(
                    bot.skip_add_esim_code,
                    pattern="^skip_activation_code$",
                ),
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
                CommandHandler("skip", bot.handle_add_esim_code),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_code,
                )
            ],
            WAITING_ADD_ESIM_DESC: [
                CallbackQueryHandler(
                    bot.skip_add_esim_description,
                    pattern="^skip_esim_description$",
                ),
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
                CommandHandler("skip", bot.handle_add_esim_desc),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_desc,
                )
            ],
            WAITING_ADD_ESIM_LPA: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_auto,
                )
            ],
            WAITING_ADD_ESIM_LPA_DESC: [
                CallbackQueryHandler(
                    bot.skip_add_esim_description,
                    pattern="^skip_esim_description$",
                ),
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
                CommandHandler("skip", bot.handle_add_esim_lpa_desc),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_lpa_desc,
                )
            ],
            WAITING_ADD_ESIM_URL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_url,
                )
            ],
            WAITING_ADD_ESIM_URL_DESC: [
                CallbackQueryHandler(
                    bot.skip_add_esim_description,
                    pattern="^skip_esim_description$",
                ),
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
                CommandHandler("skip", bot.handle_add_esim_url_desc),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_add_esim_url_desc,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    use_esim_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.start_use_esim, pattern="^use_esim$")],
        states={
            WAITING_ESIM_SELECTION: [
                CallbackQueryHandler(bot.handle_esim_selection, pattern="^select_esim_")
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    bulk_add_esim_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(bot.start_bulk_add_esim, pattern="^bulk_add_esim$")
        ],
        states={
            WAITING_BULK_SMDP_CHOICE: [
                CallbackQueryHandler(
                    bot.handle_bulk_smdp_choice,
                    pattern="^bulk_smdp_(1|2|custom)$",
                ),
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
            ],
            WAITING_BULK_SM_DP_CUSTOM: [
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_bulk_smdp_custom,
                ),
            ],
            WAITING_BULK_LIST: [
                CallbackQueryHandler(
                    bot.cancel_add_esim_callback,
                    pattern="^cancel_add_esim$",
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & admin_filter,
                    bot.handle_bulk_list,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)],
        per_message=False,
        per_chat=True,
        per_user=True,
    )

    bot.application.add_handler(create_link_qr_handler, group=1)
    bot.application.add_handler(add_esim_handler, group=1)
    bot.application.add_handler(use_esim_handler, group=1)
    bot.application.add_handler(bulk_add_esim_handler, group=1)

    bot.application.add_handler(CallbackQueryHandler(bot.button_handler), group=1)
    bot.application.add_handler(CallbackQueryHandler(bot.unauthorized_callback), group=2)
    bot.application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & admin_filter,
            bot.debug_message_handler,
        ),
        group=3,
    )
