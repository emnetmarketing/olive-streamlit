from datetime import datetime, timezone
from uuid import uuid4

from models.schemas import UserProfile
from services.google_sheets_service import append_record, delete_record, find_record, json_text, records, update_record

VALID_STATUSES = {"pending", "approved", "rejected", "disabled"}
VALID_ROLES = {"master", "editor", "operator"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_master(actor: UserProfile) -> None:
    if not actor.is_master:
        raise PermissionError("마스터 권한이 필요합니다.")


def _audit(actor: UserProfile, action: str, target_email: str, details: str = "{}") -> None:
    append_record("audit_logs", {"log_id": str(uuid4()), "created_at": _now(), "actor_email": actor.email,
                                 "action": action, "target_email": target_email, "details_json": details})


def list_profiles(actor: UserProfile) -> list[dict]:
    _require_master(actor)
    return records("users")


def list_audit_logs(actor: UserProfile, limit: int = 100) -> list[dict]:
    _require_master(actor)
    return list(reversed(records("audit_logs")))[0:max(1, min(int(limit), 500))]


def update_account(actor: UserProfile, target_id: str, *, status: str | None = None,
                   role: str | None = None) -> None:
    _require_master(actor)
    found = find_record("users", "user_id", target_id) or find_record("users", "email", target_id)
    if not found:
        raise ValueError("사용자를 찾을 수 없습니다.")
    row_number, target = found
    if status is not None and status not in VALID_STATUSES:
        raise ValueError("허용되지 않은 승인 상태입니다.")
    if role is not None and role not in VALID_ROLES:
        raise ValueError("허용되지 않은 권한입니다.")
    next_role, next_status = role or target["role"], status or target["status"]
    approved_masters = [user for user in records("users") if user.get("role") == "master" and user.get("status") == "approved"]
    target_is_master = target.get("role") == "master" and target.get("status") == "approved"
    if next_role == "master" and next_status == "approved" and not target_is_master and len(approved_masters) >= 2:
        raise ValueError("승인된 마스터는 최대 2명까지 지정할 수 있습니다.")
    if target_is_master and (next_role != "master" or next_status != "approved") and len(approved_masters) <= 1:
        raise ValueError("마지막 승인 마스터를 강등하거나 비활성화할 수 없습니다.")
    now = _now()
    changes = {"updated_at": now}
    if status is not None:
        changes["status"] = status
        changes["approved_at"] = now if status == "approved" else ""
        changes["approved_by"] = actor.email if status == "approved" else ""
    if role is not None:
        changes["role"] = role
    update_record("users", row_number, changes)
    _audit(actor, "account_updated", target.get("email", ""), json_text({"status": status, "role": role}))


def delete_account(actor: UserProfile, target_id: str) -> None:
    _require_master(actor)
    found = find_record("users", "user_id", target_id) or find_record("users", "email", target_id)
    if not found:
        raise ValueError("사용자를 찾을 수 없습니다.")
    row_number, target = found
    if target.get("email", "").casefold() == actor.email.casefold():
        raise ValueError("현재 로그인한 자신의 사용자 행은 삭제할 수 없습니다.")
    approved_masters = [user for user in records("users") if user.get("role") == "master" and user.get("status") == "approved"]
    if target.get("role") == "master" and target.get("status") == "approved" and len(approved_masters) <= 1:
        raise ValueError("마지막 승인 마스터는 삭제할 수 없습니다.")
    target_email = target.get("email", "")
    delete_record("users", row_number)
    _audit(actor, "account_deleted", target_email)
