from telegram import (
    ReplyKeyboardMarkup,
)


def start_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с кнопками."""
    return ReplyKeyboardMarkup(
        [['Создать заявку', 'Мои заявки', 'Мой профиль']],
        one_time_keyboard=True,
        resize_keyboard=True,
    )
