import logging
from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, Depends, APIRouter
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Импорт нашей библиотеки
from models import BaseModel as SQLBaseModel, Base
from repositories.base import BaseRepository
from schemas import PaginatedSchema
from services.base import BaseService
from utils.auth import require_permission, ServicePermission, Permission
from utils.crud import crud_routers
from database import db_instance

logging.basicConfig(level=logging.DEBUG)


# Модель базы данных
class User(SQLBaseModel):
    __tablename__ = "users"

    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)


# Pydantic схемы
class UserBase(BaseModel):
    name: str
    email: str
    age: int


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None


class UserResponse(UserBase):
    id: UUID

    class Config:
        from_attributes = True


# Репозиторий для пользователей
class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)


# Сервис для пользователей
class UserService(BaseService[User, UserRepository]):
    def __init__(self, repository: UserRepository):
        super().__init__(repository)


async def get_db_session() -> AsyncSession:
    """Get database session"""
    async with db_instance.get_session() as session:
        yield session


# Фабрика сервиса
def get_user_service(db: AsyncSession = Depends(get_db_session)) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


@asynccontextmanager
async def lifecycle(*args, **kwargs):
    await db_instance.create_tables()
    yield
    await db_instance.close()


# Создание FastAPI приложения
app = FastAPI(title="API Library Example", version="1.0.0", lifespan=lifecycle)

router = APIRouter()
# Добавление CRUD роутов для пользователей
crud_routers(
    router=router,
    model=User,
    create_schema=UserCreate,
    update_schema=UserUpdate,
    single_schema=UserResponse,
    list_schema=PaginatedSchema[UserResponse],
    service_dependency=get_user_service,

    create_permission=ServicePermission(name='user', permissions=[Permission.ADMIN, Permission.WRITE]),
    read_permission=ServicePermission(name='user', no_permission=True),
    update_permissions=ServicePermission(name='user', permissions=[Permission.ADMIN, Permission.WRITE]),
    delete_permission=ServicePermission(name='user', permissions=[Permission.ADMIN, Permission.DELETE]),
)
app.include_router(router, prefix='/user')


# Дополнительный эндпоинт для демонстрации
@app.get("/")
def read_root():
    return {
        "message": "Добро пожаловать в пример API Library!",
        "endpoints": {
            "GET /users": "Получить список пользователей",
            "GET /users/{id}": "Получить пользователя по ID",
            "POST /users": "Создать нового пользователя",
            "PUT /users/{id}": "Обновить пользователя",
            "DELETE /users/{id}": "Удалить пользователя"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
