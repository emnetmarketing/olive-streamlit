# Olive Streamlit

소셜 키워드와 네이버 쇼핑·뉴스·DataLab 데이터를 결합해 급상승 키워드를 분석하는 Streamlit 전용 애플리케이션입니다. 기존 HTML/Netlify 프로젝트와 독립적으로 운영됩니다.

## 제공 기능

- Supabase 이메일 회원가입·로그인과 가입 직후 `pending` 처리
- 마스터 승인 후 대시보드 접근
- `master`, `editor`, `operator` 권한
- 승인, 거절, 권한 변경, 비활성화, 계정 삭제, 감사 기록
- 암호화된 브라우저 쿠키를 이용한 로그인 세션 복원
- Supabase DB에 공용 설정과 분석 결과 저장
- 네이버 쇼핑 검색, 뉴스 검색, 검색어 DataLab, 쇼핑인사이트 API
- CSV/XLS/XLSX 업로드, 결과 필터, 차트, CSV/XLSX 다운로드
- Teams Workflow 또는 Incoming Webhook 알림
- Supabase RLS와 마스터 수 제한

비밀번호는 애플리케이션 DB가 아닌 Supabase Auth에서 관리합니다. 네이버 Client ID/Secret, Supabase 키, Teams Webhook은 코드나 DB에 저장하지 않습니다.

## 프로젝트 구조

```text
app.py                         메인 대시보드
pages/2_settings.py            분석·보관·알림 설정
pages/3_user_management.py     사용자 및 권한 관리
components/                    인증, 쿠키 세션, UI
models/                        사용자 모델
services/                      분석, Supabase, 네이버 API, Teams, 내보내기
sql/supabase_schema.sql        테이블, 함수, 트리거, RLS
tests/                         단위 테스트
```

## 1. Python 준비

Python 3.11 이상을 권장합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2. Supabase 준비

1. Supabase에서 새 프로젝트를 만듭니다.
2. SQL Editor에 `sql/supabase_schema.sql` 전체를 붙여 넣고 한 번 실행합니다.
3. Authentication → Providers에서 Email 로그인을 활성화합니다.
4. 이메일 확인을 사용할 경우 Authentication의 Site URL과 Redirect URL을 배포 주소에 맞춥니다.
5. 앱에서 최초 관리자 계정으로 회원가입합니다.
6. Table Editor의 `profiles`에서 사용자 UUID를 확인합니다.
7. SQL Editor에서 최초 마스터를 승인합니다.

```sql
update public.profiles
set role = 'master', status = 'approved', approved_at = now()
where email = 'admin@example.com';
```

마스터는 승인 상태로 최소 1명, 최대 2명입니다. 마지막 마스터의 강등·비활성화·삭제와 세 번째 마스터 승인은 DB 트리거가 차단합니다.

## 3. Secrets 설정

예시 파일을 복사합니다.

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

다음 값을 입력합니다.

```toml
SUPABASE_URL = "https://PROJECT.supabase.co"
SUPABASE_ANON_KEY = "..."
SUPABASE_SERVICE_ROLE_KEY = "..."
NAVER_CLIENT_ID = "..."
NAVER_CLIENT_SECRET = "..."
SESSION_ENCRYPTION_KEY = "..."
COOKIE_SECURE = false
TEAMS_WEBHOOK_URL = "https://..."
```

- Supabase URL과 키: Project Settings → API
- 네이버 키: 네이버 개발자 센터에서 검색, DataLab 검색어 트렌드, DataLab 쇼핑인사이트 API를 등록
- Service Role Key: 사용자 승인·삭제 같은 관리자 작업에만 서버에서 사용
- `SESSION_ENCRYPTION_KEY`: 아래 명령으로 생성

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

로컬 HTTP에서는 `COOKIE_SECURE = false`, HTTPS 배포에서는 `true`를 사용합니다. 실제 `.streamlit/secrets.toml`은 `.gitignore`에 포함되어 있습니다.

## 4. Teams 알림 준비

Teams 채널의 Workflows에서 “웹후크 요청을 받으면 채널에 게시” 유형의 Workflow를 만들고 생성된 HTTPS URL을 `TEAMS_WEBHOOK_URL`에 저장합니다. 업무 연속성을 위해 Workflow 공동 소유자를 지정하는 것을 권장합니다. 기존 Incoming Webhook URL도 Adaptive Card POST를 받는 경우 사용할 수 있습니다.

설정 화면의 “Teams 테스트 알림 보내기”로 연결을 확인합니다. 분석 설정에서 알림을 활성화하면 결과 저장 시 Teams 알림도 전송됩니다.

## 5. 실행

```powershell
python -m streamlit run app.py
```

브라우저가 열리면 회원가입 → 마스터 승인 → 로그인 순서로 진행합니다.

## 6. 데이터 형식

CSV/XLS/XLSX 파일에는 다음 열이 필요합니다.

| 열 | 의미 |
|---|---|
| `keyword` | 분석 키워드 |
| `today` | 오늘 언급량 |
| `yesterday` | 전일 언급량 |

같은 키워드가 여러 행이면 오늘/전일 언급량을 합산합니다.

쇼핑인사이트에는 네이버 쇼핑 카테고리 URL의 `cat_id` 분야 코드를 입력해야 합니다. API 결과의 비율은 절대 클릭 수가 아니라 조회 범위 내 최대값을 100으로 둔 상대값입니다.

## 7. 권한

| 기능 | master | editor | operator |
|---|---:|---:|---:|
| 대시보드/API/결과 조회 | 가능 | 가능 | 가능 |
| 분석 결과 저장 | 가능 | 가능 | 가능 |
| 공용 설정 변경 | 가능 | 가능 | 불가 |
| 사용자 승인·권한·삭제 | 가능 | 불가 | 불가 |

## 8. 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py components models pages services tests
```

실제 Supabase·네이버·Teams 통합 테스트에는 배포 환경의 자격 증명이 필요합니다. 단위 테스트는 외부 요청을 모킹하며 자격 증명을 출력하지 않습니다.

## 9. Streamlit Community Cloud 배포

1. 이 GitHub 저장소로 새 Streamlit 앱을 만듭니다.
2. Main file path를 `app.py`로 지정합니다.
3. Advanced settings → Secrets에 `.streamlit/secrets.toml.example` 형식으로 실제 값을 등록합니다.
4. `COOKIE_SECURE = true`로 설정합니다.
5. 배포 후 회원가입, 승인, API 조회, 결과 저장, Teams 테스트를 순서대로 확인합니다.

Secrets 값을 바꾸면 기존 로그인 쿠키가 무효화될 수 있습니다. 특히 `SESSION_ENCRYPTION_KEY` 변경 후에는 사용자가 다시 로그인해야 합니다.
