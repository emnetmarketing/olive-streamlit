import streamlit as st

from components.auth import sign_in


def render_login() -> None:
    st.markdown("## 네쇼검 트렌드 모니터")
    st.caption("승인된 이메일로 접속")
    st.warning("이 로그인은 비밀번호나 이메일 소유권 확인이 없는 사내 간편 접속 방식입니다. 공개 서비스에는 사용하지 마세요.")
    with st.form("email_login_form"):
        email = st.text_input("이메일", placeholder="name@company.com")
        name = st.text_input("이름", help="처음 접근을 요청할 때 users 시트에 저장됩니다.")
        submitted = st.form_submit_button("접속 또는 승인 요청", use_container_width=True)
    if submitted:
        try:
            profile = sign_in(email, name)
            if profile.approved:
                st.success("접속이 승인되었습니다.")
                st.rerun()
            messages = {"pending": "승인 대기 중입니다. master가 users 시트 또는 관리자 화면에서 승인해야 합니다.",
                        "rejected": "접근 요청이 거절되었습니다.", "disabled": "비활성화된 사용자입니다."}
            st.warning(messages.get(profile.status, "현재 접근할 수 없습니다."))
        except Exception as exc:
            st.error(str(exc))
