import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message

from app.schemas.sent_messages import SentMessageSchema
from app.schemas.status import Status
from app.schemas.users import UserSchema
from app.logger import logger
from config import API_ID, API_HASH, API_NAME, TRIGGER_WORDS, MESSAGES
from data.methods.sent_messages import SentMessageRepository
from data.methods.users import UserRepository
from data.models.models import SentMessage


app = Client(name=API_NAME,
             api_id=API_ID,
             api_hash=API_HASH,
             workdir="sessions")


async def send_message(user_id: int, text: str) -> None:
    """
        Асинхронно отправляет текстовое сообщение пользователю.
    
        Параметры:
        - user_id (int): id пользователя, которому будет отправлено сообщение.
        - text (str): Текст сообщения для отправки.
    
        При срабатывании исключения, обновляет статус пользователя на 'dead'. Например, UserDeactivated.
    """
    try:
        await app.send_message(user_id, text)
        logger.info(f"Message sent to user {user_id}: {text}")
    except Exception as e:
        await UserRepository.update_user(UserSchema(user_id=user_id, status=Status.dead.value))
        logger.error(f"An error occurred while sending a message to user {user_id}: {e}")


async def send_messages_loop() -> None:
    """
        Асинхронный бесконечный цикл, который каждую минуту проверяет наличие активных пользователей
        и отправляет им ожидающие сообщения.
    
        Для каждого активного пользователя функция ищет ожидающие сообщения и отправляет их.
        После успешной отправки сообщения, обновляет статус сообщения на 'sent'.
        Если сообщение является последним в цепочке, обновляет статус пользователя на 'finished'.
    """
    while True:
        users = await UserRepository.get_all_alive()
        if users:
            logger.debug(f"Processing {len(users)} alive users.")
        for user in users:
            message_to_send = await SentMessageRepository.fetch_pending(user.user_id)
            logger.debug(f"Found {message_to_send} messages to send for user {user.user_id}.")
            if message_to_send:
                await send_message(user.user_id, message_to_send.message_text)
                await SentMessageRepository.update_status(
                        user.user_id, message_to_send.index, is_sent=True, is_available_sent=True
                )
                logger.info(
                        f"Sent message index {message_to_send.index} to user {user.user_id},"
                        f" message_text: {message_to_send.message_text}")
                if message_to_send.index == 3:
                    await UserRepository.update_user(UserSchema(user_id=user.user_id, status=Status.finished.value))
                    logger.info(f"User {user.user_id} finished.")
            else:
                logger.debug(f"No messages to send for user {user.user_id} at this time.")
        
        await asyncio.sleep(10)


async def get_or_add_user_in_db(user_id: int) -> UserSchema:
    """
        Асинхронно проверяет наличие пользователя в базе данных по его id.
        Если пользователь найден, возвращает его данные. В противном случае создает нового пользователя
        с указанным id и добавляет начальные сообщения для него.
    
        Параметры:
        - user_id (int): id пользователя для поиска или добавления.
    
        Возвращает:
        - UserSchema: Схема данных пользователя.
    
        В случае возникновения исключения при добавлении нового пользователя, логгирует ошибку.
    """
    try:
        user = await UserRepository.get_by_user_id(user_id)
        if not user:
            user = await UserRepository.add_user(UserSchema(user_id=user_id))
            await add_initial_messages_for_user(user_id)
            logger.debug(f"New user {user_id} added and initialized.")  # Сокращаем количество логов
        return user
    except Exception as e:
        logger.error(f"An error occurred while processing user {user_id}: {e}")


async def add_initial_messages_for_user(user_id: int):
    """
        Асинхронно добавляет начальные сообщения для нового пользователя в базу данных.
    
        Параметры:
        - user_id (int): id пользователя, для которого добавляются начальные сообщения.
    
        Для каждого сообщения из предопределенного списка MESSAGES вычисляет время отправки,
        добавляет сообщение в базу данных, где is_sent = False.
    """
    now = datetime.utcnow()
    try:
        for message in MESSAGES:
            index = message["index"]
            delay = message["delay"]
            text = message["text"]
            
            sent_message = SentMessage(
                    user_id=user_id,
                    message_text=text,
                    index=index,
                    sent_at=now + delay,
                    is_available_sent=True,
                    is_sent=False
            )
            await SentMessageRepository.add_message(sent_message)
            logger.debug(f"Initial message {index} added for user {user_id}.")
    except Exception as e:
        logger.error(f"An error occurred while adding initial messages for user {user_id}: {e}")


@app.on_message(filters.text & filters.private)
async def message_handler(client: Client, message: Message):
    """
        Обработчик входящих текстовых сообщений от пользователей.
    
        Параметры:
        - client (Client): Экземпляр клиента бота.
        - message (Message): Объект сообщения, полученного от пользователя.
    
        Для каждого входящего сообщения функция определяет, является ли сообщение исходящим или входящим.
        Если исходящее, то проверяет наличие пользователя в базе данных и обрабатывает триггеры,
        если они присутствуют в тексте сообщения.
    """
    user_id = message.from_user.id
    logger.debug(f"User {user_id} sent a message: {message.text}")
    if not message.outgoing:
        await get_or_add_user_in_db(user_id)
    else:
        user = await UserRepository.get_by_user_id(message.chat.id)
        logger.debug(f"User {user} found in the database.")
        if user and user.status == Status.alive.value:
            logger.debug(f"User {user_id} is alive.")
            await handle_trigger_for_user(user.user_id, message.text)


async def handle_trigger_for_user(user_id: int, text: str):
    """
        Обрабатывает триггеры в тексте сообщения пользователя.
    
        Параметры:
        - user_id (int): id пользователя, отправившего сообщение.
        - text (str): Текст сообщения для анализа на наличие триггеров.
    
        Если в тексте сообщения есть одно из триггерных слов, то
        помечаем сообщение с индексом 2 в базе данных как недоступное.
    """
    if any(trigger_word in text for trigger_word in TRIGGER_WORDS):
        try:
            await SentMessageRepository.mark_unavailable(user_id, 2)
            event_time = datetime.utcnow() + MESSAGES[2]["delay"]
            await SentMessageRepository.update_third_message_time(SentMessageSchema(user_id=user_id, index=2, sent_at=event_time))
            logger.info(f"Trigger processed for user {user_id}.")
        except Exception as e:
            logger.error(f"Error processing trigger for user {user_id}: {e}")
