import os
from typing import Any

def secret(name: str, default: Any = None, required: bool = False) -> Any:
    value = os.getenv(name)
    if value is None:
        try:
            import streamlit as st
            value = st.secrets.get(name, default)
        except (FileNotFoundError, KeyError, ImportError):
            value = default
    if required and not value:
        raise RuntimeError(f"필수 배포 설정이 없습니다: {name}")
    return value


def google_sheet_id() -> str:
    return str(secret("GOOGLE_SHEET_ID", required=True)).strip()


def google_service_account() -> dict:
    value = secret("gcp_service_account", required=True)
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, dict):
        raise RuntimeError("gcp_service_account Secrets 블록 형식이 올바르지 않습니다.")
    credentials = {str(key): str(item) for key, item in value.items()}
    if "private_key" in credentials:
        credentials["private_key"] = credentials["private_key"].replace("\\n", "\n")
    required = {"type", "project_id", "private_key", "client_email", "token_uri"}
    missing = sorted(required - credentials.keys())
    if missing:
        raise RuntimeError(f"Google 서비스 계정 필수 항목이 없습니다: {', '.join(missing)}")
    return credentials


def secret_bool(name: str, default: bool = False) -> bool:
    value = secret(name, default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
