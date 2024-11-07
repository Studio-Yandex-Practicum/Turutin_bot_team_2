import asyncio
import os

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    event,
    func,
)
from sqlalchemy.orm import Session, declarative_base, relationship
from telegram import Bot

Base = declarative_base()


class AdminUser(Base):

    """Модель администратора."""

    __tablename__ = 'admin_users'

    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
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

    applications = relationship('Application', back_populates='user')

    def __repr__(self) -> str:
        return f"{self.name}"


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
    answers = Column(String, nullable=False)
    comment = Column(String)

    user = relationship('User', back_populates='applications')
    status = relationship('ApplicationStatus', back_populates='applications')

    def __repr__(self) -> str:
        user_name = self.user.name if self.user else 'Unknown User'
        status_text = self.status.status if self.status else 'Unknown Status'
        return (f"Application(user='{user_name}', status='{status_text}', "
                f"answers='{self.answers}')")


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


class ApplicationCheckStatus(Base):

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
    timestamp = Column(DateTime, default=func.date_trunc('minute', func.now()))
    user = relationship("User", secondary="applications", viewonly=True)

    @property
    def user_name(self):
        """Получает имя пользователя."""
        return self.user.name if self.user else None


class Question(Base):

    """Модель вопросов."""

    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    question = Column(String, nullable=False)


BOT_TOKEN = os.getenv('BOT_TOKEN')


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
                log_entry = ApplicationCheckStatus(
                    application_id=instance.id,
                    old_status=old_status,
                    new_status=new_status,
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
