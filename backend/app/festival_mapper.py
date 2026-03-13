import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
CALENDAR_PATH = BASE_DIR / "Data" / "festival_calendar_regional.json"
STATE_CALENDAR_PATH = BASE_DIR / "Data" / "festival_calendar_state.json"

REGION_ALIASES = {
    "north": "North India",
    "north india": "North India",
    "south": "South India",
    "south india": "South India",
    "east": "East India",
    "east india": "East India",
    "west": "West India",
    "west india": "West India",
    "central": "Central India",
    "central india": "Central India",
    "northeast": "Northeast India",
    "north east": "Northeast India",
    "north-east": "Northeast India",
    "northeast india": "Northeast India",
}


def _load_calendar() -> dict[str, Any]:
    if not CALENDAR_PATH.exists():
        return {}
    with open(CALENDAR_PATH, "r", encoding="utf-8") as fp:
        return json.load(fp)


def _load_state_calendar() -> dict[str, Any]:
    if not STATE_CALENDAR_PATH.exists():
        return {}
    with open(STATE_CALENDAR_PATH, "r", encoding="utf-8") as fp:
        return json.load(fp)


def normalize_region_name(region_name: str) -> str:
    if not region_name:
        return ""
    key = " ".join(str(region_name).strip().lower().replace("_", " ").replace("-", " ").split())
    return REGION_ALIASES.get(key, region_name)


def _with_computed_fields(festival: dict[str, Any]) -> dict[str, Any]:
    item = dict(festival)
    try:
        start = datetime.strptime(item["date"], "%Y-%m-%d").date()
        dur = max(1, int(item.get("duration_days", 1)))
        end = start + timedelta(days=dur - 1)
        item["start_date"] = start.isoformat()
        item["end_date"] = end.isoformat()
        item["month"] = start.month
        item["week"] = min(4, ((start.day - 1) // 7) + 1)
    except Exception:
        pass
    return item


def get_festivals_for_region(region_name: str) -> list[dict[str, Any]]:
    calendar = _load_calendar()
    if not calendar:
        return []

    normalized = normalize_region_name(region_name)
    region_block = calendar.get(normalized)
    if not region_block:
        return []

    festivals = region_block.get("festivals", [])
    enriched = [_with_computed_fields(f) for f in festivals]
    enriched.sort(key=lambda f: f.get("date", "9999-12-31"))
    return enriched


def _unique_by_name(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    merged = []
    for item in items:
        key = (item.get("name") or "").strip().lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def get_festivals_for_context(region_name: str, state_name: str | None = None) -> list[dict[str, Any]]:
    """
    Merge state-specific + region festivals, keeping 5-6 most relevant events.
    Priority:
      1) state local festivals
      2) region local festivals
      3) pan-indian festivals
    """
    region_festivals = get_festivals_for_region(region_name)
    if not state_name:
        return region_festivals

    state_calendar = _load_state_calendar()
    state_festivals = [_with_computed_fields(f) for f in state_calendar.get(state_name, [])]

    state_local = [f for f in state_festivals if f.get("type") == "local"]
    region_local = [f for f in region_festivals if f.get("type") == "local"]
    pan = [f for f in region_festivals if f.get("type") == "pan-indian"]

    state_local = sorted(state_local, key=lambda f: (-float(f.get("impact_multiplier", 1.0)), f.get("date", "9999-12-31")))
    region_local = sorted(region_local, key=lambda f: (-float(f.get("impact_multiplier", 1.0)), f.get("date", "9999-12-31")))
    pan = sorted(pan, key=lambda f: (-float(f.get("impact_multiplier", 1.0)), f.get("date", "9999-12-31")))

    selected = []
    selected.extend(state_local[:2])

    for fest in region_local:
        if len([x for x in selected if x.get("type") == "local"]) >= 4:
            break
        if all((x.get("name") or "").lower() != (fest.get("name") or "").lower() for x in selected):
            selected.append(fest)

    diwali = next((p for p in pan if (p.get("name") or "").strip().lower() == "diwali"), None)
    if diwali and all((x.get("name") or "").lower() != "diwali" for x in selected):
        selected.append(diwali)

    for fest in pan:
        if len(selected) >= 6:
            break
        if all((x.get("name") or "").lower() != (fest.get("name") or "").lower() for x in selected):
            selected.append(fest)

    top = _unique_by_name(selected)[:6]
    top.sort(key=lambda f: f.get("date", "9999-12-31"))
    return top


def get_region_calendar(region_name: str) -> dict[str, Any]:
    calendar = _load_calendar()
    normalized = normalize_region_name(region_name)
    region_block = calendar.get(normalized)
    if not region_block:
        return {
            "region_name": normalized or region_name,
            "states": [],
            "festivals": []
        }

    return {
        "region_name": region_block.get("region_name", normalized),
        "states": region_block.get("states", []),
        "festivals": get_festivals_for_region(normalized)
    }


def get_context_calendar(region_name: str, state_name: str | None = None) -> dict[str, Any]:
    calendar = get_region_calendar(region_name)
    festivals = get_festivals_for_context(region_name, state_name)
    return {
        "region_name": calendar.get("region_name", region_name),
        "state": state_name,
        "states": calendar.get("states", []),
        "festivals": festivals
    }


def get_all_regions() -> list[str]:
    return list(_load_calendar().keys())
