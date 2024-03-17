from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SentMessageSchema(BaseModel):
    """
        Схема Pydantic для представления сообщения, отправленного пользователю.
    
        Атрибуты:
        - sent_messages_id (int): id отправленного сообщения.
        - index (int): Индекс сообщения.
        - user_id (int): id, которому отправлено сообщение.
        - message_text (Optional[str]): Текст отправленного сообщения.
        - sent_at (Optional[datetime]): Дата и время отправки сообщения.
        - is_available_sent (Optional[bool]): Флаг, указывающий, доступно ли сообщение для отправки.
        - is_sent (Optional[bool]): Флаг, указывающий, было ли сообщение отправлено.
    
        Конфигурация:
        - arbitrary_types_allowed: Разрешает использование произвольных типов данных.
        - from_attributes: Разрешает создавать экземпляры схемы из объектов с атрибутами.
        - json_encoders: Способ сериализации типов данных в JSON.
    """
    sent_messages_id: int
    index: int
    user_id: int
    message_text: Optional[str]
    sent_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    is_available_sent: Optional[bool]
    is_sent: Optional[bool]
    
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # Конвертация datetime в ISO формат
        }
