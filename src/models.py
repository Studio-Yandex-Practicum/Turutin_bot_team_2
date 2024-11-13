import asyncio
import os
from datetime import datetime

import flask_login as login
import pytz
from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.orm import Session, declarative_base, relationship
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

Base = declarative_base()


class TimestampMixin:

    """Задаёт формат даты."""

    timestamp = Column(
        String,
        default=lambda: datetime.now(
            pytz.timezone('Europe/Moscow'),
        ).strftime('%H:%M %d.%m.%Y'),
    )


class AdminUser(Base):

    """Модель администратора."""

    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True)
    role = Column(
        Enum('admin', 'operator', name='admin_role_enum'),
        default='admin',
    )

    @property
    def is_authenticated(self) -> bool:
        """Определяет параметр 'is_authenticated'."""
        return True

    @property
    def is_active(self) -> bool:
        """Определяет параметр 'is_active'."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Определяет параметр 'is_anonymous'."""
        return False

    def get_id(self) -> int:
        """Получает id пользователя."""
        return self.id


class User(Base):

    """Модель пользователя."""

    __tablename__ = 'users'

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    phone = Column(String)
    is_blocked = Column(Boolean, default=False)

    applications = relationship(
        'Application',
        back_populates='user',
        cascade='all, delete',
    )
    block_history = relationship(
        'CheckIsBlocked',
        back_populates='user',
        cascade='all, delete',
    )

    def __repr__(self) -> str:
        """Отображает контактные данные из базы."""
        contact_info = []
        if self.phone:
            contact_info.append(self.phone)
        if self.email:
            contact_info.append(self.email)
        contact_info_str = ', '.join(contact_info)
        return f'{self.name}, {contact_info_str}'


class Application(Base):

    """Модель заявок клиента."""

    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        String,
        ForeignKey('users.id', name='fk_applications_user_id_users'),
        nullable=False,
    )
    status_id = Column(
        Integer,
        ForeignKey(
            'statuses.id',
            name='fk_applications_status_id_statuses',
        ),
        nullable=False,
    )
    answers = Column(Text, nullable=False)
    comment = Column(String)

    user = relationship(
        'User',
        back_populates='applications',
        cascade='all, delete',
    )
    status = relationship(
        'ApplicationStatus',
        back_populates='applications',
    )

    check_status = relationship(
        'ApplicationCheckStatus',
        back_populates='application',
        cascade='all, delete',
    )
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(pytz.timezone('Europe/Moscow')),
    )

    check_status = relationship(
        'ApplicationCheckStatus',
        cascade='all, delete',
    )


class ApplicationStatus(Base):

    """Модель статусов заявки."""

    __tablename__ = 'statuses'

    id = Column(Integer, primary_key=True)
    status = Column(
        Enum('открыта', 'в работе', 'закрыта', name='status_enum'),
        nullable=False,
    )

    applications = relationship('Application', back_populates='status')

    def __repr__(self) -> str:
        return f"{self.status}"


class ApplicationCheckStatus(Base, TimestampMixin):

    """Модель логов изменений статусов заявок."""

    __tablename__ = 'check_status'

    id = Column(Integer, primary_key=True)
    application_id = Column(
        Integer,
        ForeignKey(
            'applications.id',
            name='fk_check_status_application_id_applications',
        ),
        nullable=False,
    )
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, nullable=False)


    application = relationship(
        'Application',
        back_populates='check_status',
        overlaps="check_status",
    )


class Question(Base):

    """Модель вопросов."""

    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    question = Column(String, nullable=False)


class CheckIsBlocked(Base, TimestampMixin):

    """Модель истории блокировок пользователей."""

    __tablename__ = 'check_blocked'

    id = Column(Integer, primary_key=True)
    user_id = Column(
        String,
        ForeignKey('users.id', name='fk_check_blocked_user_id_users'),
        nullable=False,
    )
    user = relationship(
        'User',
        back_populates='block_history',
    )

    @property
    def name(self) -> None:
        """Получить имя пользователя."""
        return self.user.name if self.user else None

    @property
    def email(self) -> None:
        """Получить email пользователя."""
        return self.user.email if self.user else None

    @property
    def phone(self) -> None:
        """Получить телефон пользователя."""
        return self.user.phone if self.user else None


async def notify_user(user_id: int, application_id: int, old_status: str,
                      new_status: str) -> None:
    """Отправляет пользователю уведомление об изменении статуса заявки."""
    bot = Bot(token=BOT_TOKEN)
    message = f"Статус вашей заявки № {application_id} - {new_status}."
    await bot.send_message(chat_id=user_id, text=message)


async def log_status_change(session: Session, flush_context: any,
                            instances: list) -> None:
    """Логирует изменение статуса заявки и уведомляет пользователя об этом."""
    for instance in session.dirty:
        if isinstance(instance, Application):
            old_status = session.query(ApplicationStatus).get(
                instance.status_id).status
            new_status = instance.status.status

            if old_status != new_status:
                admin_user = session.query(AdminUser).get(
                    login.current_user.id)
                admin_nickname = admin_user.login

                log_entry = ApplicationCheckStatus(
                    application_id=instance.id,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=admin_nickname,
                )
                session.add(log_entry)

                await notify_user(instance.user_id, instance.id, old_status,
                                  new_status)


@event.listens_for(Session, 'before_flush')
def before_flush_handler(session: Session, flush_context: any,
                         instances: list) -> None:
    """Обрабатывает изменения статуса заявок перед сохранением."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(log_status_change(session, flush_context,
                                              instances))
    else:
        loop.run_until_complete(log_status_change(session, flush_context,
                                                  instances))


@event.listens_for(User.is_blocked, 'set')
def user_blocked_listener(target: User, value: bool,
                          oldvalue: bool, initiator: any) -> None:
    """Отражает заблокированного клиента в разделе 'История блокировок'."""
    if value and not oldvalue:
        session = Session.object_session(target)
        if session is not None:
            new_block_record = CheckIsBlocked(user_id=target.id)
            session.add(new_block_record)
            session.commit()
