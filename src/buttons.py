from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def start_keyboard() -> ReplyKeyboardMarkup:
    """Создает кнопку для начала опроса."""
    keyboard = [['Начать']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def contact_keyboard() -> InlineKeyboardMarkup:
    """Создает кнопку для начала нового опроса."""
    keyboard = [[InlineKeyboardButton("Да",
                                      callback_data="start_survey")]]
    return InlineKeyboardMarkup(keyboard)


def request_contact_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для запроса номера телефона или email."""
    keyboard = [[KeyboardButton("Поделиться номером",
                                request_contact=True)],
                [KeyboardButton("Введите ваш email")]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
