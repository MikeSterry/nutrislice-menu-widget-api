import os
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    timezone: str = os.getenv("APP_TIMEZONE", "America/Chicago")
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "1800"))
    nutrislice_root_url: str = os.getenv(
        "NUTRISLICE_ROOT_URL",
        "https://district196.api.nutrislice.com/menu/api/weeks/school/echo-park/menu-type/breakfast-lunch/",
    )
