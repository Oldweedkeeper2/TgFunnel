import asyncio
from datetime import datetime

from sqlalchemy import Column, DateTime, String, BigInteger, Boolean, ForeignKey, Integer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from app.logger import logger
from config import DATABASE_URL

Base = declarative_base()


class User(Base):
    """
        Модель SQLAlchemy для представления пользователя.

        Атрибуты:
        - user_id (BigInteger): id пользователя.
        - created_at (DateTime): Дата и время создания записи пользователя.
        - status (String): Статус пользователя (alive, dead, finished).
        - status_updated_at (DateTime): Дата и время последнего обновления статуса пользователя.

        Связи:
        - sent_messages: Связь с моделью отправленных сообщений.
    """
    __tablename__ = 'users'
    user_id = Column(BigInteger,
                     primary_key=True)
    created_at = Column(DateTime,
                        default=datetime.utcnow,
                        nullable=False)  # TODO: Нужно учесть часовой пояс России
    status = Column(String,
                    nullable=False,
                    default='alive')
    status_updated_at = Column(DateTime,
                               nullable=False,
                               default=datetime.utcnow,
                               onupdate=datetime.utcnow)
    sent_messages = relationship("SentMessage", back_populates="user")
    
    def __repr__(self):
        return f'<User(user_id={self.user_id}, status={self.status})>'


class SentMessage(Base):
    """
            Модель SQLAlchemy для представления сообщения, отправленного пользователю.
        
            Атрибуты:
            - sent_messages_id (Integer): id отправленного сообщения.
            - index (Integer): Порядковый номер сообщения в последовательности отправки.
            - user_id (BigInteger): id пользователя, которому отправлено сообщение.
            - message_text (String): Текст отправленного сообщения.
            - sent_at (DateTime): Дата и время отправки сообщения.
            - is_available_sent (Boolean): Флаг, указывающий, доступно ли сообщение для отправки.
            - is_sent (Boolean): Флаг, указывающий, было ли сообщение отправлено.
        
            Связи:
            - user: Связь с моделью пользователя.
    """
    __tablename__ = 'sent_messages'
    sent_messages_id = Column(Integer, primary_key=True)
    index = Column(Integer, nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    message_text = Column(String, nullable=False)
    sent_at = Column(DateTime,
                     nullable=False)
    is_available_sent = Column(Boolean, default=True, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    
    user = relationship("User", back_populates="sent_messages")
    
    def __repr__(self):
        return f'<SentMessage(sent_messages_id={self.sent_messages_id}, user_id={self.user_id}, sent_at={self.sent_at}, sent={self.is_sent}, available={self.is_available_sent}, index={self.index}, message_text={self.message_text})>'


engine = create_async_engine(
        DATABASE_URL,
        echo=False,  # DEBUG  # включает логирование SQL-запросов (для отладки).
        pool_size=10,  # Минимальное количество соединений в пуле
        max_overflow=50  # Максимальное количество соединений в пуле
)
AsyncSessionLocal = sessionmaker(  # noqa
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)  # DEBUG MODE/ # TODO: удалить после отладки
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        logger.info('Tables created')


if __name__ == '__main__':
    asyncio.run(create_tables())
