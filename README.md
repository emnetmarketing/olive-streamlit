# Olive Streamlit

네이버 쇼핑·뉴스·DataLab과 소셜 키워드를 분석하는 Streamlit 앱입니다. 공용 비밀번호로 로그인하며 설정·분석 결과·실행 기록은 Google Apps Script Web App을 통해 Google Sheets에 저장합니다.

Google Cloud 가입, 결제정보, Google Sheets API 설정, 서비스 계정 또는 JSON 키가 필요하지 않습니다.

## 로그인

- 공용 비밀번호는 Streamlit Secrets의 `APP_PASSWORD`에서만 읽습니다.
- 성공한 브라우저에는 12시간 유효한 HMAC 서명 쿠키를 저장합니다.
- 쿠키, 로그, Google Sheets에는 비밀번호 원문이나 해시를 저장하지 않습니다.
- `APP_PASSWORD`를 변경하면 기존 세션은 자동으로 무효화됩니다.

## 사용하는 Google Sheet

```text
https://docs.google.com/spreadsheets/d/1u3NE0rDElnhfYZ2sv2iLy22juLa2z5fBR5xmUgKznBo/edit
```

Apps Script는 이 문서에 다음 탭과 헤더를 자동 생성합니다.

`settings`:

```text
key | value_json | description | updated_at | updated_by
```

`analysis_results`:

```text
result_id | created_at | created_by | period_start | period_end | metrics_json | filters_json | result_json
```

`audit_logs`:

```text
log_id | created_at | actor | action | target | details_json
```

같은 이름의 탭이 이미 있으면 삭제하거나 초기화하지 않습니다. 빈 탭에는 헤더만 생성합니다. 기존 탭의 1행 헤더가 예상 구조와 다르면 데이터 보호를 위해 변경하지 않고 오류를 반환합니다.

## 1. Apps Script 붙여넣기

1. 위 Google Sheet를 엽니다.
2. 상단 메뉴에서 `확장 프로그램` → `Apps Script`를 누릅니다.
3. Apps Script 편집기에서 왼쪽 `편집기`를 선택합니다.
4. 기본으로 보이는 `Code.gs`의 내용을 모두 지웁니다.
5. 이 저장소의 `google_apps_script/Code.gs` 전체 내용을 복사해 붙여넣습니다.
6. 상단의 저장 아이콘을 누르거나 `Ctrl+S`를 누릅니다.
7. 프로젝트 이름을 묻는다면 `olive-streamlit-sheet-api`로 지정합니다.

`Code.gs`에는 공개 식별자인 Sheet ID만 포함되며 비밀번호, 네이버 키, Teams URL 같은 민감정보는 없습니다.

### 최소 OAuth 권한 설정

이 Web App은 `SpreadsheetApp.openById()`로 지정된 Sheet를 읽고 써야 하므로 다음 Sheets 읽기/쓰기 scope 하나만 사용합니다.

```text
https://www.googleapis.com/auth/spreadsheets
```

Drive, Gmail, 외부 URL 요청 권한은 사용하지 않습니다. `@OnlyCurrentDoc`와 `spreadsheets.currentonly`는 더 좁은 권한이지만, Google 공식 문서상 바운드 스크립트가 Web App으로 실행될 때 `getActiveSpreadsheet()`를 사용할 수 없으므로 이 구조에는 적용할 수 없습니다.

1. Apps Script 왼쪽에서 `프로젝트 설정`을 누릅니다.
2. `편집기에 appsscript.json 매니페스트 파일 표시`를 켭니다.
3. 왼쪽 `편집기`로 돌아가 `appsscript.json`을 누릅니다.
4. 저장소의 `google_apps_script/appsscript.json` 전체 내용을 복사해 기존 내용을 교체하고 저장합니다.
5. 왼쪽 `개요`의 `프로젝트 OAuth 범위`에는 Google Sheets 범위 하나만 표시되는지 확인합니다.

## 2. Web App 배포

1. Apps Script 화면 오른쪽 위 `배포` → `새 배포`를 누릅니다.
2. `유형 선택` 옆 톱니바퀴를 누르고 `웹 앱`을 선택합니다.
3. 설명에 `olive-streamlit v1`을 입력합니다.
4. `다음 사용자로 실행`은 `나`를 선택합니다.
5. `액세스 권한이 있는 사용자`는 `모든 사용자`를 선택합니다.
6. `배포`를 누릅니다.
7. 권한 승인 화면이 나오면 본인 Google 계정을 선택하고 Sheet 접근 권한을 허용합니다.
8. 표시되는 `웹 앱 URL`을 복사합니다. URL은 `/exec`로 끝나야 합니다.

배포 전에 편집기 상단의 함수 선택 메뉴에서 `doGet`을 선택하고 `실행`을 한 번 누르면 소유자 권한 승인 화면을 먼저 완료할 수 있습니다. 이 승인은 Apps Script 소유자 본인에게만 필요하며, `다음 사용자로 실행: 나`로 배포한 Web App 방문자에게 Google 로그인을 요구하지 않습니다.

`This app is blocked`가 계속 표시되면 기존 배포를 재사용하지 말고, 매니페스트 저장 후 `배포` → `배포 관리`에서 기존 배포를 보관처리한 다음 `새 배포`를 만드세요. Google 계정의 보안 설정에서 이 스크립트의 과거 연결을 삭제한 뒤 `doGet`을 다시 실행하면 오래된 광범위 권한 동의를 새 최소 범위로 다시 요청할 수 있습니다.

`/dev`로 끝나는 테스트 URL은 사용하지 마세요. Apps Script Content Service 응답은 Google의 일회용 URL로 리디렉션되며 Streamlit 코드는 이 리디렉션을 자동으로 따라갑니다.

Web App을 `모든 사용자`에게 허용해야 로그인 없는 Streamlit 서버가 호출할 수 있습니다. 따라서 Web App URL 자체를 비밀처럼 관리하고 GitHub, Sheet 셀, 공개 문서에 적지 마세요.

## 3. Streamlit Secrets

로컬 파일 생성:

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

필수 설정:

```toml
GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/배포_ID/exec"
APP_PASSWORD = "직접 정한 강력한 공용 비밀번호"

NAVER_CLIENT_ID = "네이버 Client ID"
NAVER_CLIENT_SECRET = "네이버 Client Secret"
COOKIE_SECURE = false
TEAMS_WEBHOOK_URL = "Teams Webhook HTTPS URL"
```

Google 서비스 계정 블록과 `GOOGLE_SHEET_ID`는 사용하지 않습니다. 실제 `.streamlit/secrets.toml`은 Git에서 제외됩니다.

## 4. 로컬 실행과 확인

```powershell
cd C:\Users\USER\Desktop\olive-streamlit
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

1. `APP_PASSWORD`로 로그인합니다.
2. 첫 연결에서 `settings`, `analysis_results`, `audit_logs`가 자동 생성되는지 Sheet를 새로고침합니다.
3. 설정 화면에서 `Google Sheets 연결 및 구조 확인`을 누릅니다.
4. 설정을 저장하고 `settings`, `audit_logs`를 확인합니다.
5. 분석 결과를 저장하고 `analysis_results`, `audit_logs`를 확인합니다.
6. 네이버 API와 Teams 테스트 알림을 확인합니다.

Web App URL을 브라우저에서 직접 열어도 세 탭 생성 결과가 JSON으로 표시됩니다.

## 5. Apps Script 코드 수정 후 재배포

`Code.gs`를 수정했다면 저장만 해서는 기존 `/exec` 배포에 반영되지 않을 수 있습니다.

1. `배포` → `배포 관리`
2. 현재 Web App 오른쪽의 연필 아이콘
3. 버전에서 `새 버전`
4. `배포`

기존 배포를 업데이트하면 보통 Web App URL은 그대로 유지됩니다.

## 6. 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py components pages services tests
```

단위 테스트는 Apps Script HTTP 응답과 다른 외부 API를 모킹합니다. 실제 연결은 설정 화면의 연결 확인 버튼으로 검증합니다.

## 7. Streamlit Community Cloud

1. GitHub 저장소 `emnetmarketing/olive-streamlit`로 앱을 만듭니다.
2. Main file path를 `app.py`로 설정합니다.
3. Advanced settings → Secrets에 로컬 `secrets.toml` 내용을 붙여넣습니다.
4. `COOKIE_SECURE = true`로 변경합니다.
5. 배포 후 로그인, Sheets 저장, 네이버 API, Teams 알림을 다시 확인합니다.

공식 참고: [Apps Script Web Apps](https://developers.google.com/apps-script/guides/web), [Content Service](https://developers.google.com/apps-script/guides/content)
