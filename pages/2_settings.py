from datetime import date, time

import streamlit as st

from components.auth import require_auth
from components.config import secret
from services.settings_service import get_all_settings, save_setting
from services.teams_service import send_teams_alert

st.set_page_config(page_title="모니터 설정", page_icon="⚙️", layout="wide")
require_auth()

st.title("모니터 설정")
st.caption("일반 설정은 현재 로그인 세션에 적용됩니다. API 인증정보는 Streamlit Secrets에서만 관리됩니다.")

settings = get_all_settings()
dashboard = settings["dashboard"]
retention = settings["retention"]
with st.form("dashboard_settings"):
    st.subheader("분석 기준")
    c1, c2, c3 = st.columns(3)
    surge = c1.number_input("급상승 기준", min_value=1, value=int(dashboard["surge_threshold"]))
    match = c2.slider("매칭 기준 (%)", 0, 100, int(dashboard["match_threshold"]))
    yesterday = c3.number_input("전일 최대량", min_value=0, value=int(dashboard["yesterday_max"]))
    st.subheader("수집 설정")
    c1, c2 = st.columns(2)
    start = c1.date_input("수집 시작일", value=date.fromisoformat(dashboard["collection_start"]) if dashboard.get("collection_start") else date.today())
    end = c2.date_input("수집 종료일", value=date.fromisoformat(dashboard["collection_end"]) if dashboard.get("collection_end") else date.today())
    schedule_mode = st.selectbox("반복 방식", ["daily", "weekly", "monthly"], index=["daily", "weekly", "monthly"].index(dashboard["schedule_mode"]))
    schedule_time = st.time_input("수집 시간", value=time.fromisoformat(dashboard["schedule_times"][0]))
    alert_enabled = st.toggle("알림 사용", value=bool(dashboard["alert_enabled"]))
    alert_channel = st.selectbox("알림 채널", ["teams"], index=0,
                                 help="현재 Teams Workflow/Incoming Webhook 알림을 지원합니다.")
    saved = st.form_submit_button("설정 저장")
if saved:
    try:
        save_setting("dashboard", {**dashboard, "surge_threshold": surge, "match_threshold": match,
                     "yesterday_max": yesterday, "collection_start": start.isoformat(), "collection_end": end.isoformat(),
                     "schedule_mode": schedule_mode, "schedule_times": [schedule_time.strftime("%H:%M")],
                     "alert_enabled": alert_enabled, "alert_channel": alert_channel})
        st.success("현재 세션에 설정을 적용했습니다.")
    except Exception as exc:
        st.error(str(exc))

with st.form("retention_settings"):
    st.subheader("분석 결과 보관")
    c1, c2 = st.columns(2)
    days = c1.number_input("보관 기간(일)", min_value=1, max_value=3650, value=int(retention["days"]))
    max_records = c2.number_input("최대 저장 건수", min_value=10, max_value=100000,
                                  value=int(retention["max_records"]), step=10)
    retention_saved = st.form_submit_button("보관 정책 저장")
if retention_saved:
    try:
        save_setting("retention", {"days": days, "max_records": max_records})
        st.success("현재 세션에 보관 정책을 적용했습니다.")
    except Exception as exc:
        st.error(str(exc))

st.subheader("서버 Secret 상태")
st.write({
    "네이버 API": "연결됨" if secret("NAVER_CLIENT_ID") and secret("NAVER_CLIENT_SECRET") else "미설정",
    "Teams": "연결됨" if secret("TEAMS_WEBHOOK_URL") else "미설정",
})

if st.button("Teams 테스트 알림 보내기"):
    try:
        send_teams_alert({"keywords": 1, "surges": 1, "matched": 1, "total_today": 1},
                         title="Olive Teams 연동 테스트")
        st.success("Teams 테스트 알림을 전송했습니다.")
    except Exception as exc:
        st.error(str(exc))
