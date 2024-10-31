import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_ASYNC_URL')
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_factory = (
    sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False))


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Создает асинхронный контекстный менеджер для работы с сессией бд."""
    async with async_session_factory() as session:
        yield session
