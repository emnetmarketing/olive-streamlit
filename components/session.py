import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

import streamlit as st
from extra_streamlit_components import CookieManager

from components.config import secret, secret_bool

COOKIE_NAME = "olive_shared_session"
SESSION_HOURS = 12


def _key() -> bytes:
    password = str(secret("APP_PASSWORD", required=True))
    if len(password) < 8:
        raise RuntimeError("APP_PASSWORD는 8자 이상으로 설정하세요.")
    return hashlib.sha256(password.encode("utf-8")).digest()


def _encode(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _decode(token: str, now: int | None = None) -> dict | None:
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(_key(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode())
        return payload if int(payload.get("exp", 0)) > int(now if now is not None else time.time()) else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def cookie_manager() -> CookieManager:
    if "_cookie_manager" not in st.session_state:
        st.session_state._cookie_manager = CookieManager(key="olive_shared_cookie_manager")
    return st.session_state._cookie_manager


def save_session() -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    token = _encode({"exp": int(expires_at.timestamp())})
    cookie_manager().set(COOKIE_NAME, token, expires_at=expires_at,
                         secure=secret_bool("COOKIE_SECURE", True), same_site="strict", key="set_shared_cookie")


def has_valid_session() -> bool:
    token = cookie_manager().get(COOKIE_NAME)
    return bool(token and _decode(token))


def clear_session() -> None:
    cookie_manager().delete(COOKIE_NAME, key="delete_shared_cookie")
    st.session_state.pop("authenticated", None)
