from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    """
        Схема Pydantic для представления данных пользователя.

        Атрибуты:
        - user_id (int): id пользователя.
        - created_at (Optional[datetime]): Дата и время создания пользователя. По умолчанию устанавливается текущее время.
        - status (str): Текущий статус пользователя. По умолчанию 'alive'.
        - status_updated_at (Optional[datetime]): Дата и время последнего обновления статуса пользователя. По умолчанию устанавливается текущее время.

        Конфигурация:
        - arbitrary_types_allowed: Разрешает использование произвольных типов данных.
        - from_attributes: Разрешает создавать экземпляры схемы из объектов с атрибутами.
        - json_encoders: Способ сериализации типов данных в JSON.
    """
    
    user_id: int
    created_at: Optional[datetime] = Field(default=datetime.utcnow())
    status: str = Field(default='alive')
    status_updated_at: Optional[datetime] = Field(default=datetime.utcnow())
    
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # Конвертация datetime в ISO формат
        }
