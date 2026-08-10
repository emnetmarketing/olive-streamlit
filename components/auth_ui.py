import streamlit as st

from components.auth import authenticate


def render_login() -> None:
    st.markdown('<div class="nt-login-wrap"><div class="nt-eyebrow">SECURE ACCESS</div>'
                '<h1 class="nt-title">네쇼검 트렌드 모니터</h1>'
                '<p style="color:#748098;margin:8px 0 20px">공용 비밀번호를 입력하면 모니터링 대시보드로 이동합니다.</p></div>',
                unsafe_allow_html=True)
    with st.form("shared_password_login", clear_on_submit=True):
        password = st.text_input("비밀번호", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("로그인", use_container_width=True)
    if submitted:
        try:
            if authenticate(password):
                st.success("로그인했습니다.")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
        except Exception as exc:
            st.error(str(exc))
