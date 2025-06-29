from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

# Generic type for paginated items
T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(cls, total: int, page: int, page_size: int) -> "PaginationMeta":
        """Create pagination metadata from basic parameters"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedSchema(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T] = Field(description="List of items")
    pagination: PaginationMeta = Field(description="Pagination metadata")

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedSchema[T]":
        """Create paginated response from items and pagination parameters"""
        pagination = PaginationMeta.create(total, page, page_size)
        return cls(items=items, pagination=pagination)


# Utility functions for pagination
def calculate_offset(page: int, page_size: int) -> int:
    """Calculate offset for database queries"""
    return (page - 1) * page_size


def calculate_limit(page_size: int) -> int:
    """Calculate limit for database queries"""
    return page_size