import html
import json
from datetime import date, datetime, timedelta
from io import BytesIO

import pandas as pd
import streamlit as st

from components.auth import require_auth, restore_auth, sign_out
from components.auth_ui import render_login
from components.config import secret
from components.styles import apply_styles
from services.analysis_service import analyze_trends, summary_metrics
from services.export_service import dataframe_to_xlsx
from services.naver_datalab_service import search_trends
from services.naver_news_service import search_news
from services.naver_shopping_insight_service import keyword_trends
from services.naver_shopping_service import search_shopping
from services.results_service import recent_results, save_analysis_result
from services.settings_service import get_setting, save_setting
from services.teams_service import send_teams_alert

st.set_page_config(page_title="네쇼검 트렌드 모니터", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")
apply_styles()

SAMPLE_SOCIAL = [
    {"keyword": "아크멜로 비타 세럼", "today": 12840, "yesterday": 94},
    {"keyword": "아크멜로비타세럼", "today": 10380, "yesterday": 51},
    {"keyword": "모닝글로우 쿠션", "today": 18810, "yesterday": 220},
    {"keyword": "인기 해시태그", "today": 15120, "yesterday": 9870},
    {"keyword": "루미네 바디미스트", "today": 11420, "yesterday": 40},
]


@st.cache_data(show_spinner=False)
def read_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "csv":
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                return pd.read_csv(BytesIO(file_bytes), encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("CSV 인코딩을 읽을 수 없습니다. UTF-8 또는 CP949 파일을 사용하세요.")
    if suffix in {"xlsx", "xls"}:
        return pd.read_excel(BytesIO(file_bytes))
    raise ValueError("CSV, XLSX 또는 XLS 파일만 업로드할 수 있습니다.")


def trend_frame(results: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{"그룹": result.get("title", ""), "기간": point.get("period"),
                          "비율": point.get("ratio", 0), "구분": point.get("group", "")}
                         for result in results for point in result.get("data", [])])


def summary_html(values: list[tuple[str, str]]) -> str:
    cards = "".join(f'<div class="nt-stat"><b>{html.escape(str(value))}</b><span>{html.escape(label)}</span></div>'
                    for value, label in values)
    return f'<section class="nt-panel"><h2 class="nt-panel-title">모니터링 요약</h2><div class="nt-stats">{cards}</div></section>'


def top10_html(frame: pd.DataFrame) -> str:
    top = frame[frame["is_surge"]].head(10)
    if top.empty:
        body = '<div class="nt-empty">분석 후 급등 키워드 증감 그래프가 표시됩니다.</div>'
    else:
        maximum = max(int(top["increase"].max()), 1)
        rows = []
        for row in top.itertuples():
            width = max(3, min(100, int(max(row.increase, 0) / maximum * 100)))
            rows.append(
                f'<div class="nt-trend-row"><div class="nt-trend-name">{html.escape(str(row.keyword))}'
                f'<span class="nt-trend-sub">{row.yesterday:,} → {row.today:,}</span></div>'
                f'<div class="nt-track"><div class="nt-fill" style="width:{width}%"></div></div>'
                f'<div class="nt-trend-value">+{row.increase:,}<small>+{row.growth_rate:,.1f}%</small></div></div>')
        body = "".join(rows)
    return f'<section class="nt-panel"><h2 class="nt-panel-title">급등 TOP 10 키워드</h2>{body}</section>'


def results_html(frame: pd.DataFrame) -> str:
    if frame.empty:
        rows = '<tr><td colspan="7" style="color:#748098">분석 실행 후 결과가 표시됩니다.</td></tr>'
    else:
        output = []
        for row in frame.itertuples():
            source = "소셜 업로드"
            ad_item = " / ".join(part for part in (str(row.brand or ""), str(row.matched_product or "")) if part) or "-"
            verdict = "일치" if row.matched else ("급등" if row.is_surge else "관찰")
            pill = "" if row.matched else ("warn" if row.is_surge else "bad")
            output.append(f'<tr><td><strong>{html.escape(str(row.keyword))}</strong></td>'
                          f'<td>{row.today:,} / {row.yesterday:,}</td><td>+{row.increase:,}</td>'
                          f'<td>{source}</td><td>{html.escape(ad_item)}</td><td>{row.match_score:.1f}%</td>'
                          f'<td><span class="nt-pill {pill}">{verdict}</span></td></tr>')
        rows = "".join(output)
    return ('<div class="nt-table-wrap"><table class="nt-table"><thead><tr>'
            '<th>급등 키워드</th><th>당일/전일</th><th>상승폭</th><th>출처</th>'
            '<th>Naver 광고 항목</th><th>일치율</th><th>판정</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')


if not restore_auth():
    render_login()
    st.stop()
require_auth()

settings = get_setting("dashboard")
st.session_state.setdefault("social_rows", SAMPLE_SOCIAL)
st.session_state.setdefault("naver_products", [])
st.session_state.setdefault("download_history", [])

with st.sidebar:
    st.markdown('<div class="nt-brand"><span class="nt-mark">NT</span><div><strong>Naver Trend Monitor</strong>'
                '<small>Keyword monitor</small></div></div>', unsafe_allow_html=True)
    monitor_tab, api_tab = st.tabs(["모니터링", "API 연결"])
    with monitor_tab:
        st.markdown("### 설정")
        s1, s2 = st.columns(2)
        surge = s1.number_input("급등 기준 언급량", min_value=1, value=int(settings["surge_threshold"]))
        match = s2.number_input("일치율 기준(%)", min_value=0, max_value=100,
                                value=int(settings["match_threshold"]))
        yesterday = st.number_input("전일 저조 기준 최대 언급량", min_value=0,
                                    value=int(settings["yesterday_max"]))
        uploaded = st.file_uploader("브랜드/제품 엑셀 업로드", type=["csv", "xlsx", "xls"],
                                    help="소셜 데이터: keyword/today/yesterday 또는 브랜드 데이터: brand/product")
        if uploaded:
            try:
                uploaded_frame = read_upload(uploaded.getvalue(), uploaded.name)
                if {"keyword", "today", "yesterday"} <= set(uploaded_frame.columns):
                    st.session_state.social_rows = uploaded_frame.to_dict("records")
                    st.success(f"소셜 데이터 {len(uploaded_frame):,}건 반영")
                elif {"brand", "product"} <= set(uploaded_frame.columns):
                    st.session_state.naver_products = uploaded_frame.to_dict("records")
                    st.success(f"브랜드/제품 {len(uploaded_frame):,}건 반영")
                else:
                    raise ValueError("keyword/today/yesterday 또는 brand/product 열이 필요합니다.")
            except Exception as exc:
                st.error(str(exc))
        st.markdown('<div class="nt-note">엑셀 업로드 또는 샘플 데이터로 분석할 수 있습니다. 설정은 현재 세션에 적용됩니다.</div>',
                    unsafe_allow_html=True)
        save_setting("dashboard", {**settings, "surge_threshold": surge, "match_threshold": match,
                                    "yesterday_max": yesterday})
    with api_tab:
        naver_ready = bool(secret("NAVER_CLIENT_ID") and secret("NAVER_CLIENT_SECRET"))
        teams_ready = bool(secret("TEAMS_WEBHOOK_URL"))
        st.markdown("### API 연결")
        st.markdown(f'<div class="nt-note"><strong>네이버 API</strong><br>{"🟢 연결됨" if naver_ready else "🔴 미설정"}'
                    f'<br><br><strong>Teams</strong><br>{"🟢 연결됨" if teams_ready else "⚪ 선택 미설정"}</div>',
                    unsafe_allow_html=True)
        st.caption("인증정보는 Streamlit Secrets에서만 관리되며 화면에 표시되지 않습니다.")

st.markdown('<div class="nt-header"><div class="nt-eyebrow">NAVER TREND MONITOR</div>'
            '<h1 class="nt-title">네쇼검 트렌드 모니터</h1></div>', unsafe_allow_html=True)
default_start = date.fromisoformat(settings["collection_start"]) if settings.get("collection_start") else date.today()-timedelta(days=7)
default_end = date.fromisoformat(settings["collection_end"]) if settings.get("collection_end") else date.today()
h1, h2, h3, h4, h5, h6 = st.columns([1.15, 1.15, .9, 1.1, .9, .75])
start_date = h1.date_input("수집 기간 시작일", default_start)
end_date = h2.date_input("수집 기간 종료일", default_end)
run_clicked = h3.button("▶ 분석 실행", use_container_width=True)
with h4.popover("⏱ 자동 수집 설정", use_container_width=True):
    schedule_mode = st.selectbox("수집 반복 방식", ["daily", "weekly", "monthly"],
                                 index=["daily", "weekly", "monthly"].index(settings["schedule_mode"]))
    schedule_time = st.time_input("수집 시간", datetime.strptime(settings["schedule_times"][0], "%H:%M").time())
    alert_enabled = st.toggle("Teams 자동 알림", value=bool(settings["alert_enabled"]))
    if st.button("자동 수집 설정 적용"):
        settings = save_setting("dashboard", {**settings, "schedule_mode": schedule_mode,
                                "schedule_times": [schedule_time.strftime("%H:%M")], "alert_enabled": alert_enabled})
        st.success("현재 세션에 적용했습니다.")
if h5.button("↗ Teams 전송", use_container_width=True):
    st.session_state.send_teams_now = True
if h6.button("로그아웃", use_container_width=True):
    sign_out(); st.rerun()
if start_date > end_date:
    st.error("수집 시작일은 종료일보다 늦을 수 없습니다."); st.stop()
if run_clicked:
    st.session_state.last_analysis_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_setting("dashboard", {**settings, "collection_start": start_date.isoformat(),
                                "collection_end": end_date.isoformat()})

with st.expander("API 연결 및 데이터 수집", expanded=False):
    search_tab, news_tab, datalab_tab, insight_tab = st.tabs(["쇼핑 검색", "뉴스 검색", "검색어 DataLab", "쇼핑인사이트"])
    with search_tab:
        query = st.text_input("쇼핑 검색어")
        if st.button("쇼핑 상품 가져오기"):
            try: st.session_state.naver_products=search_shopping(query); st.success("쇼핑 결과를 반영했습니다.")
            except Exception as exc: st.error(str(exc))
    with news_tab:
        query = st.text_input("뉴스 검색어")
        if st.button("뉴스 가져오기"):
            try: st.session_state.news_items=search_news(query); st.success("뉴스 결과를 불러왔습니다.")
            except Exception as exc: st.error(str(exc))
    with datalab_tab:
        query = st.text_input("DataLab 검색어"); unit=st.selectbox("조회 단위",["date","week","month"])
        if st.button("검색어 트렌드 조회"):
            try: st.session_state.datalab_items=search_trends(start_date,end_date,[{"groupName":query,"keywords":[query]}],time_unit=unit)
            except Exception as exc: st.error(str(exc))
    with insight_tab:
        category=st.text_input("네이버 쇼핑 분야 코드",placeholder="예: 50000002"); query=st.text_input("쇼핑인사이트 키워드")
        c1,c2,c3=st.columns(3); unit=c1.selectbox("구간",["date","week","month"]); device=c2.selectbox("기기",["전체","PC","모바일"]); gender=c3.selectbox("성별",["전체","여성","남성"])
        ages=st.multiselect("연령대",["10","20","30","40","50","60"])
        if st.button("쇼핑 클릭 트렌드 조회"):
            try: st.session_state.shopping_insight_items=keyword_trends(start_date,end_date,category,[{"name":query,"param":[query]}],time_unit=unit,device={"PC":"pc","모바일":"mo"}.get(device),gender={"여성":"f","남성":"m"}.get(gender),ages=ages)
            except Exception as exc: st.error(str(exc))

result = analyze_trends(st.session_state.social_rows, st.session_state.naver_products,
                        surge_threshold=surge, yesterday_max=yesterday, match_threshold=match)
metrics = summary_metrics(result)
if st.session_state.pop("send_teams_now", False):
    try: send_teams_alert(metrics); st.success("Teams 알림을 전송했습니다.")
    except Exception as exc: st.error(str(exc))

st.markdown(summary_html([(str(len(st.session_state.get("datalab_items", []))),"네이버 검색어트렌드"),
                          (str(len(st.session_state.get("shopping_insight_items", []))),"네이버 쇼핑인사이트"),
                          (str(len(st.session_state.get("news_items", []))),"네이버 뉴스"),
                          (str(metrics["matched"]),"일치 키워드"),
                          (st.session_state.get("last_analysis_at","-"),"마지막 분석 시간")]), unsafe_allow_html=True)
st.markdown(top10_html(result), unsafe_allow_html=True)

st.markdown('<section class="nt-panel" style="margin-bottom:0"><h2 class="nt-panel-title">모니터링 결과</h2>', unsafe_allow_html=True)
f1,f2,f3=st.columns([2,1,1]); keyword_filter=f1.text_input("키워드 검색",placeholder="키워드 또는 브랜드"); surge_filter=f2.selectbox("급등",["전체","급상승만","일반만"]); match_filter=f3.selectbox("상품 매칭",["전체","매칭만","미매칭만"])
filtered=result.copy()
if keyword_filter:
    term=keyword_filter.casefold(); filtered=filtered[filtered["keyword"].str.casefold().str.contains(term,regex=False)|filtered["brand"].fillna("").str.casefold().str.contains(term,regex=False)|filtered["matched_product"].fillna("").str.casefold().str.contains(term,regex=False)]
if surge_filter!="전체": filtered=filtered[filtered["is_surge"]==(surge_filter=="급상승만")]
if match_filter!="전체": filtered=filtered[filtered["matched"]==(match_filter=="매칭만")]
d1,d2,d3=st.columns([1,1,1.25]); csv_data=filtered.to_csv(index=False).encode("utf-8-sig"); xlsx_data=dataframe_to_xlsx(filtered)
d1.download_button("CSV 다운로드",csv_data,"naver_trend_results.csv","text/csv",use_container_width=True)
d2.download_button("엑셀 다운로드",xlsx_data,"naver_trend_results.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
if d3.button("다운로드 신청 이력",use_container_width=True): st.session_state.show_download_history=not st.session_state.get("show_download_history",False)
if st.session_state.get("show_download_history"):
    st.info("다운로드 파일은 브라우저에서 바로 생성됩니다. 별도 서버 저장 이력은 남기지 않습니다.")
st.markdown(results_html(filtered),unsafe_allow_html=True)
if st.button("현재 결과를 세션에 저장"):
    payload={"period":{"start":start_date.isoformat(),"end":end_date.isoformat()},"metrics":summary_metrics(filtered),"rows":json.loads(filtered.to_json(orient="records",force_ascii=False))}
    save_analysis_result(payload); st.success("현재 세션에 저장했습니다.")
if recent_results():
    with st.expander("최근 저장 기록"):
        st.dataframe(pd.DataFrame([{"저장 시각":x["created_at"],**x["result_data"].get("metrics",{})} for x in recent_results()]),hide_index=True,use_container_width=True)
st.markdown('</section>',unsafe_allow_html=True)

if st.session_state.get("news_items"):
    with st.expander("뉴스 결과"):
        news=pd.DataFrame(st.session_state.news_items); cols=[c for c in ("title_clean","description_clean","pubDate","link") if c in news]; st.dataframe(news[cols],hide_index=True,use_container_width=True)
for key,label in (("datalab_items","검색어 DataLab 결과"),("shopping_insight_items","쇼핑인사이트 결과")):
    if st.session_state.get(key):
        with st.expander(label):
            data=trend_frame(st.session_state[key]); st.line_chart(data,x="기간",y="비율",color="그룹"); st.dataframe(data,hide_index=True,use_container_width=True)
