import re
from datetime import datetime, timezone
from uuid import uuid4

import streamlit as st

from components.session import clear_identity, load_identity, save_identity
from models.schemas import UserProfile
from services.google_sheets_service import append_record, find_record, update_record

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user(email: str) -> UserProfile | None:
    found = find_record("users", "email", email.strip().lower())
    return UserProfile.from_record(found[1]) if found else None


def request_access(email: str, name: str) -> UserProfile:
    email = email.strip().lower()
    name = name.strip()
    if not EMAIL_PATTERN.match(email):
        raise ValueError("올바른 이메일 주소를 입력하세요.")
    if not name:
        raise ValueError("사용자 이름을 입력하세요.")
    existing = get_user(email)
    if existing:
        return existing
    now = _now()
    append_record("users", {"user_id": str(uuid4()), "email": email, "name": name, "status": "pending",
                            "role": "operator", "created_at": now, "updated_at": now})
    append_record("audit_logs", {"log_id": str(uuid4()), "created_at": now, "actor_email": email,
                                 "action": "access_requested", "target_email": email, "details_json": "{}"})
    return get_user(email)


def sign_in(email: str, name: str = "") -> UserProfile:
    email = email.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise ValueError("올바른 이메일 주소를 입력하세요.")
    profile = get_user(email) or request_access(email, name)
    if profile.approved:
        found = find_record("users", "email", email)
        update_record("users", found[0], {"last_login_at": _now(), "updated_at": _now()})
        save_identity(email)
        st.session_state.profile = profile
    return profile


def restore_auth() -> UserProfile | None:
    email = load_identity()
    if not email:
        return None
    try:
        profile = get_user(email)
        if not profile or not profile.approved:
            clear_identity()
            return profile
        st.session_state.profile = profile
        return profile
    except Exception:
        return None


def sign_out() -> None:
    clear_identity()


def require_approved() -> UserProfile:
    profile = restore_auth()
    if not profile:
        st.error("승인된 사용자 이메일로 로그인해야 합니다.")
        st.stop()
    if not profile.approved:
        messages = {"pending": "승인 대기 중입니다.", "rejected": "접근 요청이 거절되었습니다.",
                    "disabled": "비활성화된 계정입니다."}
        st.warning(messages.get(profile.status, "이 계정으로 접근할 수 없습니다."))
        if st.button("로그아웃"):
            sign_out()
            st.rerun()
        st.stop()
    return profile
