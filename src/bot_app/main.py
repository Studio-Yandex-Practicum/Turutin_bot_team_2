import logging

from telegram.ext import (
    Application as TelegramApplication,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .bot import (
    error_handler,
    handle_message,
    handle_my_applications,
    handle_question_response,
    handle_start_button,
    start,
    start_new_survey,
)
from .config import BOT_TOKEN


def init_bot() -> TelegramApplication:
    """Инициализирует и настраивает Telegram бота."""
    application = TelegramApplication.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        CommandHandler("my_applications", handle_my_applications))
    application.add_handler(
        MessageHandler(filters.Regex('^Создать заявку$'), handle_start_button),
    )
    application.add_handler(
        MessageHandler(filters.Regex('^Мои заявки$'), handle_my_applications),
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND,
                       handle_question_response),
    )
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    application.add_handler(
        CallbackQueryHandler(start_new_survey, pattern="start_survey"))
    application.add_error_handler(error_handler)
    return application


if __name__ == '__main__':
    logging.info("Запуск Telegram бота.")
    bot = init_bot()
    bot.run_polling()
