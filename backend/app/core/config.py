"""Application settings (base product)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI SDR Customer Architecture POC"
    database_url: str = (
        "mysql+pymysql://poc:pocpass@db:3306/generic?charset=utf8mb4"
    )
    # Shared tenant-catalog database (not customer lead data).
    platform_database: str = "generic"
    run_migrations_on_startup: bool = True
    # Comma-separated host → customer_id mappings (mirrors frontend HOST_BACKEND_MAP)
    customer_host_map: str = (
        "customer-1.localhost:customer-1,"
        "customer-2.localhost:customer-2,"
        "customer-3.localhost:customer-3"
    )
    default_customer_id: str = "customer-3"
    # Celery / Redis (replaces in-process APScheduler from AI_SDR CampaignManagement)
    redis_url: str = "redis://redis:6379/0"
    celery_task_always_eager: bool = False

    def host_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for pair in self.customer_host_map.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            host, customer_id = pair.split(":", 1)
            mapping[host.strip().lower()] = customer_id.strip()
        return mapping


@lru_cache
def get_settings() -> Settings:
    return Settings()
