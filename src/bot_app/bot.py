import logging

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from telegram import Update
from telegram.ext import CallbackContext

from .buttons import request_contact_keyboard, start_keyboard
from .config import logger
from .database import get_async_db_session
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
        update: Update, context: CallbackContext,
) -> None:
    """Обработка нажатия кнопки 'Создать заявку' и запуск первого вопроса."""
    questions = await get_questions()
    if questions:
        await update.message.reply_text(questions[0]['question'])
        context.user_data['questions'] = questions
        context.user_data['current_question'] = 0
        context.user_data['started'] = True
    else:
        await update.message.reply_text('Вопросы для опроса отсутствуют.')


async def process_application(
        update: Update, context: CallbackContext,
) -> None:
    """Обработка ответов пользователя и отправка следующего вопроса."""
    user_id = str(update.message.from_user.id)
    if 'answers' not in context.user_data:
        context.user_data['answers'] = []
    context.user_data['answers'].append(update.message.text)

    await update.message.reply_text(
        f'{update.message.from_user.first_name}, ваш ответ принят.',
    )

    current_question_index = context.user_data.get('current_question', 0)
    questions = context.user_data.get('questions', [])
    context.user_data['current_question'] = current_question_index + 1

    if context.user_data['current_question'] < len(questions):
        await update.message.reply_text(
            questions[context.user_data['current_question']]['question'],
        )
    else:
        await update.message.reply_text(
            'Как с вами удобнее связаться, '
            'по электронной почте или телефону:',
        )
        context.user_data['awaiting_contact'] = True

        # Сохранение заявки в базе данных
        async with get_async_db_session() as session:
            result = await session.execute(
                select(ApplicationStatus).filter_by(status='открыта'),
            )
            status = result.scalars().first() or ApplicationStatus(
                status='открыта')
            if not status.id:
                session.add(status)
                await session.commit()

            application = Application(
                user_id=user_id,
                status_id=status.id,
                answers="; ".join(context.user_data['answers']),
            )
            session.add(application)
            await session.commit()

            logger.info(
                f'Заявка от пользователя '
                f'{update.message.from_user.first_name} '
                f'со статусом "{status.status}" сохранена.',
            )


async def handle_contact_info(
        update: Update, context: CallbackContext) -> None:
    """Обработка контактной информации пользователя."""
    user_id = str(update.message.from_user.id)
    contact_info = update.message.contact.phone_number if (
        update.message.contact) else update.message.text

    async with get_async_db_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user_record = result.scalars().first()

        if user_record:
            if "@" in contact_info:
                user_record.email = contact_info
            else:
                user_record.phone = contact_info
            await session.commit()

            # Сброс данных
            context.user_data['awaiting_contact'] = False
            context.user_data['answers'] = []
            context.user_data['current_question'] = 0

    reply_markup = start_keyboard()

    await update.message.reply_text(
        'Спасибо! Ваша контактная информация сохранена.\n'
        'Вы можете создать новую заявку или просмотреть свои заявки.',
        reply_markup=reply_markup,
    )


async def start_new_survey(update: Update, context: CallbackContext) -> None:
    """Функция для начала нового опроса после нажатия кнопки."""
    query = update.callback_query
    await query.answer()

    # Сброс ответов и параметров для нового опроса
    context.user_data['answers'] = []
    context.user_data['current_question'] = 0

    questions = context.user_data.get('questions', [])
    if questions:
        await query.message.reply_text(questions[0]['question'])


async def request_contact(update: Update, context: CallbackContext) -> None:
    """Запросить у пользователя его контакт."""
    reply_markup = request_contact_keyboard()
    await update.message.reply_text(
        'Пожалуйста, поделитесь своим номером телефона '
        'или введите ваш email:',
        reply_markup=reply_markup,
    )


async def handle_question_response(
        update: Update, context: CallbackContext,
) -> None:
    """Обработка ответов пользователя на вопросы."""
    if context.user_data.get('awaiting_contact', False):
        await handle_contact_info(update, context)
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
            await update.message.reply_text(
                'Все вопросы завершены. Спасибо за участие!',
            )
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
        # Получаем все заявки пользователя с загруженными статусами
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
            applications_text += (f"Номер: {index}. "
                                  f"Статус: {app.status.status}.\n")

        await update.message.reply_text(applications_text)
