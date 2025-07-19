from typing import TypeVar, Optional, Type, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.params import Query
from starlette import status
from pydantic import BaseModel as PydanticBaseModel

from api_lib.services import BaseService, BaseVersionalService
from api_lib.models import Base as BaseModel
from api_lib.schemas import PaginatedSchema
from api_lib.utils.auth import TokenData, require_permission, ServicePermission
from api_lib.utils.schema_convertor import SchemaConverter

S = TypeVar('S', bound=BaseService)
VS = TypeVar('VS', bound=BaseVersionalService)
M = TypeVar('M', bound=BaseModel)
LS = TypeVar('LS', bound=PaginatedSchema)
SS = TypeVar('SS', bound=PydanticBaseModel)
CS = TypeVar('CS', bound=PydanticBaseModel)  # Create Schema
US = TypeVar('US', bound=PydanticBaseModel)  # Update Schema


def permission_2_desc(permission: ServicePermission):
    description = f"Permissions key: {permission.name}, {' or '.join(permission.permissions)}" if permission else ""
    return description


def crud_routers(service_dependency: Callable[[], S | VS],
                 router: APIRouter,
                 model: Type[M],
                 list_schema: Type[LS],
                 single_schema: Type[SS],
                 create_schema: Type[CS],
                 update_schema: Type[US],
                 entity_name: str = "Item",
                 create_permission: Optional[ServicePermission] = None,
                 read_permission: Optional[ServicePermission] = None,
                 update_permissions: Optional[ServicePermission] = None,
                 delete_permission: Optional[ServicePermission] = None
                 ):
    @router.get('/',
                response_model=list_schema,
                status_code=status.HTTP_200_OK,
                description=permission_2_desc(read_permission))
    async def get_list(
            page: int = Query(1, ge=1, description="Page number"),
            page_size: int = Query(20, ge=1, le=100, description="Items per page"),
            filters: Optional[str] = Query(None, description="Filters"),
            service: S = Depends(service_dependency),
            current_user: Optional[TokenData] = Depends(require_permission(read_permission))
    ):
        result = await service.get_filtered(filters=filters, page=page, page_size=page_size)
        return list_schema.create(items=result.items,
                                  total=result.total,
                                  page=page,
                                  page_size=page_size)

    @router.get('/{id}',
                response_model=single_schema,
                status_code=status.HTTP_200_OK,
                description=permission_2_desc(read_permission)
                )
    async def get_single(id: UUID,
                         service: S = Depends(service_dependency),
                         current_user: Optional[TokenData] = Depends(require_permission(read_permission))):
        result = await service.get_by_id(id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found"
            )
        return result

    @router.post('/',
                 response_model=single_schema,
                 status_code=status.HTTP_201_CREATED,
                 description=permission_2_desc(create_permission))
    async def create(data: create_schema,
                     service: S = Depends(service_dependency),
                     current_user: Optional[TokenData] = Depends(require_permission(create_permission))):
        data_model = SchemaConverter.schema_to_model(data, model)
        return await service.create(data_model)

    @router.put('/{id}',
                response_model=single_schema,
                status_code=status.HTTP_200_OK,
                description=permission_2_desc(update_permissions))
    async def update(id: UUID,
                     data: update_schema,
                     service: S = Depends(service_dependency),
                     current_user: Optional[TokenData] = Depends(require_permission(update_permissions))):
        candidate = await service.get_by_id(id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found"
            )
        data_model = SchemaConverter.schema_to_model(data, model, id=id)
        if getattr(service, "versional_update"):
            return await service.versional_update(data_model)
        return await service.update(data_model)

    @router.delete('/{id}',
                   status_code=status.HTTP_204_NO_CONTENT,
                   description=permission_2_desc(delete_permission))
    async def delete(id: UUID,
                     service: S = Depends(service_dependency),
                     current_user: Optional[TokenData] = Depends(require_permission(delete_permission))):
        success = await service.delete(id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found"
            )
        return None
