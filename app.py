import json
from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from components.auth import require_auth, restore_auth, sign_out
from components.auth_ui import render_login
from components.styles import apply_styles
from services.analysis_service import analyze_trends, summary_metrics
from services.export_service import dataframe_to_xlsx
from services.google_sheets_service import ensure_schema
from services.naver_datalab_service import search_trends
from services.naver_news_service import search_news
from services.naver_shopping_insight_service import keyword_trends
from services.naver_shopping_service import search_shopping
from services.results_service import recent_results, save_analysis_result
from services.settings_service import get_setting
from services.teams_service import send_teams_alert

st.set_page_config(page_title="네쇼검 트렌드 모니터", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")
apply_styles()


@st.cache_data(show_spinner=False)
def read_social_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "csv":
        last_error = None
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                return pd.read_csv(BytesIO(file_bytes), encoding=encoding)
            except UnicodeDecodeError as exc:
                last_error = exc
        raise ValueError("CSV 인코딩을 읽을 수 없습니다. UTF-8 또는 CP949 파일을 사용하세요.") from last_error
    if suffix in {"xlsx", "xls"}:
        return pd.read_excel(BytesIO(file_bytes))
    raise ValueError("CSV, XLSX 또는 XLS 파일만 업로드할 수 있습니다.")


def trend_frame(results: list[dict]) -> pd.DataFrame:
    rows = []
    for result in results:
        for point in result.get("data", []):
            rows.append({"그룹": result.get("title", ""), "기간": point.get("period"),
                         "비율": point.get("ratio", 0), "구분": point.get("group", "")})
    return pd.DataFrame(rows)


if not restore_auth():
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        render_login()
    st.stop()
require_auth()

try:
    ensure_schema()
except Exception as exc:
    st.error(f"Google Sheets 초기 연결에 실패했습니다: {exc}")
    st.info("Google Sheets API 활성화, 서비스 계정 편집자 공유, Secrets의 인증정보를 확인하세요.")
    st.stop()

with st.sidebar:
    st.markdown("### NAVER TREND MONITOR")
    st.caption("공용 비밀번호 세션 · 12시간 유지")
    st.page_link("app.py", label="대시보드", icon="📈")
    st.page_link("pages/2_settings.py", label="설정", icon="⚙️")
    if st.button("로그아웃", use_container_width=True):
        sign_out()
        st.rerun()

st.markdown('<p class="olive-title">네쇼검 트렌드 모니터</p>', unsafe_allow_html=True)
st.markdown('<p class="olive-subtitle">소셜 급상승 키워드와 네이버 쇼핑·뉴스·DataLab 데이터를 한 화면에서 분석합니다.</p>',
            unsafe_allow_html=True)

try:
    settings = get_setting("dashboard")
except Exception:
    st.error("공용 설정을 불러오지 못했습니다. Google Sheets 공유 권한과 Secrets를 확인하세요.")
    st.stop()

SAMPLE_SOCIAL = [
    {"keyword": "아크멜로 비타 세럼", "today": 12840, "yesterday": 94},
    {"keyword": "아크멜로비타세럼", "today": 10380, "yesterday": 51},
    {"keyword": "모닝글로우 쿠션", "today": 18810, "yesterday": 220},
    {"keyword": "인기 해시태그", "today": 15120, "yesterday": 9870},
    {"keyword": "루미네 바디미스트", "today": 11420, "yesterday": 40},
]
st.session_state.setdefault("social_rows", SAMPLE_SOCIAL)
st.session_state.setdefault("naver_products", [])

top1, top2, top3 = st.columns([1.2, 1.2, 2])
default_start = date.fromisoformat(settings["collection_start"]) if settings.get("collection_start") else date.today() - timedelta(days=7)
default_end = date.fromisoformat(settings["collection_end"]) if settings.get("collection_end") else date.today()
start_date = top1.date_input("수집 시작일", value=default_start)
end_date = top2.date_input("수집 종료일", value=default_end)
uploaded = top3.file_uploader("소셜 데이터 업로드", type=["csv", "xlsx", "xls"],
                              help="필수 열: keyword, today, yesterday")
if start_date > end_date:
    st.error("수집 시작일은 종료일보다 늦을 수 없습니다.")
    st.stop()
if uploaded:
    try:
        uploaded_frame = read_social_file(uploaded.getvalue(), uploaded.name)
        required = {"keyword", "today", "yesterday"}
        missing = required - set(uploaded_frame.columns)
        if missing:
            raise ValueError(f"필수 열이 없습니다: {', '.join(sorted(missing))}")
        st.session_state.social_rows = uploaded_frame.to_dict("records")
        st.success(f"{len(uploaded_frame):,}건을 불러왔습니다.")
    except Exception as exc:
        st.error(f"파일을 읽지 못했습니다: {exc}")

with st.expander("네이버 API 데이터 가져오기", expanded=True):
    search_tab, news_tab, datalab_tab, insight_tab = st.tabs(["쇼핑 검색", "뉴스 검색", "검색어 DataLab", "쇼핑인사이트"])
    with search_tab:
        shopping_query = st.text_input("쇼핑 검색어", key="shopping_query")
        if st.button("쇼핑 상품 가져오기", use_container_width=True):
            try:
                st.session_state.naver_products = search_shopping(shopping_query)
                st.success(f"쇼핑 결과 {len(st.session_state.naver_products):,}건을 분석에 반영했습니다.")
            except Exception as exc:
                st.error(str(exc))
    with news_tab:
        news_query = st.text_input("뉴스 검색어", key="news_query")
        if st.button("뉴스 가져오기", use_container_width=True):
            try:
                st.session_state.news_items = search_news(news_query)
                st.success(f"뉴스 결과 {len(st.session_state.news_items):,}건")
            except Exception as exc:
                st.error(str(exc))
    with datalab_tab:
        datalab_query = st.text_input("DataLab 검색어", key="datalab_query")
        unit = st.selectbox("조회 단위", ["date", "week", "month"], key="datalab_unit")
        if st.button("검색어 트렌드 조회", use_container_width=True):
            try:
                st.session_state.datalab_items = search_trends(
                    start_date, end_date, [{"groupName": datalab_query, "keywords": [datalab_query]}], time_unit=unit)
                st.success("검색어 트렌드를 불러왔습니다.")
            except Exception as exc:
                st.error(str(exc))
    with insight_tab:
        category_code = st.text_input("네이버 쇼핑 분야 코드", placeholder="예: 50000002")
        insight_query = st.text_input("쇼핑인사이트 키워드")
        i1, i2, i3 = st.columns(3)
        insight_unit = i1.selectbox("구간", ["date", "week", "month"], key="insight_unit")
        device_label = i2.selectbox("기기", ["전체", "PC", "모바일"])
        gender_label = i3.selectbox("성별", ["전체", "여성", "남성"])
        ages = st.multiselect("연령대", ["10", "20", "30", "40", "50", "60"],
                              format_func=lambda value: f"{value}대" if value != "60" else "60대 이상")
        if st.button("쇼핑 클릭 트렌드 조회", use_container_width=True):
            try:
                st.session_state.shopping_insight_items = keyword_trends(
                    start_date, end_date, category_code,
                    [{"name": insight_query, "param": [insight_query]}], time_unit=insight_unit,
                    device={"PC": "pc", "모바일": "mo"}.get(device_label),
                    gender={"여성": "f", "남성": "m"}.get(gender_label), ages=ages)
                st.success("쇼핑인사이트 클릭 트렌드를 불러왔습니다.")
            except Exception as exc:
                st.error(str(exc))

try:
    result = analyze_trends(
        st.session_state.social_rows, st.session_state.naver_products,
        surge_threshold=settings["surge_threshold"], yesterday_max=settings["yesterday_max"],
        match_threshold=settings["match_threshold"])
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.subheader("분석 결과 필터")
f1, f2, f3 = st.columns([2, 1, 1])
keyword_filter = f1.text_input("키워드 포함", placeholder="키워드 또는 브랜드")
surge_filter = f2.selectbox("급상승", ["전체", "급상승만", "일반만"])
match_filter = f3.selectbox("상품 매칭", ["전체", "매칭만", "미매칭만"])
filtered = result.copy()
if keyword_filter:
    term = keyword_filter.casefold()
    filtered = filtered[
        filtered["keyword"].str.casefold().str.contains(term, regex=False)
        | filtered["brand"].fillna("").str.casefold().str.contains(term, regex=False)
        | filtered["matched_product"].fillna("").str.casefold().str.contains(term, regex=False)]
if surge_filter != "전체":
    filtered = filtered[filtered["is_surge"] == (surge_filter == "급상승만")]
if match_filter != "전체":
    filtered = filtered[filtered["matched"] == (match_filter == "매칭만")]

metrics = summary_metrics(filtered)
m1, m2, m3, m4 = st.columns(4)
m1.metric("표시 키워드", f"{metrics['keywords']:,}")
m2.metric("급상승 감지", f"{metrics['surges']:,}")
m3.metric("네이버 매칭", f"{metrics['matched']:,}")
m4.metric("오늘 언급량", f"{metrics['total_today']:,}")

chart_col, table_col = st.columns([1, 1.45])
with chart_col:
    st.subheader("키워드 언급량")
    if filtered.empty:
        st.info("필터 조건에 맞는 결과가 없습니다.")
    else:
        fig = px.bar(filtered.head(20), x="today", y="keyword", color="is_surge", orientation="h",
                     color_discrete_map={True: "#e05252", False: "#24795e"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False,
                          margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
with table_col:
    st.subheader("분석 결과")
    display_columns = ["keyword", "today", "yesterday", "increase", "growth_rate", "is_surge",
                       "brand", "matched_product", "match_score"]
    st.dataframe(filtered[display_columns], use_container_width=True, hide_index=True,
                 column_config={"growth_rate": st.column_config.NumberColumn("증가율", format="%.1f%%"),
                                "match_score": st.column_config.ProgressColumn("매칭", min_value=0, max_value=100)})

csv_data = filtered.to_csv(index=False).encode("utf-8-sig")
xlsx_data = dataframe_to_xlsx(filtered)
d1, d2, d3, d4, d5 = st.columns(5)
d1.download_button("CSV 다운로드", csv_data, "naver_trend_results.csv", "text/csv", use_container_width=True)
d2.download_button("XLSX 다운로드", xlsx_data, "naver_trend_results.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
if d3.button("결과 저장", use_container_width=True):
    try:
        payload = {"period": {"start": start_date.isoformat(), "end": end_date.isoformat()}, "metrics": metrics,
                   "filters": {"keyword": keyword_filter, "surge": surge_filter, "match": match_filter},
                   "rows": json.loads(filtered.to_json(orient="records", force_ascii=False))}
        save_analysis_result(payload)
        if settings.get("alert_enabled") and settings.get("alert_channel") == "teams":
            send_teams_alert(metrics)
        st.success("분석 결과를 Google Sheets에 저장했습니다.")
    except Exception as exc:
        st.error(f"결과 저장 또는 알림 전송에 실패했습니다: {exc}")
if d4.button("Teams 알림", use_container_width=True):
    try:
        send_teams_alert(metrics)
        st.success("Teams 알림을 전송했습니다.")
    except Exception as exc:
        st.error(str(exc))
if d5.button("최근 결과", use_container_width=True):
    try:
        st.session_state.recent_results = recent_results()
    except Exception as exc:
        st.error(f"최근 결과를 불러오지 못했습니다: {exc}")

if st.session_state.get("recent_results"):
    with st.expander("최근 저장 기록", expanded=True):
        history_rows = [{"저장 시각": item["created_at"], **item["result_data"].get("metrics", {})}
                        for item in st.session_state.recent_results]
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)

if st.session_state.get("news_items"):
    with st.expander("뉴스 결과"):
        news_frame = pd.DataFrame(st.session_state.news_items)
        columns = [column for column in ("title_clean", "description_clean", "pubDate", "link") if column in news_frame]
        st.dataframe(news_frame[columns], use_container_width=True, hide_index=True)
for state_key, label in (("datalab_items", "검색어 DataLab 결과"),
                         ("shopping_insight_items", "쇼핑인사이트 결과")):
    if st.session_state.get(state_key):
        with st.expander(label, expanded=True):
            data = trend_frame(st.session_state[state_key])
            if data.empty:
                st.info("조회 결과가 없습니다.")
            else:
                st.line_chart(data, x="기간", y="비율", color="그룹")
                st.dataframe(data, use_container_width=True, hide_index=True)
