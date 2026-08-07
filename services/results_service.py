from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from models.schemas import UserProfile
from services.google_sheets_service import append_record, delete_record, json_text, parse_json, records
from services.settings_service import get_setting


def save_analysis_result(profile: UserProfile, result_data: dict[str, Any]) -> None:
    if not profile.approved:
        raise PermissionError("승인된 사용자만 분석 결과를 저장할 수 있습니다.")
    now = datetime.now(timezone.utc).isoformat()
    period = result_data.get("period", {})
    append_record("analysis_results", {
        "result_id": str(uuid4()), "created_at": now, "created_by_email": profile.email,
        "period_start": period.get("start", ""), "period_end": period.get("end", ""),
        "metrics_json": json_text(result_data.get("metrics", {})),
        "filters_json": json_text(result_data.get("filters", {})), "result_json": json_text(result_data),
    })
    append_record("audit_logs", {"log_id": str(uuid4()), "created_at": now, "actor_email": profile.email,
                                 "action": "analysis_saved", "target_email": "", "details_json": json_text(result_data.get("metrics", {}))})
    cleanup_analysis_results()


def cleanup_analysis_results() -> None:
    retention = get_setting("retention")
    all_rows = records("analysis_results")
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention["days"])
    remove_rows = []
    for row_number, item in enumerate(all_rows, start=2):
        try:
            created_at = datetime.fromisoformat(item.get("created_at", ""))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at < cutoff:
                remove_rows.append(row_number)
        except (TypeError, ValueError):
            continue
    remaining = [(index, item) for index, item in enumerate(all_rows, start=2) if index not in remove_rows]
    excess = max(0, len(remaining) - retention["max_records"])
    remove_rows.extend(index for index, _ in remaining[:excess])
    for row_number in sorted(set(remove_rows), reverse=True):
        delete_record("analysis_results", row_number)


def recent_results(limit: int = 20) -> list[dict]:
    retention = get_setting("retention")
    safe_limit = max(1, min(int(limit), min(retention["max_records"], 200)))
    output = []
    for item in reversed(records("analysis_results")):
        result_data = parse_json(item.get("result_json", ""), {})
        output.append({"id": item.get("result_id", ""), "created_at": item.get("created_at", ""),
                       "created_by": item.get("created_by_email", ""), "result_data": result_data})
    return output[:safe_limit]
