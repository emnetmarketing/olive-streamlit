# Olive Streamlit

네이버 쇼핑·뉴스·DataLab 데이터와 소셜 키워드를 결합해 급상승 키워드를 분석하는 독립 Streamlit 애플리케이션입니다. Supabase Auth, Row Level Security, 공용 설정, 사용자 권한 관리 및 분석 결과 저장을 지원합니다.

## 프로젝트 구조

```text
app.py                         Streamlit 메인 대시보드
pages/2_settings.py            공용 설정과 보관 정책
pages/3_user_management.py     사용자 승인 및 권한 관리
components/                    인증, 세션, 설정, UI 스타일
models/                        데이터 모델
services/                      Supabase, 분석, 네이버 API 연동
sql/supabase_schema.sql        DB 테이블, 함수, RLS 정책
tests/                         단위 테스트
```

이 저장소는 Python/Streamlit 앱 전용입니다. 기존 HTML 및 Netlify 운영 파일은 포함하지 않습니다.

## 요구 사항

- Python 3.11 이상
- Supabase 프로젝트
- 네이버 검색 및 DataLab API 자격 증명

## 로컬 실행

```powershell
python -m pip install -r requirements.txt
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
python -m streamlit run app.py
```

`.streamlit/secrets.toml`에 실제 값을 입력합니다. 이 파일은 Git에 포함되지 않습니다.

## Secrets

필수 항목:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `NAVER_CLIENT_ID`
- `NAVER_CLIENT_SECRET`
- `SESSION_ENCRYPTION_KEY`

세션 암호화 키 생성 예시:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Supabase 준비

1. Supabase 프로젝트를 생성합니다.
2. SQL Editor에서 `sql/supabase_schema.sql`을 실행합니다.
3. Authentication에서 Email 로그인을 활성화합니다.
4. 최초 사용자를 가입시킨 후 해당 프로필을 `master`, `approved` 상태로 설정합니다.
5. Streamlit 배포 환경에 위 Secrets를 등록합니다.

## 테스트

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py components models pages services tests
```

외부 Supabase 및 네이버 API 통합 검증에는 별도의 실제 자격 증명이 필요합니다. 자격 증명을 테스트 출력이나 Git 기록에 남기지 마세요.

## 배포

Streamlit Community Cloud에서 이 저장소를 연결하고 Main file path를 `app.py`로 지정합니다. 실제 Secrets는 저장소 파일이 아니라 배포 환경의 Secrets 설정에 등록합니다.
