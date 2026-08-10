import json
from typing import Any
from urllib.parse import urlparse

import httpx

from components.config import google_apps_script_url

SHEET_HEADERS = {
    "settings": ["key", "value_json", "description", "updated_at", "updated_by"],
    "analysis_results": ["result_id", "created_at", "created_by", "period_start", "period_end",
                         "metrics_json", "filters_json", "result_json"],
    "audit_logs": ["log_id", "created_at", "actor", "action", "target", "details_json"],
}
TIMEOUT_SECONDS = 30


class GoogleSheetsAPIError(RuntimeError):
    pass


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_json(value: str, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def _web_app_url() -> str:
    url = google_apps_script_url()
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "script.google.com" or not parsed.path.endswith("/exec"):
        raise RuntimeError("GOOGLE_APPS_SCRIPT_URL에는 Apps Script Web App의 HTTPS /exec URL을 입력하세요.")
    return url


def _request(action: str, **payload: Any) -> Any:
    try:
        response = httpx.post(_web_app_url(), json={"action": action, **payload}, timeout=TIMEOUT_SECONDS,
                              follow_redirects=True)
        response.raise_for_status()
        body = response.json()
    except httpx.TimeoutException as exc:
        raise GoogleSheetsAPIError("Google Apps Script 요청 시간이 초과되었습니다.") from exc
    except httpx.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        suffix = f" (HTTP {status})" if status else ""
        raise GoogleSheetsAPIError(f"Google Apps Script 요청에 실패했습니다{suffix}.") from exc
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise GoogleSheetsAPIError("Google Apps Script가 올바른 JSON을 반환하지 않았습니다.") from exc
    if not isinstance(body, dict) or not body.get("ok"):
        message = body.get("error", "알 수 없는 오류") if isinstance(body, dict) else "응답 형식 오류"
        raise GoogleSheetsAPIError(f"Google Apps Script 오류: {message}")
    return body.get("data")


def ensure_schema() -> dict[str, int]:
    data = _request("ensure_schema")
    return {name: int((data or {}).get(name, 0)) for name in SHEET_HEADERS}


def records(name: str) -> list[dict[str, str]]:
    if name not in SHEET_HEADERS:
        raise ValueError(f"허용되지 않은 시트입니다: {name}")
    data = _request("records", sheet=name)
    return data if isinstance(data, list) else []


def append_record(name: str, data: dict[str, Any]) -> None:
    if name not in SHEET_HEADERS:
        raise ValueError(f"허용되지 않은 시트입니다: {name}")
    _request("append_record", sheet=name, data=data)


def find_record(name: str, key: str, value: str) -> tuple[int, dict[str, str]] | None:
    target = str(value).strip().casefold()
    for index, record in enumerate(records(name), start=2):
        if str(record.get(key, "")).strip().casefold() == target:
            return index, record
    return None


def update_record(name: str, row_number: int, changes: dict[str, Any]) -> None:
    if name not in SHEET_HEADERS:
        raise ValueError(f"허용되지 않은 시트입니다: {name}")
    invalid = set(changes) - set(SHEET_HEADERS[name])
    if invalid:
        raise ValueError(f"허용되지 않은 컬럼입니다: {', '.join(sorted(invalid))}")
    _request("update_record", sheet=name, row_number=int(row_number), changes=changes)


def delete_record(name: str, row_number: int) -> None:
    if name not in SHEET_HEADERS:
        raise ValueError(f"허용되지 않은 시트입니다: {name}")
    _request("delete_record", sheet=name, row_number=int(row_number))


def connection_status() -> dict[str, int]:
    return ensure_schema()
