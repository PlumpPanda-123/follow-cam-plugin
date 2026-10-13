# octopus-ev-smart-charger

Self-hosted Docker service that decides, every minute, whether your EV should be charging, based on
Octopus half-hourly prices. Built for a BYD Seal on a grid-only home (no solar) with Octopus.

**What it does**
1. Pulls half-hourly unit rates from Octopus' public API (Agile, Intelligent Go, Cosy, Go... any half-hourly tariff).
2. Reads battery % from your car and works out the kWh needed to hit `target_soc` by `ready_by`.
3. Charges in the **cheapest** slots before the deadline (with an optional price cap).
4. Charges **extra** (up to `opportunistic_soc`) in **free / negative** slots: Agile negative prices are detected automatically; announced Octoplus free sessions go in `manual_free_windows`.
5. Switches the charger on/off via Home Assistant. Ships in `dry_run` mode: it only logs until you turn that off.

## Why Home Assistant in the middle?
Direct car APIs are fragile. The Tesla-style approach (calling the car to start/stop) works because Tesla has
a stable API; BYD's cloud API is unofficial and can break. Controlling the **charger** is far more reliable, and HA
already has integrations for OCPP, Ohme, Zappi, Hypervolt, Wallbox etc. and community integrations for BYD
(used here only to *read* battery %). If the SoC can't be read, `fallback_soc` is used so it still works.

## Buying the charger (you have a month)
Pick one that is **HA-controllable and can pause/resume locally** (OCPP or a documented cloud/local API) and has
a UK-approved smart-charge-point spec (required for installs anyway). Check it against Octopus' compatibility
list if you also want Intelligent Octopus Go, which does its own scheduling for supported cars and chargers
(check whether the Seal is on that list; I could not verify it). Don't use Intelligent Go and this service
to control the same charger at once.

## Tariff choice (the main saving)
- **Intelligent Octopus Go**: simplest, fixed cheap overnight window; this service adds little unless the car/charger isn't supported.
- **Agile**: prices vary per half-hour and sometimes go negative/free; this service shines here, but your house load is also exposed to peak prices.
- Free-electricity sessions are Octoplus events announced via app/email; enter them as `manual_free_windows`.

## V2L: be realistic
V2L (up to ~3.3 kW through the adapter) powers appliances directly from the car. It is **not** vehicle-to-grid and
does not feed your house wiring or earn export payments, so it can't be scheduled for arbitrage by this service.
Useful for outages/camping/tools. (Verify the Seal's V2L/V2H capabilities for your exact trim.)

## Run
```bash
cp config.example.yaml config.yaml   # edit tariff, HA entities, car/charger specs
echo "HA_TOKEN=<home-assistant-long-lived-token>" > .env
docker compose up -d --build
docker compose logs -f               # watch decisions; status in data/status.json
```
Set `dry_run: false` once the logged plan looks right.

Tests: `pip install -r requirements-dev.txt && pytest`

## Roadmap
- Read real per-slot plan into a small web UI / HA sensor
- Octopus GraphQL for Intelligent dispatches and consumption history
- Direct OCPP central system (drop the HA dependency)
- Whole-house load shifting (dishwasher, hot water) on the same price signal
