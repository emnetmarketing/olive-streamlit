import hmac

import streamlit as st

from components.config import secret
from components.session import clear_session, has_valid_session, save_session


def authenticate(password: str) -> bool:
    expected = str(secret("APP_PASSWORD", required=True))
    if len(expected) < 8:
        raise RuntimeError("APP_PASSWORD는 8자 이상으로 설정하세요.")
    valid = hmac.compare_digest(str(password).encode("utf-8"), expected.encode("utf-8"))
    if valid:
        save_session()
        st.session_state.authenticated = True
    return valid


def restore_auth() -> bool:
    if st.session_state.get("authenticated") is True:
        return True
    valid = has_valid_session()
    if valid:
        st.session_state.authenticated = True
    return valid


def sign_out() -> None:
    clear_session()


def require_auth() -> None:
    if not restore_auth():
        st.error("공용 비밀번호로 로그인해야 합니다.")
        st.stop()
