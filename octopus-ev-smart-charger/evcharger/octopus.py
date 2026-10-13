"""Octopus Energy public REST API client (unit rates need no auth)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests

from .planner import Slot

BASE = "https://api.octopus.energy/v1"


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fetch_rates(product: str, tariff: str, start: datetime, end: datetime) -> list[Slot]:
    url = f"{BASE}/products/{product}/electricity-tariffs/{tariff}/standard-unit-rates/"
    params = {
        "period_from": start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "period_to": end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "page_size": 250,
    }
    slots: list[Slot] = []
    while url:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        for row in data["results"]:
            if not row.get("valid_from"):
                continue
            slots.append(
                Slot(
                    _parse(row["valid_from"]),
                    # open-ended fixed-rate tariffs: cap at the window end
                    _parse(row["valid_to"]) if row.get("valid_to") else end,
                    float(row["value_inc_vat"]),
                )
            )
        url, params = data.get("next"), None
    return sorted(slots, key=lambda s: s.start)


def manual_windows(windows: list[dict]) -> list[Slot]:
    """Announced free sessions, expanded into half-hour slots at price 0."""
    out = []
    for w in windows:
        t, end = _parse(w["start"]), _parse(w["end"])
        while t < end:
            out.append(Slot(t, min(t + timedelta(minutes=30), end), 0.0))
            t += timedelta(minutes=30)
    return out


def merge(rates: list[Slot], free: list[Slot]) -> list[Slot]:
    """Free windows override the tariff price where they overlap."""
    freed = {s.start for s in free}
    out = [Slot(s.start, s.end, 0.0) if s.start in freed else s for s in rates]
    known = {s.start for s in rates}
    out += [s for s in free if s.start not in known]
    return sorted(out, key=lambda s: s.start)
