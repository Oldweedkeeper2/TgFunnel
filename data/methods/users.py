import asyncio
from typing import Optional, List

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from app.schemas.users import UserSchema
from data.models.models import AsyncSessionLocal
from data.models.models import User


class UserRepository:
    @staticmethod
    async def get_all() -> List[UserSchema]:
        """
            Асинхронно извлекает всех пользователей из базы данных.
    
            Возвращает:
            - List[UserSchema]: Список всех пользователей в форме схемы Pydantic.
    
            В случае ошибки доступа к базе данных возвращает пустой список.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
                return [UserSchema.from_orm(user) for user in users]
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while fetching all users: {e}")
            return []
    
    @staticmethod
    async def get_all_alive() -> List[UserSchema]:
        """
            Асинхронно извлекает всех активных (alive) пользователей из базы данных.

            Возвращает:
            - List[UserSchema]: Список активных пользователей в форме схемы Pydantic.

            В случае ошибки доступа к базе данных возвращает пустой список.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.status == "alive"))
                users = result.scalars().all()
                return [UserSchema.from_orm(user) for user in users]
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while fetching all alive users: {e}")
            return []
    
    @staticmethod
    async def add_user(user_data: UserSchema) -> Optional[UserSchema]:
        """
           Асинхронно добавляет нового пользователя в базу данных.

           Параметры:
           - user_data (UserSchema): Данные пользователя для добавления.

           Возвращает:
           - Optional[UserSchema]: Схема добавленного пользователя или None в случае ошибки.
       """
        try:
            async with AsyncSessionLocal() as session:
                new_user = User(**user_data.dict(exclude_unset=True))
                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)
                return UserSchema.from_orm(new_user)
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while adding a new user: {e}")
            return None
    
    @staticmethod
    async def get_by_user_id(user_id: int) -> Optional[UserSchema]:
        """
            Асинхронно извлекает пользователя по его идентификатору.

            Параметры:
            - user_id (int): id пользователя для поиска.

            Возвращает:
            - Optional[UserSchema]: Схема пользователя, если он найден, иначе None.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.user_id == user_id))
                user = result.scalars().first()
                if user:
                    return UserSchema.from_orm(user)
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while fetching user by user_id: {e}")
            return None
    
    @staticmethod
    async def update_user(update_data: UserSchema) -> UserSchema | None:
        """
            Асинхронно обновляет данные пользователя в базе данных.
        
            Параметры:
            - update_data (UserSchema): Схема пользователя с обновленными данными.
        
            Возвращает:
            - UserSchema | None: Схема обновленного пользователя или None в случае ошибки.
        
            Примечание:
            - Поля 'created_at' и 'status_updated_at' исключаются из обновления для сохранения их исходных значений.
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(User).where(User.user_id == update_data.user_id))
                user_to_update = result.scalars().first()
                if user_to_update:
                    for key, value in update_data.model_dump().items():
                        if hasattr(user_to_update, key) and key not in ['created_at', "status_updated_at"]:
                            setattr(user_to_update, key, value)
                    await session.commit()
                    return UserSchema.from_orm(user_to_update)
            return None
        except SQLAlchemyError as e:
            logger.error(f"An error occurred while updating user: {e}")
            return None
