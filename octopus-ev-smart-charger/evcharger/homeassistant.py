"""Home Assistant as the hardware abstraction.

HA already has integrations for most smart chargers (OCPP, Ohme, Zappi, Hypervolt,
Wallbox...) and for BYD vehicles (community integrations), so we only need its REST API.
"""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)


class HomeAssistant:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.h = {"Authorization": f"Bearer {token}"}

    def state(self, entity: str) -> str | None:
        r = requests.get(f"{self.url}/api/states/{entity}", headers=self.h, timeout=10)
        if r.status_code != 200:
            return None
        s = r.json().get("state")
        return None if s in ("unknown", "unavailable") else s

    def soc(self, entity: str) -> float | None:
        s = self.state(entity)
        try:
            return float(s) if s is not None else None
        except ValueError:
            return None

    def plugged_in(self, entity: str | None) -> bool:
        return True if not entity else self.state(entity) == "on"

    def set_charging(self, entity: str, on: bool) -> None:
        domain = entity.split(".")[0]
        svc = "turn_on" if on else "turn_off"
        r = requests.post(
            f"{self.url}/api/services/{domain}/{svc}",
            headers=self.h, json={"entity_id": entity}, timeout=10,
        )
        r.raise_for_status()
