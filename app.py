import streamlit as st
import requests
import pandas as pd
from datetime import date
from streamlit import config as _config

# ─── CONFIG ──────────────────────────────────────────────────────
API = "http://localhost:8000"

st.set_page_config(
    page_title="BloodBank Pro",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── GLOBAL CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0f;
    color: #f0eee8;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 20%, #1a0a1e 0%, #0a0a0f 50%, #0a0f1a 100%);
}
h1, h2, h3 { font-family: 'Syne', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }

.stButton > button {
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    letter-spacing: 0.02em;
    transition: all 0.2s ease;
    border: none;
}
.stButton > button[kind="primary"],
div[data-testid="column"] .stButton > button {
    background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%);
    color: white;
    padding: 0.55rem 1.4rem;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
.stDateInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #f0eee8 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > label, .stNumberInput > label,
.stSelectbox > label, .stDateInput > label {
    color: rgba(240,238,232,0.7) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    overflow: hidden;
}
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem;
}
.stSuccess > div { background: rgba(39,174,96,0.15) !important; border-color: #27ae60 !important; border-radius: 10px !important; }
.stError > div   { background: rgba(231,76,60,0.15)  !important; border-color: #e74c3c !important; border-radius: 10px !important; }
.stWarning > div { background: rgba(241,196,15,0.15) !important; border-color: #f1c40f !important; border-radius: 10px !important; }
.stInfo > div    { background: rgba(52,152,219,0.15) !important; border-color: #3498db !important; border-radius: 10px !important; }
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04);
    border-radius: 12px; padding: 4px; gap: 2px;
    border: 1px solid rgba(255,255,255,0.08);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px; color: rgba(240,238,232,0.6);
    font-family: 'DM Sans', sans-serif; font-weight: 500; padding: 0.45rem 1.1rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #c0392b, #e74c3c) !important; color: white !important;
}
hr { border-color: rgba(255,255,255,0.08); }
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03);
    border-right: 1px solid rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

# ─── API HELPERS ─────────────────────────────────────────────────
def api_get(path):
    try:
        r = requests.get(f"{API}{path}", timeout=8)
        return r.json() if r.ok else []
    except:
        return []

def api_post(path, data):
    try:
        r = requests.post(f"{API}{path}", json=data, timeout=8)
        return r.json(), r.ok
    except Exception as e:
        return {"detail": str(e)}, False

def api_put(path, data):
    try:
        r = requests.put(f"{API}{path}", json=data, timeout=8)
        return r.json(), r.ok
    except Exception as e:
        return {"detail": str(e)}, False

def api_delete(path):
    try:
        r = requests.delete(f"{API}{path}", timeout=8)
        return r.json(), r.ok
    except Exception as e:
        return {"detail": str(e)}, False

def next_id(records, key):
    if not records: return 1
    return max(r.get(key, 0) for r in records) + 1

# ─── REUSABLE UI COMPONENTS ──────────────────────────────────────
def stat_card(label, value, color="#e74c3c", icon="🩸", subtitle=""):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(255,255,255,0.06) 0%,rgba(255,255,255,0.02) 100%);
        border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:1.4rem 1.5rem;
        position:relative;overflow:hidden;min-height:110px;">
        <div style="position:absolute;top:-10px;right:-10px;font-size:4rem;opacity:0.08;">{icon}</div>
        <div style="color:rgba(240,238,232,0.55);font-size:0.72rem;font-weight:600;
            letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">{label}</div>
        <div style="font-family:'Syne',sans-serif;font-size:2.4rem;font-weight:800;
            color:{color};line-height:1;">{value}</div>
        <div style="color:rgba(240,238,232,0.4);font-size:0.75rem;margin-top:0.35rem;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def section_header(title, subtitle="", icon=""):
    st.markdown(f"""
    <div style="margin:1.5rem 0 1rem 0;">
        <div style="display:flex;align-items:center;gap:0.6rem;">
            <span style="font-size:1.4rem;">{icon}</span>
            <h2 style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;
                margin:0;color:#f0eee8;">{title}</h2>
        </div>
        <p style="color:rgba(240,238,232,0.45);font-size:0.85rem;margin:0.25rem 0 0 2.1rem;">{subtitle}</p>
    </div>""", unsafe_allow_html=True)

def page_header(title, subtitle=""):
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid rgba(255,255,255,0.08);">
        <h1 style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;margin:0;
            background:linear-gradient(135deg,#e74c3c,#ff6b6b);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">{title}</h1>
        <p style="color:rgba(240,238,232,0.5);margin:0.3rem 0 0 0;font-size:0.9rem;">{subtitle}</p>
    </div>""", unsafe_allow_html=True)

# ─── SESSION STATE ───────────────────────────────────────────────
if "page" not in st.session_state: st.session_state.page = "landing"
if "user" not in st.session_state: st.session_state.user = None

def go(page):
    st.session_state.page = page
    st.rerun()

# ─── helpers to check identity ───────────────────────────────────
def is_system_admin():
    u = st.session_state.user
    return u and u.get("user_type") == "system_admin"

def is_staff_admin():
    # There is no "Admin" role in STAFF table anymore.
    # Full access via staff is not applicable — only System Admin has it.
    return False

def has_full_access():
    """System admin OR staff admin both get full access."""
    return is_system_admin() or is_staff_admin()

def get_role_display():
    u = st.session_state.user
    if not u: return ""
    return u.get("role", "")

def get_name_display():
    u = st.session_state.user
    if not u: return "User"
    return u.get("fullname", u.get("username", "User"))

# ═══════════════════════════════════════════════════════════════════
# LANDING PAGE
# ═══════════════════════════════════════════════════════════════════
def landing():
    st.markdown("""
    <style>
    .hero-wrap { min-height:88vh; display:flex; flex-direction:column;
        align-items:center; justify-content:center; text-align:center; padding:3rem 1rem; }
    .hero-badge { display:inline-block; background:rgba(231,76,60,0.18);
        border:1px solid rgba(231,76,60,0.35); color:#e74c3c;
        font-size:0.72rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase;
        padding:0.35rem 1rem; border-radius:999px; margin-bottom:1.8rem; }
    .hero-title { font-family:'Syne',sans-serif; font-size:clamp(3rem,7vw,6rem);
        font-weight:800; line-height:1.05; margin:0 0 0.5rem 0; letter-spacing:-0.02em; }
    .hero-title span { background:linear-gradient(135deg,#e74c3c 0%,#ff8a80 60%,#c0392b 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
    .hero-sub { color:rgba(240,238,232,0.5); font-size:1.15rem; max-width:540px;
        margin:1rem auto 2.5rem auto; line-height:1.7; }
    .feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1rem;
        max-width:750px; margin:0 auto 3rem auto; text-align:left; }
    .feature-card { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
        border-radius:14px; padding:1.1rem 1.2rem; }
    .feature-icon { font-size:1.6rem; margin-bottom:0.5rem; }
    .feature-title { font-family:'Syne',sans-serif; font-size:0.9rem; font-weight:700;
        color:#f0eee8; margin-bottom:0.25rem; }
    .feature-desc { color:rgba(240,238,232,0.45); font-size:0.78rem; line-height:1.5; }
    .orb1 { position:fixed; top:-150px; left:-150px; width:600px; height:600px;
        border-radius:50%; background:radial-gradient(circle,rgba(192,57,43,0.15) 0%,transparent 70%);
        pointer-events:none; z-index:0; }
    .orb2 { position:fixed; bottom:-200px; right:-200px; width:700px; height:700px;
        border-radius:50%; background:radial-gradient(circle,rgba(41,128,185,0.08) 0%,transparent 70%);
        pointer-events:none; z-index:0; }
    </style>
    <div class="orb1"></div><div class="orb2"></div>
    <div class="hero-wrap">
        <div class="hero-badge">🩸 Blood Inventory and Tracking System</div>
        <h1 class="hero-title">Save Lives with<br><span>Smarter Management</span></h1>
        <p class="hero-sub">A complete hospital blood bank solution — track inventory, manage donors,
            issue blood safely with automated safety checks.</p>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">🛡️</div>
                <div class="feature-title">Safety Triggers</div>
                <div class="feature-desc">Auto-blocking of expired or untested blood bags</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Live Dashboard</div>
                <div class="feature-desc">Real-time blood inventory &amp; issuance tracking</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">👤</div>
                <div class="feature-title">Role-Based Access</div>
                <div class="feature-desc">Admin, Receptionist &amp; Nurse access controls</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧪</div>
                <div class="feature-title">Lab Testing</div>
                <div class="feature-desc">Record HB levels &amp; test results per bag</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🏥</div>
                <div class="feature-title">Multi-Hospital</div>
                <div class="feature-desc">Manage multiple hospital units from one place</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">FastAPI Backend</div>
                <div class="feature-desc">Lightning-fast Oracle DB integration</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔐  Login to System", use_container_width=True, type="primary"):
            go("login")


# ═══════════════════════════════════════════════════════════════════
# LOGIN PAGE  — two tabs: Staff  |  System Admin
# ═══════════════════════════════════════════════════════════════════
def login_page():
    st.markdown("""
    <style>
    .login-card { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1);
        border-radius:24px; padding:2.5rem 3rem; backdrop-filter:blur(20px);
        box-shadow:0 40px 80px rgba(0,0,0,0.4),0 0 0 1px rgba(255,255,255,0.05); text-align:center; }
    .login-logo { font-size:3.5rem; margin-bottom:0.5rem; }
    .login-title { font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800;
        color:#f0eee8; margin-bottom:0.25rem; }
    .login-sub { color:rgba(240,238,232,0.45); font-size:0.85rem; margin-bottom:1.5rem; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">🩸</div>
            <div class="login-title">Blood Inventory & Tracking</div>
            <div class="login-sub">Sign in to continue</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("### ")

        tab_staff, tab_admin = st.tabs(["👤 Staff Login", "🔑 System Admin Login"])

        # ── STAFF TAB ─────────────────────────────────────────────
        with tab_staff:
            with st.form("staff_login_form"):
                staff_id = st.number_input("Staff ID", min_value=1, step=1,
                                           placeholder="Enter your Staff ID")
                password = st.text_input("Password", type="password",
                                         placeholder="Enter your password")
                col_l, col_r = st.columns(2)
                with col_l:
                    if st.form_submit_button("← Back", use_container_width=True):
                        go("landing")
                with col_r:
                    staff_submitted = st.form_submit_button("Login →", use_container_width=True,
                                                            type="primary")

            if staff_submitted:
                if staff_id and password:
                    data, ok = api_post("/auth/login",
                                        {"staff_id": int(staff_id), "password": password})
                    if ok:
                        st.session_state.user = data
                        go("overview")
                    else:
                        st.error("❌ " + data.get("detail", "Invalid credentials"))

            st.markdown("""
            <div style="text-align:center;margin-top:1rem;padding:0.8rem;
                background:rgba(255,255,255,0.03);border-radius:10px;
                border:1px solid rgba(255,255,255,0.07);">
                <div style="color:rgba(240,238,232,0.4);font-size:0.78rem;margin-bottom:0.3rem;">
                    Demo Credentials</div>
                <div style="color:rgba(240,238,232,0.6);font-size:0.82rem;">
                    Staff ID: <b>101</b> &nbsp;|&nbsp; Password: <b>Admin@123</b></div>
            </div>""", unsafe_allow_html=True)

        # ── SYSTEM ADMIN TAB ──────────────────────────────────────
        with tab_admin:
            with st.form("admin_login_form"):
                adm_user = st.text_input("Username", placeholder="Enter admin username")
                adm_pass = st.text_input("Password", type="password",
                                         placeholder="Enter admin password")
                col_l2, col_r2 = st.columns(2)
                with col_l2:
                    if st.form_submit_button("← Back", use_container_width=True):
                        go("landing")
                with col_r2:
                    adm_submitted = st.form_submit_button("Login →", use_container_width=True,
                                                          type="primary")

            if adm_submitted:
                if adm_user and adm_pass:
                    data, ok = api_post("/auth/admin-login",
                                        {"username": adm_user, "password": adm_pass})
                    if ok:
                        st.session_state.user = data
                        go("overview")
                    else:
                        st.error("❌ " + data.get("detail", "Invalid admin credentials"))

            st.markdown("""
            <div style="text-align:center;margin-top:1rem;padding:0.8rem;
                background:rgba(255,255,255,0.03);border-radius:10px;
                border:1px solid rgba(255,255,255,0.07);">
                <div style="color:rgba(240,238,232,0.4);font-size:0.78rem;margin-bottom:0.3rem;">
                    System Admin (from DB)</div>
                <div style="color:rgba(240,238,232,0.6);font-size:0.82rem;">
                    Username: <b>admin_main</b> &nbsp;|&nbsp; Password: <b>admin123</b></div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TOP BAR + NAV
# ═══════════════════════════════════════════════════════════════════
def topbar():
    user = st.session_state.user
    role = get_role_display()
    name = get_name_display()
    role_colors = {
        "Doctor": "#e74c3c", "Receptionist": "#3498db",
        "Nurse": "#27ae60",  "Technician": "#9b59b6",
        "System Admin": "#f39c12"
    }
    rc = role_colors.get(role, "#95a5a6")

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
        background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
        border-radius:14px;padding:0.85rem 1.4rem;margin-bottom:1.5rem;">
        <div style="display:flex;align-items:center;gap:0.8rem;">
            <span style="font-size:1.5rem;">🩸</span>
            <span style="font-family:'Syne',sans-serif;font-weight:800;
                font-size:1.1rem;color:#f0eee8;">BloodBank Pro</span>
        </div>
        <div style="display:flex;align-items:center;gap:1rem;">
            <div style="text-align:right;">
                <div style="font-weight:600;color:#f0eee8;font-size:0.9rem;">{name}</div>
                <div style="font-size:0.72rem;color:{rc};font-weight:600;
                    letter-spacing:0.07em;text-transform:uppercase;">{role}</div>
            </div>
            <div style="width:38px;height:38px;border-radius:50%;
                background:linear-gradient(135deg,{rc},rgba(255,255,255,0.3));
                display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:1rem;color:white;">{name[0].upper()}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def nav_buttons(current="overview"):
    full = has_full_access()

    pages = [
        ("overview",   "📊 Overview"),
        ("donors",     "💉 Donors"),
        ("patients",   "🏥 Patients"),
        ("inventory",  "🩸 Blood Bags"),
        ("tests",      "🧪 Lab Tests"),
        ("issuances",  "📋 Issuances"),
    ]
    if full:
        pages += [
            ("staff",      "👥 Staff"),
            ("hospitals",  "🏨 Hospitals"),
        ]
    if is_system_admin():
        pages += [("sysadmin", "🔑 Sys Admin")]

    cols = st.columns(len(pages) + 1)
    for i, (key, label) in enumerate(pages):
        with cols[i]:
            style = "primary" if current == key else "secondary"
            if st.button(label, use_container_width=True, type=style, key=f"nav_{key}"):
                go(key)
    with cols[-1]:
        if st.button("🚪 Logout", use_container_width=True, key="nav_logout"):
            st.session_state.user = None
            go("landing")
    st.markdown("<hr style='margin:0.8rem 0 1.5rem 0;'>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# OVERVIEW / DASHBOARD
# ═══════════════════════════════════════════════════════════════════
def page_overview():
    topbar()
    nav_buttons("overview")
    page_header("Dashboard Overview", "Live snapshot of the blood bank")

    stats = api_get("/stats")
    if not stats:
        st.error("⚠️ Cannot connect to API. Make sure FastAPI is running on port 8000.")
        st.code("cd backend && uvicorn main:app --reload", language="bash")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("Total Donors",    stats.get("total_donors",   0), "#e74c3c", "💉", "Registered donors")
    with c2: stat_card("Total Patients",  stats.get("total_patients", 0), "#3498db", "🏥", "Registered patients")
    with c3: stat_card("Available Bags",  stats.get("available_bags", 0), "#27ae60", "🩸", "Ready to issue")
    with c4: stat_card("Issued Bags",     stats.get("issued_bags",    0), "#9b59b6", "✅", "Successfully issued")

    st.markdown("<br>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    with c5: stat_card("Expired Bags",    stats.get("expired_bags",    0), "#e67e22", "⚠️", "Needs disposal")
    with c6: stat_card("Total Issuances", stats.get("total_issuances", 0), "#1abc9c", "📋", "All time")
    with c7: stat_card("Staff Members",   stats.get("total_staff",     0), "#e91e63", "👥", "Active staff")
    with c8: stat_card("Hospitals",       stats.get("total_hospitals", 0), "#f39c12", "🏨", "Registered")

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Blood Group Inventory", "Available bags per blood type", "🩸")

    inventory = stats.get("blood_inventory", {})
    all_groups = ["A+","A-","B+","B-","O+","O-","AB+","AB-"]
    cols = st.columns(8)
    rare = {"O-","AB-","B-","A-"}
    for i, bg in enumerate(all_groups):
        count = inventory.get(bg, 0)
        color = "#e74c3c" if bg in rare else "#27ae60" if count > 3 else "#e67e22"
        with cols[i]:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);
                border-radius:14px;padding:1rem;text-align:center;
                {'border-color:rgba(231,76,60,0.4);' if bg in rare else ''}">
                <div style="font-family:'Syne',sans-serif;font-size:1.15rem;
                    font-weight:800;color:#f0eee8;">{bg}</div>
                <div style="font-size:2rem;font-weight:800;color:{color};
                    font-family:'Syne',sans-serif;">{count}</div>
                <div style="font-size:0.65rem;color:rgba(240,238,232,0.4);
                    text-transform:uppercase;letter-spacing:0.08em;">
                    {'⚠️ Rare' if bg in rare else 'bags'}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Recent Issuances", "Last blood issuance records", "📋")
    issuances = api_get("/issuances")
    if issuances:
        df = pd.DataFrame(issuances[-10:][::-1])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No issuances yet.")


# ═══════════════════════════════════════════════════════════════════
# DONORS
# ═══════════════════════════════════════════════════════════════════
def page_donors():
    topbar(); nav_buttons("donors")
    page_header("Donor Management", "Register and manage blood donors")

    donors    = api_get("/donors")
    hospitals = api_get("/hospitals")
    staff     = api_get("/staff")
    hosp_opt  = {h["name"]: h["hospital_id"] for h in hospitals}
    hosp_map  = {h["hospital_id"]: h["name"]  for h in hospitals}
    rare      = {"O-","AB-","B-","A-"}

    tab1, tab2 = st.tabs(["📋 All Donors", "➕ Add Donor"])

    with tab1:
        if donors:
            df = pd.DataFrame(donors)
            df["hospital"] = df["hospital_id"].map(hosp_map)
            st.dataframe(df.drop(columns=["hospital_id"], errors="ignore"),
                         use_container_width=True, hide_index=True)

        if donors and has_full_access():
            st.markdown("---")
            section_header("Edit / Delete Donor", "", "✏️")
            d_ids = [d["donor_id"] for d in donors]
            sel_id = st.selectbox("Select Donor", d_ids,
                                  format_func=lambda x: next((f"{x} – {d['name']}" for d in donors if d["donor_id"]==x), str(x)))
            sel = next((d for d in donors if d["donor_id"] == sel_id), None)
            if sel:
                with st.form("edit_donor"):
                    c1, c2 = st.columns(2)
                    name   = c1.text_input("Name",    sel["name"])
                    bg     = c2.selectbox("Blood Group",
                                          ["A+","A-","B+","B-","O+","O-","AB+","AB-"],
                                          index=["A+","A-","B+","B-","O+","O-","AB+","AB-"].index(sel["blood_group"])
                                          if sel["blood_group"] in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                    c3, c4 = st.columns(2)
                    gender  = c3.selectbox("Gender", ["Male","Female","Other"],
                                           index=["Male","Female","Other"].index(sel.get("gender","Male"))
                                           if sel.get("gender") in ["Male","Female","Other"] else 0)
                    contact = c4.text_input("Contact", sel.get("contact",""))
                    c5, c6 = st.columns(2)
                    city    = c5.text_input("City", sel.get("city",""))
                    fit_opts = ["Fit", "Unfit", "Deferred"]
                    fit_cur  = sel.get("fitness_status", "Fit") or "Fit"
                    fitness = c6.selectbox("Fitness Status", fit_opts,
                                           index=fit_opts.index(fit_cur) if fit_cur in fit_opts else 0)
                    if bg in rare:
                        st.warning(f"⚠️ {bg} is a RARE blood type!")
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("💾 Update", type="primary", use_container_width=True):
                        res, ok = api_put(f"/donors/{sel_id}",
                                          {"name":name,"blood_group":bg,"gender":gender,
                                           "contact":contact,"city":city,"fitness_status":fitness})
                        if ok:
                            st.success("✅ Donor updated!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                    if col2.form_submit_button("🗑️ Delete", use_container_width=True):
                        res, ok = api_delete(f"/donors/{sel_id}")
                        if ok:
                            st.success("Deleted!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                        if ok: st.rerun()

    with tab2:
        section_header("Register New Donor", "", "💉")
        with st.form("add_donor"):
            new_id = next_id(donors, "donor_id")
            c1, c2 = st.columns(2)
            d_id   = c1.number_input("Donor ID", value=new_id, step=1)
            d_name = c2.text_input("Full Name")
            c3, c4 = st.columns(2)
            d_bg   = c3.selectbox("Blood Group", ["A+","A-","B+","B-","O+","O-","AB+","AB-"])
            d_gen  = c4.selectbox("Gender", ["Male","Female","Other"])
            c5, c6 = st.columns(2)
            d_cont = c5.text_input("Contact Number")
            d_city = c6.text_input("City")
            c7, c8 = st.columns(2)
            d_hosp = c7.selectbox("Hospital", list(hosp_opt.keys()) if hosp_opt else ["—"])
            d_fit  = c8.selectbox("Fitness Status", ["Fit", "Unfit", "Deferred"])
            s_ids  = [s["staff_id"] for s in staff]
            d_staff = st.selectbox("Registering Staff", s_ids,
                                   format_func=lambda x: next(
                                       (f"{x} – {s['fullname']}" for s in staff if s["staff_id"]==x),
                                       f"Staff {x}"))
            if d_bg in rare:
                st.warning(f"{d_bg} is a RARE blood type — notify senior doctor!")
            if d_fit == "Deferred":
                st.warning("Donor is DEFERRED — they can donate again later after re-evaluation.")
            if d_fit == "Unfit":
                st.error("Donor is UNFIT — cannot donate blood at all.")
            if st.form_submit_button("Register Donor", type="primary", use_container_width=True):
                res, ok = api_post("/donors", {
                    "donor_id": int(d_id), "name": d_name, "blood_group": d_bg,
                    "gender": d_gen, "contact": d_cont, "city": d_city,
                    "fitness_status": d_fit, "hospital_id": hosp_opt.get(d_hosp),
                    "staff_id": int(d_staff) if d_staff else None
                })
                if ok:
                    st.success("Donor registered!")
                else:
                    st.error(res.get("detail", "Operation failed"))
                if ok: st.rerun()


# ═══════════════════════════════════════════════════════════════════
# PATIENTS
# ═══════════════════════════════════════════════════════════════════
def page_patients():
    topbar(); nav_buttons("patients")
    page_header("Patient Management", "Register and manage patients")

    patients  = api_get("/patients")
    hospitals = api_get("/hospitals")
    staff     = api_get("/staff")
    hosp_opt  = {h["name"]: h["hospital_id"] for h in hospitals}
    hosp_map  = {h["hospital_id"]: h["name"]  for h in hospitals}

    tab1, tab2 = st.tabs(["📋 All Patients", "➕ Add Patient"])

    with tab1:
        if patients:
            df = pd.DataFrame(patients)
            df["hospital"] = df["hospital_id"].map(hosp_map)
            st.dataframe(df.drop(columns=["hospital_id"], errors="ignore"),
                         use_container_width=True, hide_index=True)

        if patients and has_full_access():
            st.markdown("---")
            section_header("Edit / Delete Patient", "", "✏️")
            p_ids  = [p["patient_id"] for p in patients]
            sel_id = st.selectbox("Select Patient", p_ids,
                                  format_func=lambda x: next((f"{x} – {p['name']}" for p in patients if p["patient_id"]==x), str(x)))
            sel = next((p for p in patients if p["patient_id"] == sel_id), None)
            if sel:
                with st.form("edit_patient"):
                    c1, c2 = st.columns(2)
                    name    = c1.text_input("Name", sel["name"])
                    bg      = c2.selectbox("Blood Group",
                                           ["A+","A-","B+","B-","O+","O-","AB+","AB-"],
                                           index=["A+","A-","B+","B-","O+","O-","AB+","AB-"].index(sel["blood_group"])
                                           if sel["blood_group"] in ["A+","A-","B+","B-","O+","O-","AB+","AB-"] else 0)
                    c3, c4  = st.columns(2)
                    gender  = c3.selectbox("Gender", ["Male","Female","Other"],
                                           index=["Male","Female","Other"].index(sel.get("gender","Male"))
                                           if sel.get("gender") in ["Male","Female","Other"] else 0)
                    contact = c4.text_input("Contact", sel.get("contact",""))
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("💾 Update", type="primary", use_container_width=True):
                        res, ok = api_put(f"/patients/{sel_id}",
                                          {"name":name,"blood_group":bg,"gender":gender,"contact":contact})
                        if ok:
                            st.success("✅ Patient updated!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                    if col2.form_submit_button("🗑️ Delete", use_container_width=True):
                        res, ok = api_delete(f"/patients/{sel_id}")
                        if ok:
                            st.success("Deleted!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                        if ok: st.rerun()

    with tab2:
        section_header("Register New Patient", "", "🏥")
        with st.form("add_patient"):
            new_id  = next_id(patients, "patient_id")
            c1, c2  = st.columns(2)
            p_id    = c1.number_input("Patient ID", value=new_id, step=1)
            p_name  = c2.text_input("Full Name")
            c3, c4  = st.columns(2)
            p_bg    = c3.selectbox("Blood Group", ["A+","A-","B+","B-","O+","O-","AB+","AB-"])
            p_gen   = c4.selectbox("Gender", ["Male","Female","Other"])
            c5, c6  = st.columns(2)
            p_dob   = c5.date_input("Date of Birth", value=date(1990,1,1))
            p_cont  = c6.text_input("Contact Number")
            c7, c8  = st.columns(2)
            p_hosp  = c7.selectbox("Hospital", list(hosp_opt.keys()) if hosp_opt else ["—"])
            s_ids   = [s["staff_id"] for s in staff]
            p_staff = c8.selectbox("Registering Staff", s_ids,
                                   format_func=lambda x: f"Staff {x}")
            if st.form_submit_button("✅ Register Patient", type="primary", use_container_width=True):
                res, ok = api_post("/patients", {
                    "patient_id": int(p_id), "name": p_name, "blood_group": p_bg,
                    "date_of_birth": str(p_dob), "gender": p_gen, "contact": p_cont,
                    "hospital_id": hosp_opt.get(p_hosp),
                    "staff_id": int(p_staff) if p_staff else None
                })
                if ok:
                    st.success("✅ Patient registered!")
                else:
                    st.error(res.get("detail", "Operation failed"))
                if ok: st.rerun()


# ═══════════════════════════════════════════════════════════════════
# BLOOD BAGS (INVENTORY)
# ═══════════════════════════════════════════════════════════════════
def page_inventory():
    topbar(); nav_buttons("inventory")
    page_header("Blood Bag Inventory", "Track all blood bags and their status")

    bags      = api_get("/blood-bags")
    donors    = api_get("/donors")
    hospitals = api_get("/hospitals")
    hosp_opt  = {h["name"]: h["hospital_id"] for h in hospitals}
    hosp_map  = {h["hospital_id"]: h["name"]  for h in hospitals}

    # Categorise
    available = [b for b in bags if b.get("status") == "Available"]
    issued    = [b for b in bags if b.get("status") == "Issued"]
    today_str = str(date.today())
    expired   = [b for b in available if (b.get("expiry_date") or "") < today_str]

    tab1, tab2, tab3 = st.tabs(["📦 All Bags", "✅ Available", "➕ Add Bag"])

    with tab1:
        if bags:
            df = pd.DataFrame(bags)
            df["hospital"] = df["hospital_id"].map(hosp_map)
            st.dataframe(df, use_container_width=True, hide_index=True)

        if bags and has_full_access():
            st.markdown("---")
            section_header("Delete Blood Bag", "", "🗑️")
            b_ids = [b["bag_id"] for b in bags]
            sel_b = st.selectbox("Select Bag", b_ids,
                                 format_func=lambda x: next(
                                     (f"Bag {x} – {b['blood_group']} [{b['status']}]"
                                      for b in bags if b["bag_id"]==x), str(x)))
            if st.button("🗑️ Delete Selected Bag", type="primary"):
                res, ok = api_delete(f"/blood-bags/{sel_b}")
                if ok:
                    st.success("Deleted!")
                else:
                    st.error(res.get("detail", "Operation failed"))
                if ok: st.rerun()

    with tab2:
        if available:
            df2 = pd.DataFrame(available)
            st.dataframe(df2, use_container_width=True, hide_index=True)
            if expired:
                st.warning(f"⚠️ {len(expired)} bag(s) are past expiry date and should be discarded.")
        else:
            st.info("No available bags in inventory.")

    with tab3:
        section_header("Add New Blood Bag", "", "🩸")

        # ── Eligibility checker (runs before the form) ─────────────
        st.markdown("**Step 1 — Check Donor Eligibility First**")
        donor_ids = [d["donor_id"] for d in donors]

        if donor_ids:
            chk_donor = st.selectbox(
                "Select donor to check",
                donor_ids,
                format_func=lambda x: next(
                    (f"{x} – {d['name']} ({d['blood_group']}) [{d.get('fitness_status','?')}]"
                     for d in donors if d["donor_id"] == x), str(x)
                ),
                key="elig_check_sel"
            )
            if st.button("Check Eligibility", key="elig_btn"):
                elig = api_get(f"/blood-bags/donor/{chk_donor}/eligibility")
                if isinstance(elig, dict):
                    if elig.get("eligible"):
                        active = elig.get("active_bags_in_inventory", 0)
                        total  = elig.get("total_donations", 0)
                        last   = elig.get("last_donation") or "Never"
                        st.success(
                            f"**{elig['donor_name']}** is ELIGIBLE to donate.  \n"
                            f"Fitness: **{elig['fitness']}** | "
                            f"Last donation: **{last}** | "
                            f"Active bags in inventory: **{active}/3** | "
                            f"Total donations: **{total}**"
                        )
                    else:
                        for r in elig.get("reasons", []):
                            st.error(r)
                        next_d = elig.get("next_eligible_date")
                        if next_d:
                            st.info(f"Next eligible donation date: **{next_d}**")
                else:
                    st.error("Could not fetch eligibility data from API.")

        st.markdown("---")
        st.markdown("**Step 2 — Add the Blood Bag**")
        st.caption("The backend enforces: Fit status, 56-day interval, max 3 active bags per donor.")

        with st.form("add_bag"):
            new_id    = next_id(bags, "bag_id")
            c1, c2    = st.columns(2)
            b_id      = c1.number_input("Bag ID", value=new_id, step=1)

            # Only show Fit donors in the dropdown — Unfit/Deferred are blocked by backend anyway
            fit_donors = [d for d in donors if d.get("fitness_status") == "Fit"]
            all_donor_map = {
                d["donor_id"]: f"{d['donor_id']} – {d['name']} ({d['blood_group']}) [{d.get('fitness_status','?')}]"
                for d in donors
            }
            d_sel = c2.selectbox(
                "Donor",
                list(all_donor_map.keys()),
                format_func=lambda x: all_donor_map.get(x, str(x))
            )

            c3, c4  = st.columns(2)
            b_bg    = c3.selectbox("Blood Group", ["A+","A-","B+","B-","O+","O-","AB+","AB-"])
            b_hosp  = c4.selectbox("Hospital", list(hosp_opt.keys()) if hosp_opt else ["—"])

            st.caption("Collection date defaults to TODAY. Expiry is auto-calculated as +35 days by Oracle.")

            sub_bag = st.form_submit_button("Add Blood Bag", type="primary", use_container_width=True)

        if sub_bag:
            res, ok = api_post("/blood-bags", {
                "bag_id": int(b_id), "donor_id": int(d_sel),
                "blood_group": b_bg, "hospital_id": hosp_opt.get(b_hosp)
            })
            if ok:
                st.success(res.get("message", "Blood bag added!"))
                st.rerun()
            else:
                st.error(res.get("detail", "Could not add bag — check eligibility first."))


# ═══════════════════════════════════════════════════════════════════
# LAB TESTS
# ═══════════════════════════════════════════════════════════════════
def page_tests():
    topbar()
    nav_buttons("tests")
    page_header("Lab Tests", "Record blood test results")

    tests  = api_get("/blood-tests")
    bags   = api_get("/blood-bags")
    staff  = api_get("/staff")

    # Show ALL bags in the test dropdown — a bag may need re-testing too
    bag_map = {b["bag_id"]: f"Bag {b['bag_id']} – {b['blood_group']} [{b.get('status','?')}]"
               for b in bags}

    tab1, tab2 = st.tabs(["📋 Test Records", "➕ Add Test"])

    with tab1:
        if tests:
            df = pd.DataFrame(tests)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No test records yet.")

        if tests and has_full_access():
            st.markdown("---")
            section_header("Delete Test Record", "", "🗑️")
            t_ids = [t["test_id"] for t in tests]
            sel_t = st.selectbox(
                "Select Test", t_ids,
                format_func=lambda x: next(
                    (f"Test {x} – Bag {t['bag_id']} [{t['test_result']}]"
                     for t in tests if t["test_id"] == x), str(x)
                )
            )
            if st.button("Delete Test Record", type="primary"):
                res, ok = api_delete(f"/blood-tests/{sel_t}")
                if ok:
                    st.success("Test record deleted!")
                    st.rerun()
                else:
                    st.error(res.get("detail", "Delete failed"))

    with tab2:
        section_header("Record New Test", "", "🧪")

        # ── ORA-02290 root-cause explanation ──────────────────────
        st.info(
            "**Note:** Your Oracle `BLOOD_TEST` table CHECK constraint requires the result "
            "to be exactly **`Passed`** or **`Failed`** (matches the values already in your DB). "
            "The form below uses those exact values."
        )

        with st.form("add_test"):
            new_id = next_id(tests, "test_id")
            c1, c2 = st.columns(2)
            t_id   = c1.number_input("Test ID", value=new_id, step=1)

            if bag_map:
                b_sel = c2.selectbox(
                    "Blood Bag",
                    list(bag_map.keys()),
                    format_func=lambda x: bag_map.get(x, str(x))
                )
            else:
                st.warning("No blood bags found. Add a bag first.")
                b_sel = None

            c3, c4 = st.columns(2)
            hb     = c3.number_input("HB Level (g/dL)", min_value=0.0,
                                     max_value=25.0, value=13.5, step=0.1)
            # Values match the Oracle CHECK constraint in BLOOD_TEST table
            result = c4.selectbox("Test Result", ["Passed", "Failed"])

            remarks = st.text_area("Remarks (optional)", height=80)

            s_ids = [s["staff_id"] for s in staff]
            s_sel = st.selectbox(
                "Tested By (Staff)", s_ids,
                format_func=lambda x: next(
                    (f"{x} – {s['fullname']}" for s in staff if s["staff_id"] == x), f"Staff {x}"
                )
            )

            if result == "Failed":
                st.error("FAIL: This bag will be blocked by the Oracle trigger and cannot be issued.")

            submitted = st.form_submit_button(
                "Save Test Result", type="primary", use_container_width=True
            )

        # Handle submission OUTSIDE the form block to avoid Python 3.14 inline issues
        if submitted and b_sel:
            res, ok = api_post("/blood-tests", {
                "test_id":    int(t_id),
                "bag_id":     int(b_sel),
                "hb_level":   float(hb),
                "test_result": result,
                "remarks":    remarks,
                "staff_id":   int(s_sel)
            })
            if ok:
                st.success("Test result saved to database!")
                st.rerun()
            else:
                st.error(res.get("detail", "Failed to save test result"))


# ═══════════════════════════════════════════════════════════════════
# ISSUANCES
# ═══════════════════════════════════════════════════════════════════
def page_issuances():
    topbar(); nav_buttons("issuances")
    page_header("Blood Issuances", "Issue blood to patients — trigger-protected")

    issuances = api_get("/issuances")
    bags      = api_get("/blood-bags")
    patients  = api_get("/patients")
    hospitals = api_get("/hospitals")
    staff     = api_get("/staff")
    tests     = api_get("/blood-tests")
    today_str = str(date.today())

    # Accept both "Pass" and "Passed" — handles whatever CHECK constraint your DB has
    tested_bag_ids = {t["bag_id"] for t in tests if t.get("test_result") in ("Pass", "Passed")}
    issuable_bags  = [
        b for b in bags
        if b.get("status") == "Available"
        and (b.get("expiry_date") or "") >= today_str
        and b["bag_id"] in tested_bag_ids
    ]

    tabs = ["📋 All Issuances", "🩸 Issue Blood"]
    tab_objs = st.tabs(tabs)

    with tab_objs[0]:
        if issuances:
            df = pd.DataFrame(issuances[-20:][::-1])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No issuances recorded yet.")

        if issuances and has_full_access():
            st.markdown("---")
            section_header("Delete Issuance Record", "", "🗑️")
            i_ids = [i["issue_id"] for i in issuances]
            sel_i = st.selectbox("Select Issuance", i_ids)
            if st.button("🗑️ Delete Issuance Record", type="primary"):
                res, ok = api_delete(f"/issuances/{sel_i}")
                if ok:
                    st.success("Deleted!")
                else:
                    st.error(res.get("detail", "Operation failed"))
                if ok: st.rerun()

    with tab_objs[1]:
        section_header("Issue Blood to Patient",
                       "Only tested, non-expired, available bags can be issued", "🩸")

        st.info("Oracle trigger **trg_check_blood_issuance_safety** is active — it automatically "
                "blocks: expired bags, untested bags, failed-test bags, already-issued bags.")

        if not issuable_bags:
            st.warning("No issuable bags right now. Bags must be: Available status + Passed test + Not expired.")
            st.markdown("**Checklist:**")
            st.markdown("- Add a blood bag in the Blood Bags page")
            st.markdown("- Record a **Passed** test for that bag in Lab Tests")
            st.markdown("- Make sure the bag is within its 35-day expiry window")
        else:
            with st.form("issue_blood"):
                new_id  = next_id(issuances, "issue_id")
                c1, c2  = st.columns(2)
                i_id    = c1.number_input("Issue ID", value=new_id, step=1)
                bag_fmt = {
                    b["bag_id"]: f"Bag {b['bag_id']} – {b['blood_group']} (Exp: {b['expiry_date']})"
                    for b in issuable_bags
                }
                bag_sel = c2.selectbox("Select Blood Bag", list(bag_fmt.keys()),
                                       format_func=lambda x: bag_fmt[x])

                p_fmt   = {p["patient_id"]: f"{p['patient_id']} – {p['name']} ({p['blood_group']})"
                           for p in patients}
                p_sel   = st.selectbox("Select Patient", list(p_fmt.keys()) if p_fmt else [None],
                                       format_func=lambda x: p_fmt.get(x, "No patients yet"))

                c3, c4  = st.columns(2)
                hosp_options = {h["name"]: h["hospital_id"] for h in hospitals}
                h_sel   = c3.selectbox("Hospital",
                                       list(hosp_options.keys()) if hosp_options else ["—"])
                s_ids   = [s["staff_id"] for s in staff]
                user_sid = st.session_state.user.get("staff_id") if st.session_state.user else None
                default_s = s_ids.index(user_sid) if user_sid in s_ids else 0
                s_sel   = c4.selectbox("Authorizing Staff", s_ids, index=default_s,
                                       format_func=lambda x: next(
                                           (f"{x} – {s['fullname']}" for s in staff if s["staff_id"]==x),
                                           f"Staff {x}"))

                # Blood group mismatch warning (inside form, purely visual)
                sel_bag     = next((b for b in issuable_bags if b["bag_id"] == bag_sel), None)
                sel_patient = next((p for p in patients if p["patient_id"] == p_sel), None)
                if sel_bag and sel_patient and sel_bag["blood_group"] != sel_patient["blood_group"]:
                    st.warning(f"Blood group mismatch! "
                               f"Bag: **{sel_bag['blood_group']}** | "
                               f"Patient: **{sel_patient['blood_group']}** — verify compatibility.")

                issue_submitted = st.form_submit_button("Issue Blood", type="primary",
                                                        use_container_width=True)

            if issue_submitted and p_sel:
                res, ok = api_post("/issuances", {
                    "issue_id": int(i_id), "bag_id": int(bag_sel),
                    "patient_id": int(p_sel),
                    "hospital_id": hosp_options.get(h_sel),
                    "staff_id": int(s_sel)
                })
                if ok:
                    st.success("Blood issued successfully! Bag status updated to Issued automatically.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(res.get("detail", "Trigger blocked issuance — check bag status, test result and expiry."))


# ═══════════════════════════════════════════════════════════════════
# STAFF  (Admin + System Admin)
# ═══════════════════════════════════════════════════════════════════
def page_staff():
    topbar(); nav_buttons("staff")
    page_header("Staff Management", "Manage hospital staff accounts")

    staff     = api_get("/staff")
    hospitals = api_get("/hospitals")
    hosp_opt  = {h["name"]: h["hospital_id"] for h in hospitals}
    hosp_map  = {h["hospital_id"]: h["name"]  for h in hospitals}

    tab1, tab2 = st.tabs(["📋 All Staff", "➕ Add Staff"])

    with tab1:
        if staff:
            df = pd.DataFrame(staff)
            df["hospital"] = df["hospital_id"].map(hosp_map)
            st.dataframe(df.drop(columns=["hospital_id"], errors="ignore"),
                         use_container_width=True, hide_index=True)

        if staff:
            st.markdown("---")
            section_header("Edit / Delete Staff", "", "✏️")
            s_ids  = [s["staff_id"] for s in staff]
            sel_id = st.selectbox("Select Staff", s_ids,
                                  format_func=lambda x: next(
                                      (f"{x} – {s['fullname']} [{s['role']}]"
                                       for s in staff if s["staff_id"]==x), str(x)))
            sel = next((s for s in staff if s["staff_id"] == sel_id), None)
            if sel:
                with st.form("edit_staff"):
                    c1, c2  = st.columns(2)
                    name    = c1.text_input("Full Name", sel["fullname"])
                    role    = c2.selectbox("Role", ["Doctor","Receptionist","Nurse","Technician"],
                                           index=["Doctor","Receptionist","Nurse","Technician"].index(sel["role"])
                                           if sel["role"] in ["Doctor","Receptionist","Nurse","Technician"] else 0)
                    c3, c4  = st.columns(2)
                    contact = c3.text_input("Contact", sel.get("contact","") or "")
                    password= c4.text_input("New Password (blank = keep)", type="password")
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("💾 Update", type="primary", use_container_width=True):
                        payload = {"fullname": name, "role": role, "contact": contact}
                        if password: payload["password"] = password
                        res, ok = api_put(f"/staff/{sel_id}", payload)
                        if ok:
                            st.success("✅ Staff updated!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                    if col2.form_submit_button("🗑️ Delete", use_container_width=True):
                        res, ok = api_delete(f"/staff/{sel_id}")
                        if ok:
                            st.success("Deleted!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                        if ok: st.rerun()

    with tab2:
        section_header("Add New Staff Member", "", "👤")
        with st.form("add_staff"):
            new_id   = next_id(staff, "staff_id")
            c1, c2   = st.columns(2)
            s_id     = c1.number_input("Staff ID", value=new_id, step=1)
            s_name   = c2.text_input("Full Name")
            c3, c4   = st.columns(2)
            s_role   = c3.selectbox("Role", ["Doctor","Receptionist","Nurse","Technician"])
            s_cont   = c4.text_input("Contact Number")
            c5, c6   = st.columns(2)
            s_pass   = c5.text_input("Password", type="password")
            s_hosp   = c6.selectbox("Hospital", list(hosp_opt.keys()) if hosp_opt else ["—"])
            if st.form_submit_button("✅ Create Staff Account", type="primary",
                                     use_container_width=True):
                res, ok = api_post("/staff", {
                    "staff_id": int(s_id), "fullname": s_name, "password": s_pass,
                    "role": s_role, "hospital_id": hosp_opt.get(s_hosp), "contact": s_cont
                })
                if ok:
                    st.success("✅ Staff account created!")
                else:
                    st.error(res.get("detail", "Operation failed"))
                if ok: st.rerun()


# ═══════════════════════════════════════════════════════════════════
# HOSPITALS  (full CRUD — now in nav for Admin + System Admin)
# ═══════════════════════════════════════════════════════════════════
def page_hospitals():
    topbar(); nav_buttons("hospitals")
    page_header("Hospital Management", "Add, edit and delete hospital records")

    hospitals = api_get("/hospitals")
    tab1, tab2 = st.tabs(["📋 All Hospitals", "➕ Add Hospital"])

    with tab1:
        if hospitals:
            st.dataframe(pd.DataFrame(hospitals), use_container_width=True, hide_index=True)

        if hospitals:
            st.markdown("---")
            section_header("Edit / Delete Hospital", "", "✏️")
            h_ids  = [h["hospital_id"] for h in hospitals]
            sel_h  = st.selectbox("Select Hospital", h_ids,
                                  format_func=lambda x: next(
                                      (f"{x} – {h['name']}" for h in hospitals if h["hospital_id"]==x), str(x)))
            sel    = next((h for h in hospitals if h["hospital_id"] == sel_h), None)
            if sel:
                with st.form("edit_hospital"):
                    c1, c2   = st.columns(2)
                    h_name   = c1.text_input("Hospital Name", sel["name"])
                    h_cont   = c2.text_input("Contact", sel.get("contact","") or "")
                    h_addr   = st.text_area("Address", sel.get("address","") or "", height=80)
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("💾 Update", type="primary", use_container_width=True):
                        res, ok = api_put(f"/hospitals/{sel_h}",
                                          {"name": h_name, "contact": h_cont, "address": h_addr})
                        if ok:
                            st.success("✅ Hospital updated!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                    if col2.form_submit_button("🗑️ Delete", use_container_width=True):
                        res, ok = api_delete(f"/hospitals/{sel_h}")
                        if ok:
                            st.success("Deleted!")
                        else:
                            st.error(res.get("detail", "Operation failed"))
                        if ok: st.rerun()

    with tab2:
        section_header("Register New Hospital", "", "🏨")
        with st.form("add_hospital"):
            new_id  = next_id(hospitals, "hospital_id")
            c1, c2  = st.columns(2)
            h_id    = c1.number_input("Hospital ID", value=new_id, step=1)
            h_name  = c2.text_input("Hospital Name")
            h_addr  = st.text_area("Address", height=80)
            h_cont  = st.text_input("Contact Number")
            if st.form_submit_button("✅ Add Hospital", type="primary", use_container_width=True):
                res, ok = api_post("/hospitals", {
                    "hospital_id": int(h_id), "name": h_name,
                    "address": h_addr, "contact": h_cont
                })
                if ok:
                    st.success("✅ Hospital added!")
                else:
                    st.error(res.get("detail", "Operation failed"))
                if ok: st.rerun()


# ═══════════════════════════════════════════════════════════════════
# SYSTEM ADMIN PANEL  (only visible to system_admin user_type)
# ═══════════════════════════════════════════════════════════════════
def page_sysadmin():
    topbar(); nav_buttons("sysadmin")
    page_header("System Admin Panel",
                "Manage system administrator accounts — reads live from SYSTEM_ADMIN table")

    admins = api_get("/system-admins")

    tab1, = st.tabs(["🔑 Admin Accounts"])        # only one tab for now

    with tab1:
        if admins:
            st.dataframe(pd.DataFrame(admins), use_container_width=True, hide_index=True)

        if admins:
            st.markdown("---")
            section_header("Update Admin Account", "Change name, contact or password", "✏️")
            a_ids  = [a["admin_id"] for a in admins]
            sel_id = st.selectbox("Select Admin", a_ids,
                                  format_func=lambda x: next(
                                      (f"{x} – {a['username']} ({a['fullname']})"
                                       for a in admins if a["admin_id"]==x), str(x)))
            sel    = next((a for a in admins if a["admin_id"] == sel_id), None)
            if sel:
                with st.form("edit_sysadmin"):
                    c1, c2   = st.columns(2)
                    fullname = c1.text_input("Full Name", sel.get("fullname","") or "")
                    contact  = c2.text_input("Contact",   sel.get("contact","")  or "")
                    password = st.text_input("New Password (blank = keep)", type="password")
                    if st.form_submit_button("💾 Update Admin", type="primary",
                                             use_container_width=True):
                        payload = {"fullname": fullname, "contact": contact}
                        if password: payload["password"] = password
                        res, ok = api_put(f"/system-admins/{sel_id}", payload)
                        if ok:
                            st.success("✅ Admin account updated!")
                        else:
                            st.error(res.get("detail", "Operation failed"))

        st.markdown("---")
        st.info("ℹ️ To add a new System Admin, run this SQL in BloodBank_PDB:\n\n"
                "```sql\n"
                "INSERT INTO SYSTEM_ADMIN (ADMIN_ID, USERNAME, PASSWORD, FULLNAME, CONTACT)\n"
                "VALUES (2, 'new_admin', 'securepass', 'New Admin Name', '9999999999');\n"
                "COMMIT;\n"
                "```\n"
                "The login page reads credentials live from the database — no code change needed.")


# ═══════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════
page = st.session_state.page
user = st.session_state.user

if page not in ("landing", "login") and not user:
    go("landing")

if   page == "landing":   landing()
elif page == "login":     login_page()
elif page == "overview":  page_overview()
elif page == "donors":    page_donors()
elif page == "patients":  page_patients()
elif page == "inventory": page_inventory()
elif page == "tests":     page_tests()
elif page == "issuances": page_issuances()
elif page == "sysadmin":
    if is_system_admin():
        page_sysadmin()
    else:
        st.error("Access denied. System Admins only.")
        go("overview")
elif page == "staff":
    if has_full_access():
        page_staff()
    else:
        st.error("Access denied.")
        go("overview")
elif page == "hospitals":
    if has_full_access():
        page_hospitals()
    else:
        st.error("Access denied.")
        go("overview")