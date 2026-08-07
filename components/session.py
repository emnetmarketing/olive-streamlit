import json
from datetime import datetime, timedelta, timezone

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from extra_streamlit_components import CookieManager

from components.config import secret, secret_bool

COOKIE_NAME = "olive_email_session"


def _cipher() -> Fernet:
    return Fernet(str(secret("SESSION_ENCRYPTION_KEY", required=True)).encode())


def cookie_manager() -> CookieManager:
    if "_cookie_manager" not in st.session_state:
        st.session_state._cookie_manager = CookieManager(key="olive_email_cookie_manager")
    return st.session_state._cookie_manager


def save_identity(email: str) -> None:
    encrypted = _cipher().encrypt(json.dumps({"email": email.strip().lower()}).encode()).decode()
    cookie_manager().set(COOKIE_NAME, encrypted, expires_at=datetime.now(timezone.utc) + timedelta(days=14),
                         secure=secret_bool("COOKIE_SECURE", True), same_site="strict", key="set_email_cookie")


def load_identity() -> str | None:
    encrypted = cookie_manager().get(COOKIE_NAME)
    if not encrypted:
        return None
    try:
        data = json.loads(_cipher().decrypt(encrypted.encode(), ttl=60 * 60 * 24 * 14))
        email = str(data.get("email", "")).strip().lower()
        return email or None
    except (InvalidToken, ValueError, TypeError, json.JSONDecodeError):
        clear_identity()
        return None


def clear_identity() -> None:
    cookie_manager().delete(COOKIE_NAME, key="delete_email_cookie")
    st.session_state.pop("profile", None)
