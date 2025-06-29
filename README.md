# API Lib

Библиотека для быстрого создания CRUD API с использованием FastAPI и dependency injection.

## Возможности

- 🚀 Автоматическое создание CRUD маршрутов
- 💉 Dependency Injection для сервисов
- 📝 Автоматическая генерация OpenAPI документации
- 🔧 Гибкая настройка схем и моделей
- ✅ Правильные HTTP статус коды
- 🎯 Type hints и валидация с Pydantic

## Установка

### Из Git репозитория

```bash
pip install git+https://github.com/yourusername/api-lib.git
```

### Для разработки

```bash
git clone https://github.com/yourusername/api-lib.git
cd api-lib
pip install -e .
```

## Быстрый старт

```python
from fastapi import FastAPI, APIRouter
from api_lib.utils.crud import crud_routers
from your_app.services import UserService
from your_app.models import User
from your_app.schemas import UserSchema, UserListSchema, CreateUserSchema, UpdateUserSchema

app = FastAPI()
router = APIRouter()

# Функция-фабрика для создания сервиса
def get_user_service() -> UserService:
    return UserService()

# Настройка CRUD маршрутов
crud_routers(
    service_dependency=get_user_service,
    router=router,
    model=User,
    list_schema=UserListSchema,
    single_schema=UserSchema,
    create_schema=CreateUserSchema,
    update_schema=UpdateUserSchema,
    entity_name="User"
)

app.include_router(router, prefix="/users", tags=["users"])
```

## Структура проекта

```
api_lib/
├── models/          # Базовые модели
├── repositories/    # Базовые репозитории
├── schemas/         # Схемы для пагинации
├── services/        # Базовые сервисы
└── utils/
    ├── crud.py      # Основная функция для создания CRUD маршрутов
    └── schema_convertor.py  # Конвертер схем
```

## API Endpoints

Библиотека автоматически создает следующие маршруты:

- `GET /` - Получить список с пагинацией и фильтрацией
- `GET /{id}` - Получить объект по ID
- `POST /` - Создать новый объект
- `PUT /{id}` - Обновить объект
- `DELETE /{id}` - Удалить объект

## Требования

- Python 3.8+
- FastAPI
- Pydantic
- SQLAlchemy (опционально)

## Лицензия

MIT License