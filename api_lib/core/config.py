"""Database configuration for domain layer"""

from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration settings"""

    # Database connection settings
    driver: str = "sqlite+aiosqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "kaspi_core"
    username: str = "postgres"
    password: str = ""

    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # SQLAlchemy settings
    echo: bool = False
    echo_pool: bool = False

    # Test mode settings
    test_mode: bool = True
    test_db_path: str = "test.db"

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        case_sensitive = False

        # Field aliases for environment variables
        fields = {
            "database": {"env": "DB_NAME"},
            "username": {"env": "DB_USER"},
            "test_mode": {"env": "TEST_MODE"}
        }

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy"""
        if self.test_mode:
            # SQLite in-memory database for tests
            return f"{self.driver}:///{self.test_db_path}"
        else:
            # Regular PostgreSQL connection
            if self.password:
                return f"{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
            else:
                return f"{self.driver}://{self.username}@{self.host}:{self.port}/{self.database}"


class BaseConfig(BaseSettings):
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


database_config = DatabaseConfig()
base_config = BaseConfig()
