from typing import TypeVar, Type
from pydantic import BaseModel

from models.base import Base

T = TypeVar('T', bound=Base)
S = TypeVar('S', bound=BaseModel)


class SchemaConverter:
    """Утилита для преобразования схем API в доменные модели и обратно"""

    @staticmethod
    def schema_to_model(schema: BaseModel, model_class: Type[T], **extra_fields) -> T:
        """Преобразовать схему API в доменную модель

        Args:
            schema: Схема API (например, ProductCreate)
            model_class: Класс доменной модели (например, Product)
            **extra_fields: Дополнительные поля для модели

        Returns:
            Экземпляр доменной модели
        """
        # Получаем данные из схемы
        schema_data = schema.model_dump(exclude_unset=True)

        # Добавляем дополнительные поля
        schema_data.update(extra_fields)

        # Создаем экземпляр доменной модели
        return model_class(**schema_data)

    @staticmethod
    def update_model_from_schema(model: T, schema: BaseModel) -> T:
        """Обновить доменную модель данными из схемы

        Args:
            model: Существующая доменная модель
            schema: Схема с данными для обновления

        Returns:
            Обновленная доменная модель
        """
        # Получаем данные из схемы, исключая неустановленные поля
        update_data = schema.model_dump(exclude_unset=True)

        # Обновляем поля модели
        for field, value in update_data.items():
            if hasattr(model, field):
                setattr(model, field, value)

        return model