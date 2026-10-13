"""Pure planning logic: pick which half-hour slots to charge in."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Slot:
    start: datetime
    end: datetime
    price: float  # pence/kWh inc VAT (may be <= 0)

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600


def kwh_needed(soc: float, target_soc: float, battery_kwh: float, efficiency: float) -> float:
    return max(0.0, (target_soc - soc) / 100 * battery_kwh / efficiency)


def plan(
    slots: list[Slot],
    now: datetime,
    deadline: datetime,
    soc: float,
    *,
    battery_kwh: float,
    efficiency: float,
    target_soc: float,
    opportunistic_soc: float,
    power_kw: float,
    max_price: float = 0.0,
    free_threshold: float = 0.0,
) -> list[Slot]:
    """Return slots to charge in, sorted by start.

    1. Must-have energy (to target_soc) goes in the cheapest slots before the
       deadline, ignoring slots above max_price (if set).
    2. Extra energy (up to opportunistic_soc) is added only in free slots.
    """
    usable = []
    for s in slots:
        start = max(s.start, now)
        end = min(s.end, deadline)
        if end > start:
            usable.append(Slot(start, end, s.price))

    chosen: dict[datetime, Slot] = {}

    need = kwh_needed(soc, target_soc, battery_kwh, efficiency)
    eligible = [s for s in usable if not max_price or s.price <= max_price]
    for s in sorted(eligible, key=lambda s: (s.price, s.start)):
        if need <= 1e-6:
            break
        chosen[s.start] = s
        need -= power_kw * s.hours

    extra = kwh_needed(soc, opportunistic_soc, battery_kwh, efficiency) - kwh_needed(
        soc, target_soc, battery_kwh, efficiency
    )
    for s in sorted((s for s in usable if s.price <= free_threshold), key=lambda s: s.start):
        if extra <= 1e-6:
            break
        if s.start in chosen:
            # already charging here; this slot's energy was counted toward 'need'
            continue
        chosen[s.start] = s
        extra -= power_kw * s.hours

    return sorted(chosen.values(), key=lambda s: s.start)


def slot_count_needed(kwh: float, power_kw: float) -> int:
    return math.ceil(kwh / (power_kw * 0.5))


def should_charge_now(chosen: list[Slot], now: datetime) -> bool:
    return any(s.start <= now < s.end for s in chosen)


def next_deadline(now: datetime, hhmm: str) -> datetime:
    h, m = (int(x) for x in hhmm.split(":"))
    d = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return d if d > now else d + timedelta(days=1)
