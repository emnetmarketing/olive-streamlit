import streamlit as st


def apply_styles() -> None:
    st.markdown("""
    <style>
      :root { --brand:#6c5cff; --brand-dark:#4f46e5; --mint:#17c8bd; --ink:#071733;
        --muted:#748098; --line:#e7ecf5; --panel:rgba(255,255,255,.94); }
      html, body, [data-testid="stAppViewContainer"] { background:
        radial-gradient(circle at 4% 0%,rgba(108,92,255,.13),transparent 28vw),
        radial-gradient(circle at 88% 8%,rgba(23,200,189,.12),transparent 24vw),
        linear-gradient(180deg,#fbfcff 0%,#f7f9ff 50%,#f4f7fd 100%); color:var(--ink); }
      [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer,
      [data-testid="stSidebarNav"], [data-testid="collapsedControl"] { display:none!important; }
      [data-testid="stAppViewBlockContainer"] { max-width:1480px; padding:1.35rem 1.5rem 3rem 20rem; }
      [data-testid="stSidebar"] { width:292px!important; background:var(--panel); border-right:1px solid var(--line);
        box-shadow:0 18px 48px rgba(64,77,117,.10); }
      [data-testid="stSidebar"] > div:first-child { width:292px!important; padding:1.25rem 1rem; }
      [data-testid="stSidebar"] * { color:var(--ink); }
      .block-container { padding-top:1.2rem; }
      h1,h2,h3,p { letter-spacing:0; }
      .nt-brand { display:flex;align-items:center;gap:11px;padding:4px 3px 18px;border-bottom:1px solid var(--line);margin-bottom:12px; }
      .nt-mark { display:grid;place-items:center;width:36px;height:36px;border-radius:11px;color:white;font-weight:900;
        background:linear-gradient(135deg,#5aa7ff,#7b55ff);box-shadow:0 12px 24px rgba(108,92,255,.25); }
      .nt-brand strong { display:block;font-size:15px; }.nt-brand small { color:var(--muted);font-size:11px; }
      .nt-eyebrow { color:var(--brand-dark);font-size:12px;font-weight:900;letter-spacing:.08em;margin-bottom:5px; }
      .nt-title { margin:0;font-size:28px;font-weight:900;color:var(--ink);line-height:1.2; }
      .nt-header { padding:8px 0 12px; }
      div[data-testid="stVerticalBlockBorderWrapper"] { border:1px solid var(--line)!important;border-radius:18px!important;
        background:var(--panel)!important;box-shadow:0 18px 48px rgba(64,77,117,.09)!important;padding:4px!important; }
      div[data-baseweb="tab-list"] { gap:5px;background:#f3f5fc;border-radius:12px;padding:4px; }
      button[data-baseweb="tab"] { border-radius:9px!important;font-weight:800!important; }
      button[data-baseweb="tab"][aria-selected="true"] { background:white!important;color:var(--brand-dark)!important;
        box-shadow:0 4px 14px rgba(64,77,117,.10); }
      .stButton>button, .stDownloadButton>button { min-height:40px;border-radius:11px;border:1px solid transparent;
        font-weight:800;background:linear-gradient(135deg,#5673ff,#7c55ff);color:white;
        box-shadow:0 10px 22px rgba(92,93,255,.21); }
      .stButton>button:hover,.stDownloadButton>button:hover { color:white;border-color:transparent;transform:translateY(-1px); }
      [data-testid="stDateInput"] input, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
      [data-testid="stSelectbox"]>div>div { border-radius:11px!important;border-color:#dfe6f3!important;background:white!important; }
      .nt-panel { background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:20px;
        box-shadow:0 18px 48px rgba(64,77,117,.09);margin:0 0 18px; }
      .nt-panel-title { font-size:16px;font-weight:900;color:var(--ink);margin:0 0 16px; }
      .nt-stats { display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px; }
      .nt-stat { min-height:118px;padding:20px;border:1px solid var(--line);border-radius:18px;position:relative;overflow:hidden;
        background:linear-gradient(145deg,#fff,#f7f9ff);box-shadow:0 10px 24px rgba(80,96,132,.07); }
      .nt-stat:after { content:"";position:absolute;right:18px;top:16px;width:44px;height:44px;border-radius:16px;
        background:linear-gradient(135deg,rgba(108,92,255,.22),rgba(23,200,189,.14)); }
      .nt-stat b { display:block;font-size:29px;line-height:1.1;margin:16px 0 7px;color:var(--ink); }
      .nt-stat span { color:var(--muted);font-size:12px; }
      .nt-trend-row { display:grid;grid-template-columns:minmax(150px,1.35fr) minmax(220px,2fr) 125px;gap:14px;
        align-items:center;padding:13px 0;border-bottom:1px solid #edf1f7; }
      .nt-trend-row:last-child { border-bottom:0; }.nt-trend-name{font-size:13px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
      .nt-trend-sub{display:block;margin-top:4px;color:var(--muted);font-size:11px;font-weight:700;}
      .nt-track{height:12px;border-radius:999px;background:#edf2fb;overflow:hidden}.nt-fill{height:100%;border-radius:inherit;
        background:linear-gradient(90deg,var(--mint),var(--brand));box-shadow:0 8px 18px rgba(108,92,255,.20)}
      .nt-trend-value{text-align:right;font-size:13px;font-weight:900}.nt-trend-value small{display:block;color:var(--brand-dark);margin-top:3px}
      .nt-empty{padding:18px;color:var(--muted);border:1px dashed #dce4f2;border-radius:16px;background:#fbfcff;font-size:13px}
      .nt-table-wrap{overflow:auto;border:1px solid var(--line);border-radius:16px;max-height:480px;background:white}
      .nt-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px}.nt-table th,.nt-table td{padding:14px 11px;
        border-bottom:1px solid #edf1f7;text-align:left;vertical-align:middle;word-break:break-word}.nt-table th{color:#7a8498;background:#f7f9fd;font-size:11px;position:sticky;top:0}
      .nt-pill{display:inline-flex;padding:4px 8px;border-radius:999px;background:#e8fbf5;color:#12a878;font-weight:800}
      .nt-pill.warn{background:#fff0d9;color:#9b4e00}.nt-pill.bad{background:#ffe9e8;color:#ef4444}
      .nt-note{border:1px solid #ede7ff;background:linear-gradient(135deg,#f7f4ff,#eef9ff);padding:12px;border-radius:14px;
        color:#4d5570;font-size:12px;line-height:1.5;margin:8px 0 14px}
      [data-testid="stFileUploader"] section { border-radius:13px;border-color:#dfe6f3;background:#fafbff; }
      div[data-testid="stForm"] { border:1px solid var(--line);border-radius:24px;background:rgba(255,255,255,.97);
        box-shadow:0 24px 70px rgba(64,77,117,.16);padding:28px; }
      div[data-testid="stFormSubmitButton"] button { background:linear-gradient(135deg,#5673ff,#7c55ff)!important;
        color:white!important;border-color:transparent!important; }
      .nt-login-wrap { max-width:520px;margin:10vh auto 0;text-align:left; }
      @media(max-width:1050px){[data-testid="stAppViewBlockContainer"]{padding-left:1.2rem}.nt-stats{grid-template-columns:repeat(2,1fr)}
        [data-testid="stSidebar"]{position:relative;width:100%!important}.nt-trend-row{grid-template-columns:1fr}}
    </style>
    """, unsafe_allow_html=True)
