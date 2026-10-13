from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from . import octopus
from .homeassistant import HomeAssistant
from .planner import next_deadline, plan, should_charge_now

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("evcharger")


def main() -> None:
    cfg = yaml.safe_load(Path(os.environ.get("CONFIG", "config.yaml")).read_text())
    oc, car, ch, ha_cfg = cfg["octopus"], cfg["car"], cfg["charger"], cfg["home_assistant"]
    dry = cfg.get("dry_run", True)
    ha = HomeAssistant(ha_cfg["url"], os.environ.get("HA_TOKEN", ""))
    free = octopus.manual_windows(oc.get("manual_free_windows") or [])
    state_file = Path("data/status.json")
    state_file.parent.mkdir(exist_ok=True)
    rates, fetched = [], datetime.min.astimezone()
    last_cmd: bool | None = None
    log.info("Started (dry_run=%s)", dry)

    while True:
        try:
            now = datetime.now().astimezone()
            deadline = next_deadline(now, car["ready_by"])
            if now - fetched > timedelta(minutes=30) or not rates:
                rates = octopus.fetch_rates(
                    oc["product_code"], oc["tariff_code"], now - timedelta(hours=1), now + timedelta(hours=36)
                )
                fetched = now
            slots = octopus.merge(rates, free)

            soc = ha.soc(ha_cfg["car_soc_sensor"])
            if soc is None:
                soc = car["fallback_soc"]
                log.warning("SoC unavailable, assuming %s%%", soc)
            plugged = ha.plugged_in(ha_cfg.get("car_plugged_in"))

            chosen = plan(
                slots, now, deadline, soc,
                battery_kwh=car["battery_kwh"], efficiency=car["charge_efficiency"],
                target_soc=car["target_soc"], opportunistic_soc=car["opportunistic_soc"],
                power_kw=ch["power_kw"], max_price=ch.get("max_price_p_per_kwh", 0),
                free_threshold=ch.get("free_threshold_p", 0.0),
            )
            want = plugged and should_charge_now(chosen, now)
            if want != last_cmd:
                log.info("charging=%s soc=%s%% plugged=%s planned_slots=%d", want, soc, plugged, len(chosen))
                if not dry:
                    ha.set_charging(ha_cfg["charger_switch"], want)
                last_cmd = want
            state_file.write_text(json.dumps({
                "updated": now.isoformat(), "soc": soc, "plugged": plugged, "charging": want,
                "plan": [{"start": s.start.isoformat(), "end": s.end.isoformat(), "p_per_kwh": s.price} for s in chosen],
            }, indent=2))
        except Exception:
            log.exception("loop error (will retry)")
        time.sleep(cfg.get("poll_seconds", 60))


if __name__ == "__main__":
    main()
