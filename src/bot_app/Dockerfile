FROM python:3.11-slim

WORKDIR /app

COPY ./src/bot_app /app
COPY ./src/models.py /app/models.py

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]