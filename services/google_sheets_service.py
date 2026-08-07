import json
from functools import lru_cache
from typing import Any

import gspread
from gspread.exceptions import WorksheetNotFound

from components.config import google_service_account, google_sheet_id

SHEET_HEADERS = {
    "users": ["user_id", "email", "name", "status", "role", "created_at", "updated_at",
              "approved_at", "approved_by", "last_login_at"],
    "settings": ["key", "value_json", "description", "updated_at", "updated_by"],
    "analysis_results": ["result_id", "created_at", "created_by_email", "period_start", "period_end",
                         "metrics_json", "filters_json", "result_json"],
    "audit_logs": ["log_id", "created_at", "actor_email", "action", "target_email", "details_json"],
}


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def parse_json(value: str, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


@lru_cache(maxsize=1)
def spreadsheet():
    client = gspread.service_account_from_dict(
        google_service_account(), scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return client.open_by_key(google_sheet_id())


def worksheet(name: str):
    if name not in SHEET_HEADERS:
        raise ValueError(f"허용되지 않은 시트입니다: {name}")
    book = spreadsheet()
    try:
        sheet = book.worksheet(name)
    except WorksheetNotFound:
        sheet = book.add_worksheet(title=name, rows=1000, cols=max(12, len(SHEET_HEADERS[name])))
    expected = SHEET_HEADERS[name]
    current = sheet.row_values(1)
    if not current:
        sheet.append_row(expected, value_input_option="RAW")
    elif current != expected:
        raise RuntimeError(f"'{name}' 시트의 1행 컬럼을 README의 권장 구조와 동일하게 맞춰 주세요.")
    return sheet


def ensure_schema() -> dict[str, int]:
    return {name: worksheet(name).row_count for name in SHEET_HEADERS}


def records(name: str) -> list[dict[str, str]]:
    return worksheet(name).get_all_records(default_blank="", numericise_ignore=["all"])


def append_record(name: str, data: dict[str, Any]) -> None:
    headers = SHEET_HEADERS[name]
    worksheet(name).append_row([str(data.get(header, "")) for header in headers], value_input_option="RAW")


def find_record(name: str, key: str, value: str) -> tuple[int, dict[str, str]] | None:
    target = str(value).strip().casefold()
    for index, record in enumerate(records(name), start=2):
        if str(record.get(key, "")).strip().casefold() == target:
            return index, record
    return None


def update_record(name: str, row_number: int, changes: dict[str, Any]) -> None:
    headers = SHEET_HEADERS[name]
    invalid = set(changes) - set(headers)
    if invalid:
        raise ValueError(f"허용되지 않은 컬럼입니다: {', '.join(sorted(invalid))}")
    sheet = worksheet(name)
    for key, value in changes.items():
        sheet.update_cell(row_number, headers.index(key) + 1, str(value if value is not None else ""))


def delete_record(name: str, row_number: int) -> None:
    worksheet(name).delete_rows(row_number)


def connection_status() -> dict[str, int]:
    ensure_schema()
    return {name: len(records(name)) for name in SHEET_HEADERS}
