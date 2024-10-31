from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

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
    operator_comments = relationship(
        'ApplicationComment',
        back_populates='operator',
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

    user = relationship('User', back_populates='applications')
    status = relationship('ApplicationStatus', back_populates='applications')
    comments = relationship('ApplicationComment', back_populates='application')

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
    timestamp = Column(DateTime, default=func.now())


class ApplicationComment(Base):

    """Модель комментариев оператора к заявке."""

    __tablename__ = 'application_comments'

    id = Column(Integer, primary_key=True)
    application_id = Column(
        Integer,
        ForeignKey(
            'applications.id',
            name='fk_application_comments_application_id_applications',
        ),
        nullable=False,
    )
    operator_id = Column(
        Integer,
        ForeignKey(
            'admin_users.id',
            name='fk_application_comments_operator_id_admin_users',
        ),
        nullable=False,
    )
    comment = Column(String, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    application = relationship('Application', back_populates='comments')
    operator = relationship('AdminUser', back_populates='operator_comments')


class Question(Base):

    """Модель вопросов."""

    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    question = Column(String, nullable=False)
