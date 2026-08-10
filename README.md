# Olive Streamlit

네이버 검색·뉴스·DataLab·쇼핑인사이트와 업로드한 소셜 데이터를 분석하는 Streamlit 단독 대시보드입니다.

Google Sheets, Google Apps Script, Supabase 또는 별도 Python 서버를 사용하지 않습니다. 네이버 API와 Teams Webhook은 Streamlit 서버에서 직접 호출합니다.

## 주요 기능

- Streamlit Secrets의 공용 비밀번호 로그인
- 서명된 브라우저 쿠키로 12시간 로그인 유지 및 로그아웃
- 네이버 쇼핑 검색, 뉴스 검색, 검색어 DataLab, 쇼핑인사이트 직접 호출
- 급상승 키워드 분석 및 상품 유사도 매칭
- CSV, XLS, XLSX 업로드
- 결과 필터, 표, 차트
- CSV, XLSX 다운로드
- Teams 수동 및 자동 알림
- 분석 기준 설정 UI

일반 설정은 현재 Streamlit 로그인 세션에만 적용됩니다. 별도 데이터베이스가 없으므로 서버가 재시작되거나 새 브라우저 세션을 시작하면 기본값으로 돌아갑니다.

## Secrets 설정

`.streamlit/secrets.toml.example`을 `.streamlit/secrets.toml`로 복사합니다.

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

실제 값을 입력합니다.

```toml
APP_PASSWORD = "직접 정한 강력한 공용 비밀번호"
NAVER_CLIENT_ID = "네이버 개발자센터 Client ID"
NAVER_CLIENT_SECRET = "네이버 개발자센터 Client Secret"
TEAMS_WEBHOOK_URL = "Teams Workflow 또는 Incoming Webhook HTTPS URL"

# 로컬 HTTP에서는 false, HTTPS 배포에서는 true
COOKIE_SECURE = false
```

실제 Secret 파일은 `.gitignore`에 포함되어 GitHub에 커밋되지 않습니다. 인증정보를 화면에서 입력하거나 저장하는 기능도 제공하지 않습니다.

## 로컬 실행

```powershell
cd C:\Users\USER\Desktop\olive-streamlit
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 설정 화면

로그인 후 설정 화면에서 다음과 같은 일반 분석 기준을 변경할 수 있습니다.

- 급상승 기준 언급량
- 상품 매칭 기준
- 전일 최대량
- 수집 시작일과 종료일
- 반복 방식과 수집 시간
- Teams 자동 알림 ON/OFF

쇼핑인사이트 화면에서는 조회할 때마다 기기, 성별, 연령대와 분석 구간을 선택할 수 있습니다.

설정 화면에는 실제 인증정보 대신 아래 상태만 표시됩니다.

- 네이버 API: 연결됨 / 미설정
- Teams: 연결됨 / 미설정

## 테스트

```powershell
python -m compileall -q app.py components pages services tests
python -m unittest discover -s tests -v
```

## Streamlit Community Cloud

1. `emnetmarketing/olive-streamlit` 저장소로 새 앱을 만듭니다.
2. Main file path는 `app.py`로 지정합니다.
3. Advanced settings의 Secrets에 실제 `secrets.toml` 값을 입력합니다.
4. HTTPS 배포이므로 `COOKIE_SECURE = true`로 설정합니다.
5. 배포 후 로그인, 네이버 API, 파일 업로드·다운로드, Teams 알림을 확인합니다.
