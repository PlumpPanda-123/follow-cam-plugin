from datetime import datetime, timedelta, timezone

from evcharger.octopus import manual_windows, merge
from evcharger.planner import Slot, plan, should_charge_now

T0 = datetime(2026, 11, 1, 22, 0, tzinfo=timezone.utc)
KW = dict(battery_kwh=80, efficiency=1.0, target_soc=80, opportunistic_soc=100, power_kw=8)


def slots(prices):
    return [Slot(T0 + timedelta(minutes=30 * i), T0 + timedelta(minutes=30 * (i + 1)), p) for i, p in enumerate(prices)]


def test_picks_cheapest_slots():
    s = slots([30, 5, 20, 4, 25, 6, 10, 12])  # need 8kWh from 72->80? soc 70 -> 8kWh = 2 slots
    c = plan(s, T0, T0 + timedelta(hours=4), 70, **KW)
    assert [x.price for x in c] == [5, 4]


def test_respects_deadline_and_cap():
    s = slots([40, 40, 1, 1])
    c = plan(s, T0, T0 + timedelta(hours=1), 70, max_price=25, **KW)
    assert c == []  # cheap slots are after deadline, rest above cap


def test_free_slots_top_up_beyond_target():
    s = slots([30, -2, -1, 30])
    c = plan(s, T0, T0 + timedelta(hours=2), 80, **KW)  # already at target
    assert [x.price for x in c] == [-2, -1]


def test_no_charge_when_full():
    assert plan(slots([-5, -5]), T0, T0 + timedelta(hours=1), 100, **KW) == []


def test_should_charge_now():
    c = plan(slots([1, 50]), T0, T0 + timedelta(hours=1), 76, **KW)
    assert should_charge_now(c, T0 + timedelta(minutes=10))
    assert not should_charge_now(c, T0 + timedelta(minutes=40))


def test_manual_free_window_overrides_price():
    rates = slots([30, 30, 30])
    free = manual_windows([{"start": (T0 + timedelta(minutes=30)).isoformat(), "end": (T0 + timedelta(hours=1)).isoformat()}])
    assert [s.price for s in merge(rates, free)] == [30, 0.0, 30]
