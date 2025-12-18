# local_api/config.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Inventory Intel - Local API"
    api_version: str = "0.1.0"


settings = Settings()
