from datetime import datetime, timedelta, timezone
from typing import Any, MutableMapping
from uuid import uuid4

from services.settings_service import get_setting

SESSION_RESULTS_KEY = "analysis_result_history"


def _state(state: MutableMapping[str, Any] | None = None) -> MutableMapping[str, Any]:
    if state is not None:
        return state
    import streamlit as st

    return st.session_state


def save_analysis_result(result_data: dict[str, Any], *, state: MutableMapping[str, Any] | None = None,
                         retention: dict[str, int] | None = None) -> None:
    session = _state(state)
    history = list(session.get(SESSION_RESULTS_KEY, []))
    history.append({"id": str(uuid4()), "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": "shared_session", "result_data": result_data})
    policy = retention or get_setting("retention")
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(policy["days"]))
    retained = []
    for item in history:
        try:
            created_at = datetime.fromisoformat(item["created_at"])
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at >= cutoff:
                retained.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    session[SESSION_RESULTS_KEY] = retained[-int(policy["max_records"]):]


def recent_results(limit: int = 20, *, state: MutableMapping[str, Any] | None = None,
                   max_records: int | None = None) -> list[dict[str, Any]]:
    history = list(_state(state).get(SESSION_RESULTS_KEY, []))
    maximum = int(max_records if max_records is not None else get_setting("retention")["max_records"])
    safe_limit = max(1, min(int(limit), min(maximum, 200)))
    return list(reversed(history))[:safe_limit]
