import logging
from typing import Generic, TypeVar, Optional, List, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.exc import NoResultFound

from models.base import BaseModel
from repositories.base import BaseRepository, PaginatedResult

T = TypeVar('T', bound=BaseModel)
R = TypeVar('R', bound=BaseRepository)

logger = logging.getLogger(__name__)


class BaseService(Generic[T, R]):
    """Базовый сервис с CRUD операциями"""

    def __init__(self, repository: R):
        self.repository = repository

    async def create(self, entity: T) -> T:
        """Создать новую сущность"""
        logger.debug(f"Creating new entity: {entity.__class__.__name__}")
        result = await self.repository.add(entity)
        logger.debug(f"Successfully created entity with id: {result.id}")
        return result

    async def update(self, entity: T) -> T:
        """Обновить существующую сущность"""
        logger.debug(f"Updating entity: {entity.__class__.__name__} with id: {entity.id}")
        updated_entity = await self.repository.update(entity)
        logger.debug(f"Successfully updated entity with id: {updated_entity.id}")
        return updated_entity

    async def delete(self, entity_id: UUID) -> bool:
        """Удалить сущность по идентификатору"""
        logger.debug(f"Deleting entity with id: {entity_id}")
        # Check if entity exists before deletion
        entity = await self.repository.get_by_id(entity_id)
        if not entity:
            logger.debug(f"Entity with id: {entity_id} not found for deletion")
            return False

        await self.repository.delete(entity_id)
        logger.debug(f"Successfully deleted entity with id: {entity_id}")
        return True

    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Получить сущность по идентификатору"""
        logger.debug(f"Fetching entity with id: {entity_id}")
        result = await self.repository.get_by_id(entity_id)
        if result:
            logger.debug(f"Found entity with id: {entity_id}")
        else:
            logger.debug(f"Entity with id: {entity_id} not found")
        return result

    async def get_all(self, page: Optional[int] = None, page_size: Optional[int] = None) -> List[T] | PaginatedResult:
        """Получить список всех сущностей с опциональной пагинацией

        Args:
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы (количество элементов на странице)

        Returns:
            List[T] если пагинация не используется, иначе PaginatedResult
        """
        if page is not None and page_size is not None:
            logger.debug(f"Fetching all entities with pagination: page={page}, page_size={page_size}")
        else:
            logger.debug("Fetching all entities")

        result = await self.repository.get_all(page=page, page_size=page_size)

        if isinstance(result, PaginatedResult):
            logger.debug(f"Found {result.total} total entities, returning page {result.page} of {result.total_pages}")
        else:
            logger.debug(f"Found {len(result)} entities")

        return result

    async def get_filtered(self, filters: Dict[str, Any], page: Optional[int] = None,
                           page_size: Optional[int] = None) -> List[T] | PaginatedResult:
        """Получить список сущностей с фильтрацией и опциональной пагинацией

        Args:
            filters: Словарь фильтров в формате:
                - Простые фильтры: {'field_name': value}
                - Сложные фильтры: {'field_name': {'operator': value}}
            page: Номер страницы (начиная с 1)
            page_size: Размер страницы (количество элементов на странице)

        Поддерживаемые операторы:
            - contains: содержит подстроку
            - icontains: содержит подстроку (без учета регистра)
            - starts_with: начинается с
            - ends_with: заканчивается на
            - exact: точное совпадение
            - in: значение в списке
            - gt/gte: больше/больше или равно
            - lt/lte: меньше/меньше или равно

        Примеры:
            {'name': 'Product'} - точное совпадение
            {'name': {'contains': 'prod'}} - содержит 'prod'
            {'price': {'gte': 100}} - цена >= 100

        Returns:
            List[T] если пагинация не используется, иначе PaginatedResult
        """
        if page is not None and page_size is not None:
            logger.debug(
                f"Fetching entities with filters: {filters} and pagination: page={page}, page_size={page_size}")
        else:
            logger.debug(f"Fetching entities with filters: {filters}")

        result = await self.repository.get_filtered(filters, page=page, page_size=page_size)

        if isinstance(result, PaginatedResult):
            logger.debug(
                f"Found {result.total} total entities matching filters, returning page {result.page} of {result.total_pages}")
        else:
            logger.debug(f"Found {len(result)} entities matching filters")

        return result

    async def create_or_update(self, entity: T) -> T:
        """Создать новую сущность или обновить существующую"""
        logger.debug(f"Creating or updating entity: {entity.__class__.__name__} with id: {entity.id}")
        result = await self.repository.add_or_update(entity)
        logger.debug(f"Successfully created/updated entity with id: {result.id}")
        return result


class BaseVersionalService(Generic[T, R]):

    def __init__(self, repository: R):
        self.repository = repository

    async def versional_update(self, entity: T) -> T:
        candidate = await self.repository.get_by_id(entity.id)
        if not candidate.active:
            raise NoResultFound()
        candidate.active = False
        await self.repository.update(candidate)
        entity.id = None
        entity.previous_id = candidate.id
        return await self.repository.add(entity)
