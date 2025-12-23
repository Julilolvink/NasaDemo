import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # EONET v3 base URL (docs)
    EONET_BASE_URL: str = os.getenv("EONET_BASE_URL", "https://eonet.gsfc.nasa.gov/api/v3")
    NASA_API_KEY: str | None = os.getenv("NASA_API_KEY") or None

    # HTTP settings
    HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "15"))
    HTTP_RETRIES: int = int(os.getenv("HTTP_RETRIES", "3"))
    HTTP_BACKOFF_SECONDS: float = float(os.getenv("HTTP_BACKOFF_SECONDS", "0.7"))


settings = Settings()
