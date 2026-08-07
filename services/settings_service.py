from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from services.google_sheets_service import append_record, find_record, json_text, parse_json, update_record

DEFAULT_DASHBOARD_SETTINGS: dict[str, Any] = {
    "surge_threshold": 10000, "match_threshold": 70, "yesterday_max": 500,
    "collection_start": None, "collection_end": None, "schedule_mode": "daily",
    "schedule_times": ["09:00"], "alert_enabled": False, "alert_channel": "teams",
}
DEFAULT_RETENTION = {"days": 90, "max_records": 1000}
ALLOWED_KEYS = {"dashboard", "retention"}
DESCRIPTIONS = {"dashboard": "분석 기준과 수집·알림 설정", "retention": "분석 결과 보관 정책"}


def _validate(key: str, value: dict) -> dict:
    if key == "retention":
        return {"days": max(1, min(int(value.get("days", 90)), 3650)),
                "max_records": max(10, min(int(value.get("max_records", 1000)), 100000))}
    if key == "dashboard":
        clean = {item: value.get(item, default) for item, default in DEFAULT_DASHBOARD_SETTINGS.items()}
        clean["surge_threshold"] = max(1, int(clean["surge_threshold"]))
        clean["match_threshold"] = max(0, min(int(clean["match_threshold"]), 100))
        clean["yesterday_max"] = max(0, int(clean["yesterday_max"]))
        clean["schedule_times"] = [str(item)[:5] for item in clean.get("schedule_times", []) if str(item)] or ["09:00"]
        clean["alert_channel"] = "teams"
        return clean
    raise ValueError("허용되지 않은 설정입니다.")


def get_setting(key: str) -> dict:
    if key not in ALLOWED_KEYS:
        raise ValueError("허용되지 않은 설정입니다.")
    found = find_record("settings", "key", key)
    default = DEFAULT_RETENTION if key == "retention" else DEFAULT_DASHBOARD_SETTINGS
    return _validate(key, parse_json(found[1].get("value_json", ""), default)) if found else deepcopy(default)


def save_setting(key: str, value: dict) -> dict:
    clean = _validate(key, value)
    now = datetime.now(timezone.utc).isoformat()
    data = {"key": key, "value_json": json_text(clean), "description": DESCRIPTIONS[key],
            "updated_at": now, "updated_by": "shared_session"}
    found = find_record("settings", "key", key)
    update_record("settings", found[0], data) if found else append_record("settings", data)
    append_record("audit_logs", {"log_id": str(uuid4()), "created_at": now, "actor": "shared_session",
                                 "action": "settings_saved", "target": key,
                                 "details_json": json_text({"key": key})})
    return clean


def get_all_settings() -> dict[str, dict]:
    return {key: get_setting(key) for key in ALLOWED_KEYS}
