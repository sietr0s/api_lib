from uuid import UUID
from typing import Generic, TypeVar, Optional, List, Dict, Any, NamedTuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, asc, desc

from api_lib.models import BaseModel


class PaginatedResult(NamedTuple):
    """Результат пагинации"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """Базовая реализация репозитория"""

    def __init__(self, session: AsyncSession, model_class):
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Получить сущность по идентификатору"""
        query = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self,
                      page: Optional[int] = None,
                      page_size: Optional[int] = None,
                      order_by: Optional[Union[str, List[str]]] = None) -> List[T] | PaginatedResult:
        """Получить все сущности с опциональной пагинацией и сортировкой"""
        query = select(self.model_class)

        # Применяем сортировку
        query = self._apply_ordering(query, order_by)

        if page is not None and page_size is not None:
            return await self._paginate_query(query, page, page_size)

        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_filtered(self,
                           filters: Dict[str, Any],
                           page: Optional[int] = None,
                           page_size: Optional[int] = None,
                           order_by: Optional[Union[str, List[str]]] = None) -> List[T] | PaginatedResult:
        """Получить сущности с фильтрацией, опциональной пагинацией и сортировкой"""
        query = select(self.model_class)

        if filters:
            conditions = []
            for field_name, filter_value in filters.items():
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)

                    if isinstance(filter_value, dict):
                        # Сложные фильтры
                        if 'contains' in filter_value:
                            conditions.append(field.contains(filter_value['contains']))
                        elif 'starts_with' in filter_value:
                            conditions.append(field.startswith(filter_value['starts_with']))
                        elif 'ends_with' in filter_value:
                            conditions.append(field.endswith(filter_value['ends_with']))
                        elif 'icontains' in filter_value:
                            conditions.append(field.ilike(f"%{filter_value['icontains']}%"))
                        elif 'exact' in filter_value:
                            conditions.append(field == filter_value['exact'])
                        elif 'in' in filter_value:
                            conditions.append(field.in_(filter_value['in']))
                        elif 'gt' in filter_value:
                            conditions.append(field > filter_value['gt'])
                        elif 'gte' in filter_value:
                            conditions.append(field >= filter_value['gte'])
                        elif 'lt' in filter_value:
                            conditions.append(field < filter_value['lt'])
                        elif 'lte' in filter_value:
                            conditions.append(field <= filter_value['lte'])
                    else:
                        # Простое равенство
                        conditions.append(field == filter_value)

            if conditions:
                query = query.where(and_(*conditions))

        # Применяем сортировку
        query = self._apply_ordering(query, order_by)

        if page is not None and page_size is not None:
            return await self._paginate_query(query, page, page_size)

        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def add(self, entity: T) -> T:
        """Добавить новую сущность"""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        """Обновить существующую сущность"""
        merged_entity = await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(merged_entity)
        return merged_entity

    async def delete(self, id: UUID) -> None:
        """Удалить сущность по идентификатору"""
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()

    async def add_or_update(self, entity: T) -> T:
        existing_entity = await self.get_by_id(entity.id)
        if existing_entity:
            return await self.update(entity)
        return await self.add(entity)

    def _apply_ordering(self, query, order_by: Optional[Union[str, List[str]]]) -> Any:
        """Применить сортировку к запросу"""
        if not order_by:
            return query

        order_fields = order_by if isinstance(order_by, list) else [order_by]

        for field_spec in order_fields:
            if isinstance(field_spec, str):
                # Определяем направление сортировки
                if field_spec.startswith('-'):
                    field_name = field_spec[1:]
                    direction = desc
                else:
                    field_name = field_spec
                    direction = asc

                # Проверяем, что поле существует в модели
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    query = query.order_by(direction(field))

        return query

    async def _paginate_query(self, query, page: int, page_size: int) -> PaginatedResult:
        """Применить пагинацию к запросу"""
        # Валидация параметров
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 1000:  # Ограничение максимального размера страницы
            page_size = 1000

        # Подсчет общего количества записей
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Вычисление метаданных пагинации
        total_pages = (total + page_size - 1) // page_size  # Округление вверх
        offset = (page - 1) * page_size

        # Применение LIMIT и OFFSET
        paginated_query = query.offset(offset).limit(page_size)
        result = await self.session.execute(paginated_query)
        items = result.unique().scalars().all()

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
