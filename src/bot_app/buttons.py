from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)


def start_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с кнопками 'Создать заявку' и 'Мои заявки'."""
    return ReplyKeyboardMarkup(
        [['Создать заявку', 'Мои заявки']],
        one_time_keyboard=True, resize_keyboard=False
    )


def contact_keyboard() -> InlineKeyboardMarkup:
    """Создает кнопку для начала нового опроса."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Да", callback_data="start_survey",
                               resize_keyboard=False)]],
    )
