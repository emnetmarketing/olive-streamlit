# Olive Streamlit

소셜 키워드와 네이버 쇼핑·뉴스·DataLab 데이터를 분석하는 Streamlit 앱입니다. 사이트 접근은 Streamlit Secrets의 공용 비밀번호 하나로 보호하고, 설정·분석 결과·실행 기록은 Google Sheets에 저장합니다.

## 로그인 방식

- 사이트 접속 시 공용 비밀번호 입력
- 비밀번호는 `APP_PASSWORD` Secret에서만 읽음
- 비교에는 timing attack을 줄이는 constant-time 비교 사용
- 성공하면 브라우저에 12시간 유효한 HMAC 서명 쿠키 저장
- 쿠키에는 비밀번호 원문이나 해시가 들어가지 않음
- 로그아웃 버튼으로 세션 삭제
- 비밀번호를 바꾸면 기존 서명 쿠키도 자동으로 무효화됨

공용 비밀번호를 아는 사람은 모두 같은 권한을 갖습니다. 비밀번호를 채팅·Google Sheets·소스 코드에 기록하지 말고, 필요한 사람에게만 안전한 채널로 전달하세요.

## Google Sheets 구조

Google 스프레드시트에 아래 탭 3개를 만듭니다. 각 탭의 1행에 컬럼을 순서와 철자까지 동일하게 입력하세요.

### `settings`

```text
key | value_json | description | updated_at | updated_by
```

### `analysis_results`

```text
result_id | created_at | created_by | period_start | period_end | metrics_json | filters_json | result_json
```

### `audit_logs`

```text
log_id | created_at | actor | action | target | details_json
```

공용 로그인 구조에서는 실행 주체가 `shared_session`으로 기록됩니다. 비밀번호는 어떤 시트에도 기록되지 않습니다.

시트 탭이 없으면 앱이 자동 생성할 수 있습니다. 하지만 직접 만들면 구조를 확인하기 쉽습니다. 기존에 `users` 탭이 있다면 앱은 읽거나 수정하지 않으므로 필요에 따라 직접 삭제할 수 있습니다.

## 1. Google Cloud와 서비스 계정

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트를 생성하거나 선택합니다.
2. `API 및 서비스` → `라이브러리`에서 `Google Sheets API`를 사용 설정합니다.
3. `IAM 및 관리자` → `서비스 계정` → `서비스 계정 만들기`를 누릅니다.
4. 서비스 계정 이름을 `olive-streamlit`로 지정합니다.
5. 서비스 계정의 `키` → `키 추가` → `새 키 만들기` → `JSON`을 선택합니다.
6. JSON 파일의 `client_email`을 복사합니다.
7. Google Sheet의 `공유`에서 해당 이메일을 편집자로 추가합니다.

서비스 계정 JSON은 GitHub, Google Sheets 또는 코드에 저장하지 마세요.

## 2. Secrets 설정

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml` 예시:

```toml
GOOGLE_SHEET_ID = "Google Sheet URL의 /d/와 /edit 사이 값"
APP_PASSWORD = "직접 정한 강력한 공용 비밀번호"

[gcp_service_account]
type = "service_account"
project_id = "JSON의 project_id"
private_key_id = "JSON의 private_key_id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "JSON의 client_email"
client_id = "JSON의 client_id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "JSON의 client_x509_cert_url"
universe_domain = "googleapis.com"

NAVER_CLIENT_ID = "네이버 Client ID"
NAVER_CLIENT_SECRET = "네이버 Client Secret"
COOKIE_SECURE = false
TEAMS_WEBHOOK_URL = "Teams Webhook HTTPS URL"
```

`APP_PASSWORD`는 최소 8자이며, 충분히 긴 무작위 문구를 권장합니다. 로컬 HTTP에서는 `COOKIE_SECURE=false`, Streamlit Community Cloud에서는 `true`로 설정합니다. 실제 `secrets.toml`은 `.gitignore`에 의해 Git에서 제외됩니다.

## 3. 설치와 로컬 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

확인 순서:

1. 틀린 비밀번호로 접근이 차단되는지 확인
2. `APP_PASSWORD`로 로그인되는지 확인
3. 새로고침 후에도 세션이 유지되는지 확인
4. 로그아웃 후 다시 비밀번호 화면이 표시되는지 확인
5. 설정 화면의 `Google Sheets 연결 및 구조 확인` 실행
6. 설정 저장 후 `settings` 탭 확인
7. 분석 결과 저장 후 `analysis_results`, `audit_logs` 확인
8. 네이버 API와 Teams 테스트 실행

## 4. 주요 기능

- 네이버 쇼핑 검색, 뉴스검색, 검색어 DataLab, 쇼핑인사이트
- CSV/XLS/XLSX 업로드
- 급상승 및 상품 매칭 분석
- 결과 필터, 차트, CSV/XLSX 다운로드
- Google Sheets 설정 및 결과 저장
- Teams Adaptive Card 알림

네이버 Client ID/Secret, Teams Webhook, Google 서비스 계정 인증정보, `APP_PASSWORD`는 모두 Streamlit Secrets에서만 읽습니다.

## 5. 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py components pages services tests
```

단위 테스트는 Google Sheets와 외부 API 요청을 모킹합니다. 실제 Sheets 연결은 설정 화면의 연결 검사 버튼으로 확인합니다.

## 6. Streamlit Community Cloud 배포

1. GitHub 저장소 `emnetmarketing/olive-streamlit`로 앱을 만듭니다.
2. Main file path를 `app.py`로 설정합니다.
3. Advanced settings → Secrets에 로컬 `secrets.toml` 내용을 붙여넣습니다.
4. `COOKIE_SECURE = true`로 바꿉니다.
5. 서비스 계정 이메일이 Google Sheet 편집자로 공유되어 있는지 확인합니다.
6. 배포 후 로그인, Sheets 저장, 네이버 API, Teams 알림을 다시 확인합니다.
