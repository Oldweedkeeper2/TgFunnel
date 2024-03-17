from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.logger import logger
from app.schemas.sent_messages import SentMessageSchema
from data.models.models import AsyncSessionLocal, SentMessage


class SentMessageRepository:
    @staticmethod
    async def add_message(message_data: SentMessage) -> bool:
        """
            Асинхронно добавляет новое сообщение в базу данных.
    
            Параметры:
            - message_data (SentMessage): Данные сообщения для добавления.
    
            Возвращает:
            - bool: True, если сообщение успешно добавлено, иначе False.
        """
        try:
            async with AsyncSessionLocal() as session:
                session.add(message_data)
                await session.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while adding a new message: {e}")
            return False
    
    @staticmethod
    async def update_status(user_id: int, index: int, is_sent: bool,
                            is_available_sent: bool) -> bool:
        """
            Асинхронно обновляет статус отправленного сообщения.

            Параметры:
            - user_id (int): id пользователя, которому отправлено сообщение.
            - index (int): Индекс отправленного сообщения.
            - is_sent (bool): Флаг, указывающий, было ли сообщение отправлено.
            - is_available_sent (bool): Флаг, указывающий, доступно ли сообщение для отправки.

            Возвращает:
            - bool: True, если статус сообщения успешно обновлен, иначе False.
        """
        try:
            async with AsyncSessionLocal() as session:
                # Находим сообщение по user_id и index
                result = await session.execute(
                        select(SentMessage)
                        .where(SentMessage.user_id == user_id, SentMessage.index == index)
                )
                message = result.scalars().first()
                
                if message:
                    message.is_sent = is_sent
                    message.is_available_sent = is_available_sent
                    await session.commit()
                    logger.info(
                            f"Message status updated for user_id={user_id}, index={index}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while updating message status: {e}")
            return False
    
    @staticmethod
    async def fetch_pending(user_id: int) -> SentMessageSchema | None:
        """
            Асинхронно извлекает ожидающее отправки сообщение для пользователя.

            Параметры:
            - user_id (int): id пользователя.

            Возвращает:
            - SentMessageSchema | None: Схема ожидающего сообщения или None, если таких сообщений нет.
        """
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.utcnow()
                result = await session.execute(
                        select(SentMessage)
                        .where(SentMessage.user_id == user_id,
                               SentMessage.sent_at <= now,
                               SentMessage.is_available_sent == True,
                               SentMessage.is_sent == False)
                        .order_by(SentMessage.sent_at)
                        .limit(1)
                )
                message = result.scalars().first()
                if message is not None:
                    return SentMessageSchema.from_orm(message)
                else:
                    return None
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while fetching messages to send for user {user_id}: {e}")
            return None
    
    @staticmethod
    async def mark_unavailable(user_id: int, index: int) -> bool:
        """
            Асинхронно помечает сообщение как недоступное для отправки.

            Параметры:
            - user_id (int): Идентификатор пользователя, которому отправлено сообщение.
            - index (int): Порядковый номер сообщения в последовательности отправки.

            Возвращает:
            - bool: True, если сообщение успешно помечено как недоступное, иначе False.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                        select(SentMessage)
                        .where(SentMessage.user_id == user_id, SentMessage.index == index)
                )
                message = result.scalars().first()
                
                if message:
                    message.is_available_sent = False
                    await session.commit()
                    logger.debug(f"Message marked as unavailable for user_id={user_id}, index={index}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while marking message as unavailable: {e}")
            return False
    
    @staticmethod
    async def update_third_message_time(sent_message_data: SentMessageSchema) -> bool:
        """
            Асинхронно обновляет время отправки третьего сообщения для пользователя.

            Параметры:
            - sent_message_data (SentMessageSchema): Данные сообщения, включая новое время отправки.

            Возвращает:
            - bool: True, если время отправки успешно обновлено, иначе False.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                        select(SentMessage)
                        .where(SentMessage.user_id == sent_message_data.user_id, SentMessage.index == 3)
                )
                third_message = result.scalars().first()
                
                if third_message:
                    third_message.sent_at = sent_message_data.sent_at
                    await session.commit()
                    logger.debug(
                            f"Updated sent_at for the third message for user_id={sent_message_data.user_id} to {third_message.sent_at}")
                    return True
                return False
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while updating the third message time: {e}")
            return False
