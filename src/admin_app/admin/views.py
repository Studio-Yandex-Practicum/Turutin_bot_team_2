from flask import Response, jsonify, redirect, url_for

from . import app
from .utils import get_amount_new_apps


@app.route('/')
def index() -> Response:
    """Перенаправляет пользователя на страницу '/admin'."""
    return redirect(url_for('admin.index'))


@app.route('/api/new_applications', methods=['GET'])
def new_applications() -> Response:
    """Возвращает информацию о количестве новых заявок за.

    последние 10 секунд в формате json.
    """
    new_applications = get_amount_new_apps()
    return jsonify({'new_applications': new_applications})
