import logging

from buttons import start_keyboard
from config import logger
from database import get_async_db_session
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import CallbackContext

from models import Application, ApplicationStatus, Question, User


async def get_questions() -> list[dict]:
    """Получает список вопросов из базы данных."""
    async with get_async_db_session() as session:
        result = await session.execute(select(Question)
                                       .order_by(Question.number))
        questions = result.scalars().all()
        return [{'number': q.number, 'question':
            q.question} for q in questions]


async def save_user_to_db(
        user_id: str, first_name: str, username: str,
) -> None:
    """Сохранение пользователя в базу данных, если его еще нет."""
    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalars().first()

        if not user:
            new_user = User(
                id=user_id, name=first_name, email=None,
                phone=None, is_blocked=False,
            )
            session.add(new_user)
            await session.commit()
            logger.info(
                f"Сохранен новый пользователь {first_name} с ID {user_id}.",
            )


async def start(update: Update, context: CallbackContext) -> None:
    """Отправка приветственного сообщения и сохранение пользователя."""
    user_id = str(update.message.from_user.id)
    first_name = update.message.from_user.first_name
    username = update.message.from_user.username
    await save_user_to_db(user_id, first_name, username)
    reply_markup = start_keyboard()
    await update.message.reply_text(
        'Добро пожаловать! Выберите нужное действие:',
        reply_markup=reply_markup,
    )


async def handle_start_button(
        update: Update, context: CallbackContext) -> None:
    """Обработка нажатия кнопки 'Создать заявку' и запуск первого вопроса."""
    questions = await get_questions()
    if questions:
        context.user_data['answers'] = []
        context.user_data['current_question'] = 0
        context.user_data['questions'] = questions
        context.user_data['started'] = True
        await update.message.reply_text(questions[0]['question'])
    else:
        await update.message.reply_text('Вопросы для опроса отсутствуют.')


async def process_application(
        update: Update, context: CallbackContext) -> None:
    """Сохраняет ответ пользователя и переходит к следующему вопросу."""
    if 'answers' not in context.user_data:
        context.user_data['answers'] = []
    if update.message:
        context.user_data['answers'].append(update.message.text)
    else:
        await update.message.reply_text("Произошла ошибка: "
                                        "сообщение не найдено.")
        return

    context.user_data['current_question'] += 1
    await ask_next_question(update, context)


async def save_application_to_db(query: CallbackQuery,
                                   context: CallbackContext,
                                   answers: str) -> None:
    """Финальное сохранение заявки в базе данных."""
    user_id = str(query.from_user.id)

    async with get_async_db_session() as session:
        result = await session.execute(
            select(ApplicationStatus).filter_by(status='открыта'),
        )
        status = result.scalars().first() or ApplicationStatus(
            status='открыта')
        if not status.id:
            session.add(status)
            await session.commit()

        # Создаём новую заявку
        application = Application(
            user_id=user_id,
            status_id=status.id,
            answers=answers,
        )
        session.add(application)
        await session.commit()

    logger.info(
        f'Заявка от пользователя {query.from_user.first_name} '
        f'подтверждена и сохранена.')
    await query.message.reply_text("Заявка успешно сохранена!")


async def handle_contact_info(
        update: Update, context: CallbackContext) -> None:
    """Обработка контактной информации пользователя и завершение заявки."""
    if not context.user_data.get('awaiting_contact'):
        return

    user_id = str(update.message.from_user.id)
    contact_info = update.message.text

    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user_record = result.scalars().first()

        if user_record:
            if "@" in contact_info:
                user_record.email = contact_info
            else:
                user_record.phone = contact_info
            await session.commit()

    context.user_data['awaiting_contact'] = False

    await finalize_application(update, context)


async def finalize_application(
        update: Update, context: CallbackContext) -> None:
    """Сохраняет заявку после получения контактной информации."""
    user_id = str(update.effective_user.id)
    answers_str = context.user_data.get('answers_str', '')

    async with get_async_db_session() as session:
        result = await session.execute(
            select(ApplicationStatus).filter_by(status='открыта'),
        )
        status = result.scalars().first() or ApplicationStatus(
            status='открыта')
        if not status.id:
            session.add(status)
            await session.commit()

        result = await session.execute(
            select(Application).filter_by(user_id=user_id),
        )
        total_applications = result.scalars().all()
        application_number = len(total_applications) + 1

        application = Application(
            user_id=user_id,
            status_id=status.id,
            answers=answers_str,
        )
        session.add(application)
        await session.commit()

    logger.info(f'Заявка от пользователя {user_id} подтверждена и сохранена.')
    await update.effective_chat.send_message(
        f"Заявка успешно сохранена! Номер вашей заявки: {application_number}",
    )


async def ask_for_contact_info(
        update: Update, context: CallbackContext) -> None:
    """Запрашивает у пользователя номер тел. или email после подтверждения."""
    await update.effective_chat.send_message(
        'Введите ваш номер телефона или email:',
    )


async def start_new_survey(update: Update, context: CallbackContext) -> None:
    """Функция для начала нового опроса после нажатия кнопки."""
    query = update.callback_query
    await query.answer()

    context.user_data['answers'] = []
    context.user_data['current_question'] = 0

    questions = await get_questions()
    context.user_data['questions'] = questions

    if questions:
        await query.message.reply_text(questions[0]['question'])


async def handle_question_response(
        update: Update, context: CallbackContext) -> None:
    """Обрабатывает ответ пользователя на вопрос."""
    if context.user_data.get('awaiting_contact', False):
        await handle_contact_info(update, context)
        return

    if 'editing_question' in context.user_data:
        question_number = context.user_data.pop('editing_question')
        answers = context.user_data.get('answers', [])
        answers[question_number - 1] = update.message.text
        context.user_data['answers'] = answers
        await summarize_answers(update, context)
        return

    user = update.message.from_user
    answer = update.message.text
    logger.info(f"Ответ пользователя {user.first_name}: {answer}")

    if 'current_question' in context.user_data:
        question_index = context.user_data['current_question']
        questions = context.user_data['questions']
        if question_index < len(questions):
            await process_application(update, context)
        else:
            await ask_for_contact_info(update, context)
    else:
        await update.message.reply_text(
            'Нажмите "Начать", чтобы начать опрос.',
        )


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработка произвольных сообщений от пользователей."""
    message = update.message.text
    logger.info(f"Получено сообщение: {message}")
    await update.message.reply_text("Ваше сообщение получено!")


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ошибки, возникающие при обработке обновлений Telegram."""
    logging.error(f"Update {update} caused error {context.error}")


async def handle_my_applications(update: Update,
                                 context: CallbackContext) -> None:
    """Обрабатывает запрос на просмотр заявок пользователя."""
    user_id = str(update.message.from_user.id)
    applications_text = "Ваши заявки:\n"

    async with get_async_db_session() as session:
        result = await session.execute(
            select(Application)
            .filter_by(user_id=user_id)
            .options(selectinload(Application.status)),
        )
        applications = result.scalars().all()

        if not applications:
            await update.message.reply_text("У вас нет заявок.")
            return

        for index, app in enumerate(applications, start=1):
            applications_text += (f"Номер: {index}.\n"
                                  f"Статус: {app.status.status}.\n\n")

        await update.message.reply_text(applications_text)


async def summarize_answers(update: Update, context: CallbackContext) -> None:
    """Показывает сводку ответов пользователя и запрашивает подтверждение."""
    questions = context.user_data.get('questions', [])
    answers = context.user_data.get('answers', [])

    if not questions or not answers:
        await update.message.reply_text("Нет ответов для подтверждения.")
        return

    summary_text = "Проверьте свои ответы:\n\n"
    for idx, question in enumerate(questions):
        answer = answers[idx] if idx < len(answers) else "Не отвечено"
        summary_text += (f"{question['number']}. "
                         f"{question['question']}\nОтвет: {answer}\n\n")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "✅ Подтвердить", callback_data="confirm_answers")],
        [InlineKeyboardButton(
            "✏️ Редактировать", callback_data="edit_answers")],
    ])

    await update.message.reply_text(summary_text, reply_markup=reply_markup)

    context.user_data['awaiting_confirmation'] = True


async def confirm_answers(update: Update, context: CallbackContext) -> None:
    """Подтверждает ответы, запрашивает контактные данные."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Ваши ответы подтверждены. "
                                  "Пожалуйста, укажите контактные данные.")

    answers = context.user_data.get('answers', [])

    answers_str = "; ".join(f"{i + 1}. {ans}" for i, ans in enumerate(answers))

    context.user_data['awaiting_contact'] = True

    context.user_data['answers_str'] = answers_str
    await ask_for_contact_info(update, context)


async def edit_answers(update: Update, context: CallbackContext) -> None:
    """Отображает список вопросов для редактирования."""
    query = update.callback_query
    await query.answer()

    questions = context.user_data.get('questions', [])
    if not questions:
        await query.edit_message_text("Нет вопросов для редактирования.")
        return

    buttons = [
        [InlineKeyboardButton(f"{q['number']}. {q['question']}",
                              callback_data=f"edit_{q['number']}")]
        for q in questions
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await query.edit_message_text("Выберите вопрос для редактирования:",
                                  reply_markup=reply_markup)


async def ask_next_question(update: Update, context: CallbackContext) -> None:
    """Выдаёт следующий вопрос из списка или показывает сводку."""
    current_question_index = context.user_data.get('current_question', 0)
    questions = context.user_data.get('questions', [])

    if current_question_index < len(questions):
        question_text = questions[current_question_index]['question']
        chat_id = update.effective_chat.id

        await context.bot.send_message(chat_id=chat_id, text=question_text)
    else:
        await summarize_answers(update, context)


async def handle_edit_choice(update: Update, context: CallbackContext) -> None:
    """Управляет выбором пользователем того, какой вопрос редактировать."""
    query = update.callback_query
    await query.answer()

    question_number = int(query.data.split('_')[1])
    questions = context.user_data.get('questions', [])
    question = next((q for q in questions if q['number'] == question_number),
                    None)

    if question:
        context.user_data['editing_question'] = question_number
        await query.edit_message_text(f"Редактируйте ответ на вопрос: "
                                      f"{question['question']}")
    else:
        await query.edit_message_text("Вопрос не найден.")