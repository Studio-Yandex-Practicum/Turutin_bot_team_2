from typing import Optional

import flask_admin as admin
import flask_login as login

from models import (
    AdminUser,
    Application,
    ApplicationCheckStatus,
    CheckIsBlocked,
    Question,
    User,
)

from . import app, db
from .admin_views import (
    AdminUserModelView,
    AppCheckStatusModelView,
    ApplicationModelView,
    CheckIsBlockedModelView,
    CustomAdminIndexView,
    QuestionModelView,
    UserModelView,
)


def init_login() -> None:
    """Инициализирует менеджер входа в систему."""
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: int) -> Optional[AdminUser]:
        """Загружает пользователя из базы данных."""
        return db.session.query(AdminUser).get(user_id)


init_login()

admin = admin.Admin(
    app,
    name='Turutin Bot',
    template_mode='bootstrap4',
    index_view=CustomAdminIndexView(name='Главная'),
    base_template='my_master.html',
)

admin.add_view(UserModelView(User, db.session, name='Клиенты'))
admin.add_view(ApplicationModelView(Application, db.session, name='Заявки'))
admin.add_view(AppCheckStatusModelView(ApplicationCheckStatus, db.session,
                                       name='Журнал заявок'))
admin.add_view(CheckIsBlockedModelView(CheckIsBlocked, db.session,
                                       name='Журнал блокировок'))
admin.add_view(QuestionModelView(Question, db.session, name='Вопросы'))
admin.add_view(AdminUserModelView(AdminUser, db.session,
                                  name='Сотрудники'))
