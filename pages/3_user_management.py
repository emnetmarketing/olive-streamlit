import streamlit as st

from components.auth import require_approved
from services.admin_service import delete_account, list_audit_logs, list_profiles, update_account

st.set_page_config(page_title="사용자 권한 관리", page_icon="🔐", layout="wide")
actor = require_approved()
if not actor.is_master:
    st.error("마스터만 접근할 수 있습니다.")
    st.stop()

st.title("사용자 및 권한 관리")
st.caption("승인된 마스터는 최소 1명, 최대 2명까지 유지됩니다.")

try:
    profiles = list_profiles(actor)
except Exception:
    st.error("사용자 목록을 불러오지 못했습니다.")
    st.stop()

for user in profiles:
    user_id = user.get("user_id") or user.get("email", "")
    current_status = user.get("status") if user.get("status") in {"pending", "approved", "rejected", "disabled"} else "pending"
    current_role = user.get("role") if user.get("role") in {"operator", "editor", "master"} else "operator"
    with st.container(border=True):
        info, status_col, role_col, action_col = st.columns([3, 1.5, 1.5, 2])
        info.markdown(f"**{user.get('name') or '이름 미지정'}**")
        info.caption(user.get("email", ""))
        new_status = status_col.selectbox("상태", ["pending", "approved", "rejected", "disabled"],
                                          index=["pending", "approved", "rejected", "disabled"].index(current_status), key=f"status_{user_id}")
        new_role = role_col.selectbox("권한", ["operator", "editor", "master"],
                                      index=["operator", "editor", "master"].index(current_role), key=f"role_{user_id}")
        if action_col.button("변경 저장", key=f"save_{user_id}", use_container_width=True):
            try:
                update_account(actor, user_id, status=new_status, role=new_role)
                st.success("변경했습니다."); st.rerun()
            except Exception as exc:
                st.error(str(exc))
        quick1, quick2, quick3 = st.columns(3)
        if current_status == "pending" and quick1.button("승인", key=f"approve_{user_id}", use_container_width=True):
            try:
                update_account(actor, user_id, status="approved")
                st.success("승인했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if current_status == "pending" and quick2.button("거절", key=f"reject_{user_id}", use_container_width=True):
            try:
                update_account(actor, user_id, status="rejected")
                st.success("거절했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if user_id != actor.id and current_status == "approved" and quick3.button(
                "비활성화", key=f"disable_{user_id}", use_container_width=True):
            try:
                update_account(actor, user_id, status="disabled")
                st.success("비활성화했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if user_id != actor.id and action_col.button("사용자 행 삭제", key=f"delete_{user_id}", use_container_width=True):
            try:
                delete_account(actor, user_id)
                st.success("삭제했습니다."); st.rerun()
            except Exception as exc:
                st.error(str(exc))

st.divider()
st.subheader("관리 감사 기록")
try:
    logs = list_audit_logs(actor)
    st.dataframe(logs, use_container_width=True, hide_index=True)
except Exception as exc:
    st.error(f"감사 기록을 불러오지 못했습니다: {exc}")
