# Olive Streamlit

소셜 키워드와 네이버 쇼핑·뉴스·DataLab 데이터를 결합해 급상승 키워드를 분석하는 Streamlit 앱입니다. 사용자·설정·분석 결과·실행 기록은 관리자가 직접 열어볼 수 있는 Google Sheets에 저장합니다.

## 중요: 간편 이메일 접속의 보안 범위

이 앱은 요청에 따라 비밀번호와 이메일 인증 없이 입력한 이메일을 `users` 시트에서 확인합니다. 따라서 이메일 주소를 아는 사람이 그 사용자인 것처럼 입력할 수 있습니다. 사내망, 제한된 Streamlit 배포, 신뢰할 수 있는 소규모 사용자 환경에만 사용하세요. 공개 인터넷 서비스에는 Google OAuth 같은 실제 본인 인증이 필요합니다.

비밀번호는 수집하거나 저장하지 않습니다. 네이버 키, Teams Webhook, Google 서비스 계정 인증정보도 Google Sheets에 저장하지 않고 Streamlit Secrets에서만 읽습니다.

## 기능

- 미등록 이메일의 `pending/operator` 접근 요청 자동 등록
- `approved` 사용자만 대시보드 접속
- `master`, `editor`, `operator` 권한
- 관리자 화면에서 승인·거절·비활성화·권한 변경
- Google Sheet를 직접 열어 사용자와 설정 수정 가능
- 설정, 분석 결과, 감사/실행 기록 저장
- 네이버 쇼핑 검색, 뉴스, 검색어 DataLab, 쇼핑인사이트
- CSV/XLS/XLSX 업로드, 필터, 차트, CSV/XLSX 다운로드
- Teams 알림

## 1. Google Sheet 만들기

1. Google Drive에서 `새로 만들기` → `Google 스프레드시트`를 누릅니다.
2. 파일 이름을 `olive-streamlit-data`로 지정합니다.
3. 아래 이름으로 시트 탭 4개를 만듭니다.
4. 각 시트의 1행에 아래 컬럼을 순서와 철자까지 동일하게 입력합니다.

### `users`

```text
user_id | email | name | status | role | created_at | updated_at | approved_at | approved_by | last_login_at
```

- `status`: `pending`, `approved`, `rejected`, `disabled`
- `role`: `master`, `editor`, `operator`
- 첫 master는 `user_id`에 임의의 고유 문자열, 이메일과 이름을 입력하고 `status=approved`, `role=master`로 직접 추가할 수 있습니다.

### `settings`

```text
key | value_json | description | updated_at | updated_by
```

처음에는 헤더만 있어도 됩니다. 앱 설정 화면에서 저장하면 `dashboard`, `retention` 행이 생성됩니다. `value_json`은 JSON이므로 따옴표와 쉼표를 유지하세요.

### `analysis_results`

```text
result_id | created_at | created_by_email | period_start | period_end | metrics_json | filters_json | result_json
```

### `audit_logs`

```text
log_id | created_at | actor_email | action | target_email | details_json
```

시트가 없으면 앱이 자동 생성할 수도 있지만, 직접 만들면 구조를 미리 확인하기 쉽습니다. 1행 컬럼이 다르면 앱은 데이터 손상을 막기 위해 오류를 표시합니다.

스프레드시트 URL이 다음과 같다면 `/d/`와 `/edit` 사이가 `GOOGLE_SHEET_ID`입니다.

```text
https://docs.google.com/spreadsheets/d/GOOGLE_SHEET_ID/edit
```

## 2. Google Cloud 서비스 계정 만들기

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트를 새로 만들거나 선택합니다.
2. `API 및 서비스` → `라이브러리`에서 `Google Sheets API`를 검색해 사용 설정합니다.
3. `IAM 및 관리자` → `서비스 계정` → `서비스 계정 만들기`를 누릅니다.
4. 이름을 `olive-streamlit`로 지정합니다. 프로젝트 역할은 별도로 부여하지 않아도 됩니다.
5. 생성한 서비스 계정을 열고 `키` → `키 추가` → `새 키 만들기` → `JSON`을 선택합니다.
6. 내려받은 JSON은 외부에 공유하거나 Git에 추가하지 마세요.
7. JSON의 `client_email` 값을 복사합니다.
8. 앞에서 만든 Google Sheet의 `공유`를 누르고 `client_email`을 편집자로 추가합니다.

서비스 계정은 별도 Google 계정처럼 동작하므로 Sheet를 공유하기 전에는 접근할 수 없습니다.

## 3. 로컬 Secrets 설정

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

JSON 파일의 각 값을 `.streamlit/secrets.toml`의 `[gcp_service_account]` 아래에 옮깁니다. `private_key`의 줄바꿈은 `\n` 형태를 유지합니다.

필수 값:

```toml
GOOGLE_SHEET_ID = "스프레드시트 ID"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

추가 Secrets:

```toml
NAVER_CLIENT_ID = "..."
NAVER_CLIENT_SECRET = "..."
SESSION_ENCRYPTION_KEY = "..."
COOKIE_SECURE = false
TEAMS_WEBHOOK_URL = "https://..."
```

세션 암호화 키 생성:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

실제 `.streamlit/secrets.toml`은 Git에서 제외됩니다.

## 4. Python 설치와 실행

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

처음 로그인 화면에서 master 이메일과 이름을 입력합니다. 미등록 상태라면 `users`에 pending 행이 생깁니다. Sheet에서 해당 행을 `status=approved`, `role=master`로 바꾼 후 다시 접속합니다.

설정 화면의 `Google Sheets 연결 및 구조 확인` 버튼으로 4개 시트 연결을 검사할 수 있습니다.

## 5. 권한

| 기능 | master | editor | operator |
|---|---:|---:|---:|
| 대시보드와 API | 가능 | 가능 | 가능 |
| 결과 저장 | 가능 | 가능 | 가능 |
| 설정 변경 | 가능 | 가능 | 불가 |
| 사용자 승인·권한 관리 | 가능 | 불가 | 불가 |

승인된 master는 최소 1명, 최대 2명으로 앱에서 검사합니다. Google Sheet를 직접 수정하면 이 검사를 우회할 수 있으므로 마지막 master를 삭제하거나 master를 3명 이상 승인하지 마세요.

## 6. 네이버와 Teams

네이버 개발자 센터에서 검색, DataLab 검색어 트렌드, DataLab 쇼핑인사이트 API를 등록하고 Client ID/Secret을 Secrets에 넣습니다. Teams 채널의 Workflows에서 Webhook 요청을 받는 Workflow를 만든 뒤 URL을 `TEAMS_WEBHOOK_URL`에 넣습니다.

## 7. 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py components models pages services tests
```

단위 테스트는 Google API와 외부 HTTP 호출을 모킹합니다. 실제 연동은 설정 화면의 Sheets 연결 버튼, 네이버 조회, Teams 테스트 알림으로 확인합니다.

## 8. Streamlit Community Cloud

1. 이 GitHub 저장소로 앱을 만들고 Main file path를 `app.py`로 지정합니다.
2. Advanced settings → Secrets에 로컬 `secrets.toml` 내용을 붙여넣습니다.
3. `COOKIE_SECURE = true`로 변경합니다.
4. 서비스 계정 이메일이 Google Sheet 편집자로 공유되어 있는지 확인합니다.
5. 배포 후 이메일 접속, 설정 저장, 결과 저장, 네이버 API, Teams 알림을 확인합니다.

## 저장소 구조

```text
app.py
components/                    이메일 접속, 암호화 쿠키, UI
models/                        사용자 모델
pages/                         설정, 사용자 관리
services/google_sheets_service.py
services/                      분석, 네이버, Teams, 내보내기
tests/
```
