from bot import (
    confirm_answers,
    edit_answers,
    error_handler,
    handle_edit_choice,
    handle_edit_profile,
    handle_my_applications,
    handle_my_profile,
    handle_profile_edit_choice,
    handle_start_button,
    route_message_based_on_state,
    start,
)
from config import BOT_TOKEN
from telegram import Update
from telegram.ext import (
    Application as TelegramApplication,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)


def init_bot() -> TelegramApplication:
    """Инициализирует и настраивает Telegram-бота."""
    application = TelegramApplication.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        CommandHandler("my_applications", handle_my_applications))
    application.add_handler(
        MessageHandler(filters.Regex('^Создать заявку$'), handle_start_button))
    application.add_handler(
        MessageHandler(filters.Regex('^Мои заявки$'), handle_my_applications))
    application.add_handler(
        MessageHandler(filters.Regex('^Мой профиль$'), handle_my_profile))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           route_message_based_on_state))
    application.add_handler(
        CallbackQueryHandler(confirm_answers, pattern="confirm_answers"))
    application.add_handler(
        CallbackQueryHandler(edit_answers, pattern="edit_answers"))
    application.add_handler(
        CallbackQueryHandler(handle_edit_choice, pattern=r"edit_\d+"))
    application.add_handler(CallbackQueryHandler(
        handle_profile_edit_choice,
        pattern=r"edit_(name|email|phone)"))
    application.add_handler(
        CallbackQueryHandler(handle_edit_profile, pattern="edit_profile"))

    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    init_bot()
