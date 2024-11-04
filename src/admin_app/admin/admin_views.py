from typing import Any, Dict

import flask_admin as admin
import flask_login as login
from flask import (
    Response,
    flash,
    redirect,
    request,
    url_for,
)
from flask_admin import expose, helpers
from flask_admin.contrib.sqla import ModelView

from .forms import LoginForm
from .utils import get_amount_opened_apps


class CustomAdminIndexView(admin.AdminIndexView):

    """Класс представления главной страницы админ-панели."""

    def is_visible(self) -> bool:
        """Cкрывает вкладку Home из меню."""
        return False

    @expose("/")
    def index(self) -> Response:
        """Проверяет, авторизован ли пользователь.

        Выводит на главную страницу сообщение о количестве открытых заявок.
        """
        if not login.current_user.is_authenticated:
            return redirect(url_for(".login_view"))
        amount = get_amount_opened_apps()
        flash(f'Количество заявок в статусе "открыта": {amount}', 'info')
        return super().index()

    @expose("/login/", methods=("GET", "POST"))
    def login_view(self) -> Response:
        """Определяет логику входа пользователя в систему."""
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)
        if login.current_user.is_authenticated:
            return redirect(url_for(".index"))
        self._template_args["form"] = form
        return super().index()

    @expose("/logout/")
    def logout_view(self) -> Response:
        """Определяет логику выхода пользователя из системы."""
        login.logout_user()
        flash('Вы вышли из системы.', 'error')
        return redirect(url_for(".index"))


class CustomModelView(ModelView):

    """Класс представления вкладок, доступных только авторизованным.

    пользователям.
    """

    def is_accessible(self) -> Response:
        """Проверяет авторизован ли пользователь."""
        return login.current_user.is_authenticated

    def inaccessible_callback(
            self, name: str, **kwargs: Dict[str, Any],
    ) -> Response:
        """Перенаправляет пользователя на страницу '/admin'."""
        flash('Вы не авторизованы. Пожалуйста, войдите в систему.', 'error')
        return redirect(url_for('admin.index'))


class SuperModelView(ModelView):

    """Класс представления вкладок, доступных только администратору."""

    def is_accessible(self) -> Response:
        """Проверяет, имеет ли текущий пользователь доступ к этой странице."""
        return (login.current_user.is_authenticated and
                login.current_user.role == 'admin')

    def inaccessible_callback(
            self, name: str, **kwargs: Dict[str, Any],
    ) -> Response:
        """Перенаправляет пользователя на страницу '/admin'."""
        return redirect(url_for('admin.index'))


class AdminUserModelView(SuperModelView):

    """Класс представления модели AdminUser."""

    column_labels = {
        'login': 'Логин',
        'password': 'Пароль',
        'role': 'Роль',
    }
    form_columns = ('login', 'password', 'role')


class UserModelView(SuperModelView):

    """Класс представления для модели User."""

    column_list = ('id', 'name', 'email', 'phone', 'is_blocked')
    column_labels = {
        'id': 'Телеграм ID',
        'name': 'Имя',
        'email': 'Электронная почта',
        'phone': 'Телефон',
        'is_blocked': 'Заблокировать',
    }
    form_columns = ('id', 'name', 'email', 'phone', 'is_blocked')


class ApplicationModelView(CustomModelView):

    """Класс представления для модели Application."""

    column_list = ('id', 'user_id', 'answers', 'status', 'comment')
    column_labels = {
        'id': 'Номер заявки',
        'user_id': 'Телеграм ID заявителя',
        'answers': 'Текст заявки',
        'status': 'Статус заявки',
        'comment': 'Комментарий',
    }
    form_columns = ('user_id', 'answers', 'status', 'comment')


class AppCheckStatusModelView(CustomModelView):

    """Класс представления для модели ApplicationCheckStatus."""

    column_list = (
        'id', 'application_id', 'old_status', 'new_status', 'timestamp',
    )
    column_labels = {
        'id': 'Номер в журнале',
        'application_id': 'Номер заявки',
        'old_status': 'Старый статус',
        'new_status': 'Новый статус',
        'timestamp': 'Дата изменений',
    }
    form_columns = (
        'application_id', 'old_status', 'new_status', 'timestamp',
    )


class QuestionModelView(SuperModelView):

    """Класс представления для модели Question."""

    column_labels = {
        'number': 'Номер',
        'question': 'Вопрос',
    }
