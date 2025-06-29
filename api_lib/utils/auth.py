from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from api_lib.core.config import base_config


class Permission(str, Enum):
    """Базовые разрешения системы"""
    READ = "read"
    WRITE = "write"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN = "admin"


class ServicePermission(BaseModel):
    name: str
    permissions: List[Permission] = Field(default_factory=list)
    no_permission: Optional[bool] = False


class TokenData(BaseModel):
    """Данные JWT токена"""
    user_id: str
    username: str
    service_permissions: List[ServicePermission]
    exp: datetime
    iat: datetime


class JWTAuth:
    """Класс для работы с JWT аутентификацией и авторизацией"""

    def __init__(self, secret_key: str, algorithm: str = "HS256", access_token_expire_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.security = HTTPBearer()

    def create_access_token(self,
                            user_id: str,
                            username: str,
                            service_permissions: List[ServicePermission]) -> str:
        """Создание JWT токена"""

        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        # Сериализуем service_permissions для JWT payload
        serialized_permissions = [
            {
                "name": perm.name,
                "permissions": [p.value for p in perm.permissions],
            }
            for perm in service_permissions
        ]

        payload = {
            "user_id": user_id,
            "username": username,
            "service_permissions": serialized_permissions,
            "exp": expire,
            "iat": now
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenData:
        """Проверка и декодирование JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id = payload.get("user_id")
            username = payload.get("username")
            service_permissions = payload.get("service_permissions", [])
            exp = datetime.fromtimestamp(payload.get("exp"))
            iat = datetime.fromtimestamp(payload.get("iat"))

            if not user_id or not username:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            # Десериализуем service_permissions из JWT payload
            deserialized_permissions = []
            for perm in service_permissions:
                deserialized_permissions.append(ServicePermission(
                    name=perm["name"],
                    permissions=[Permission(p) for p in perm["permissions"]],
                ))

            return TokenData(
                user_id=user_id,
                username=username,
                service_permissions=deserialized_permissions,
                exp=exp,
                iat=iat
            )

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> TokenData:
        """Dependency для получения текущего пользователя из токена"""
        return self.verify_token(credentials.credentials)

    def require_permission(self, required_permission: ServicePermission):
        """Decorator для проверки разрешений"""

        def permission_checker(current_user: TokenData = Depends(self.get_current_user)) -> TokenData:
            service_permission = next(
                (perm for perm in current_user.service_permissions if perm.name == required_permission.name), None)
            if not service_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{' or '.join([p.value for p in required_permission.permissions])}' required"
                )
            required_perms = required_permission.permissions
            service_perms = service_permission.permissions
            has_all_permissions = any(perm in service_perms for perm in required_perms)
            if not has_all_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{' or '.join([p.value for p in required_permission.permissions])}' required"
                )
            return current_user

        return permission_checker


jwt_auth = JWTAuth(
    secret_key=base_config.secret_key,
    algorithm=base_config.algorithm,
    access_token_expire_minutes=base_config.access_token_expire_minutes
)


# Удобные функции для использования
def get_current_user() -> TokenData:
    """Получить текущего пользователя"""
    return Depends(jwt_auth.get_current_user)


def require_permission(permission: Optional[ServicePermission]):
    """Требовать определенное разрешение"""
    if not permission:
        return jwt_auth.get_current_user
    if permission.no_permission:
        return lambda: None
    return jwt_auth.require_permission(permission)


if __name__ == '__main__':
    print(jwt_auth.create_access_token("123", "moderator", [
        ServicePermission(name='user', permissions=[Permission.READ, Permission.WRITE])
    ]))
