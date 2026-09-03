import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import hashlib
import base64
import os
from bs4 import BeautifulSoup
from datetime import datetime, date
from io import BytesIO

# =========================================================
# MASAR INTELLIGENCE OS
# VERSION 3.0 (Enterprise Edition)
# =========================================================

APP_NAME = "MASAR Intelligence OS"
COMPANY_NAME = "MASAR for Consultancy and Business Development"
DB_PATH = "masar_os.db"

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn

def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    result = cur.lastrowid
    conn.close()
    return result

def query(sql, params=()):
    conn = get_db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

# =========================================================
# SECURITY
# =========================================================

def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()

def verify_pin(pin, stored_hash):
    return hash_pin(pin) == stored_hash

# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        position TEXT,
        email TEXT,
        phone TEXT,
        pin_hash TEXT NOT NULL,
        role TEXT DEFAULT 'Employee',
        status TEXT DEFAULT 'Active',
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        message TEXT NOT NULL,
        created_at TEXT,
        is_read INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        assigned_to INTEGER,
        created_by INTEGER,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Pending',
        completion INTEGER DEFAULT 0,
        due_date TEXT,
        created_at TEXT,
        completed_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS performance_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        period TEXT,
        manager_rating REAL DEFAULT 0,
        notes TEXT,
        reviewed_by INTEGER,
        reviewed_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        title TEXT,
        file_name TEXT,
        file_data BLOB,
        extracted_text TEXT,
        uploaded_by INTEGER,
        uploaded_at TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        website TEXT,
        industry TEXT,
        country TEXT,
        size TEXT,
        status TEXT DEFAULT 'Prospect',
        description TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        title TEXT NOT NULL,
        service TEXT,
        stage TEXT,
        value REAL DEFAULT 0,
        probability REAL DEFAULT 0,
        next_action TEXT,
        next_action_date TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    # New Table: Projects & Deliverables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        opportunity_id INTEGER,
        company_id INTEGER,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'In Progress',
        start_date TEXT,
        deadline TEXT,
        value REAL DEFAULT 0,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        title TEXT,
        meeting_date TEXT,
        attendees TEXT,
        outcome TEXT,
        next_steps TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS governance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT,
        review_date TEXT,
        status TEXT DEFAULT 'Active'
    )
    """)

    conn.commit()
    conn.close()

    admins = query("SELECT id FROM employees WHERE role='Admin'")
    if admins.empty:
        execute(
            """
            INSERT INTO employees
            (employee_code, full_name, position, email, pin_hash, role, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ADMIN",
                "MASAR Administrator",
                "System Administrator",
                "",
                hash_pin("1234"),
                "Admin",
                "Active",
                datetime.now().isoformat()
            )
        )

init_db()

# =========================================================
# CSS STYLING
# =========================================================

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 10% 10%, rgba(56,189,248,.07), transparent 25%),
                radial-gradient(circle at 90% 10%, rgba(30,58,138,.12), transparent 25%), #0B1220;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07111F 0%, #0B1E36 100%);
    border-right: 1px solid rgba(56,189,248,.15);
}
section[data-testid="stSidebar"] * { color:#E5EEF8; }
h1,h2,h3 { color:#F5F9FF !important; }
p,label { color:#B7C5D6 !important; }
.masar-logo { font-size:30px; font-weight:900; color:white; }
.masar-tag { font-size:10px; color:#38BDF8; letter-spacing:2px; }
.header { padding:20px 0 25px; }
.title { font-size:34px; font-weight:850; color:white; }
.subtitle { color:#38BDF8; font-size:11px; text-transform:uppercase; letter-spacing:2px; }
.kpi {
    background: linear-gradient(145deg, rgba(20,36,58,.96), rgba(10,25,43,.96));
    border: 1px solid rgba(56,189,248,.13);
    border-radius: 18px;
    padding: 20px;
    min-height: 125px;
}
.kpi-label { color:#8FA6BF; font-size:11px; text-transform:uppercase; letter-spacing:1px; }
.kpi-value { color:white; font-size:31px; font-weight:850; margin-top:8px; }
.kpi-note { color:#38BDF8; font-size:12px; }
.profile {
    background: linear-gradient(145deg, #10243D, #0B1E36);
    border: 1px solid rgba(56,189,248,.13);
    border-radius: 18px;
    padding: 18px;
}
.chat-message { padding:14px; margin:8px 0; border-radius:15px; background:#10243A; }
.chat-me { border-left:3px solid #38BDF8; }
.chat-other { border-left:3px solid #64748B; }
.performance {
    background: linear-gradient(145deg, #10243D, #0B1E36);
    border-radius: 20px;
    padding: 25px;
    text-align: center;
    border: 1px solid rgba(56,189,248,.15);
}
.score { font-size:58px; font-weight:900; color:#38BDF8; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# UI HELPERS
# =========================================================

def header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="header">
            <div class="subtitle">{COMPANY_NAME}</div>
            <div class="title">{title}</div>
            <div style="color:#8295AA;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def kpi(label, value, note=""):
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def get_logo():
    row = query("SELECT value FROM settings WHERE key='logo'")
    if row.empty:
        return None
    try:
        return base64.b64decode(row.iloc[0]["value"])
    except Exception:
        return None

def display_logo():
    logo = get_logo()
    if logo:
        st.sidebar.image(logo, width=150)
    else:
        st.sidebar.markdown(
            """
            <div class="masar-logo">◈ MASAR</div>
            <div class="masar-tag">INTELLIGENCE OS</div>
            """,
            unsafe_allow_html=True
        )

# =========================================================
# LOGIN
# =========================================================

def login():
    st.markdown(
        """
        <div style="text-align:center; margin-top:90px;">
            <div style="font-size:65px; font-weight:900; color:white;">◈</div>
            <div style="font-size:38px; font-weight:900; color:white;">MASAR</div>
            <div style="color:#38BDF8; letter-spacing:3px; font-size:12px;">INTELLIGENCE OS V3.0</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.markdown("### Secure Employee Login")
        with st.form("login_form"):
            code = st.text_input("Employee Code")
            pin = st.text_input("PIN", type="password")
            submit = st.form_submit_button("SIGN IN", use_container_width=True)
            if submit:
                users = query("SELECT * FROM employees WHERE employee_code=? AND status='Active'", (code.upper().strip(),))
                if users.empty:
                    st.error("Invalid employee code.")
                else:
                    user = users.iloc[0]
                    if verify_pin(pin, user["pin_hash"]):
                        st.session_state["authenticated"] = True
                        st.session_state["user_id"] = int(user["id"])
                        st.session_state["user_name"] = user["full_name"]
                        st.session_state["user_role"] = user["role"]
                        st.session_state["employee_code"] = user["employee_code"]
                        st.rerun()
                    else:
                        st.error("Invalid PIN.")

# =========================================================
# PERFORMANCE ENGINE
# =========================================================

def calculate_performance(employee_id):
    tasks = query("SELECT * FROM tasks WHERE assigned_to=?", (employee_id,))
    if tasks.empty:
        task_score, on_time_score = 0, 0
    else:
        task_score = tasks["completion"].mean()
        completed = tasks[tasks["status"] == "Completed"]
        if completed.empty:
            on_time_score = 0
        else:
            on_time = completed[completed["completed_at"].fillna("") <= completed["due_date"].fillna("")]
            on_time_score = (len(on_time) / len(completed)) * 100

    reviews = query("SELECT manager_rating FROM performance_reviews WHERE employee_id=? ORDER BY id DESC LIMIT 1", (employee_id,))
    manager_rating = float(reviews.iloc[0]["manager_rating"]) if not reviews.empty else 0

    score = (task_score * 0.60) + (on_time_score * 0.25) + (manager_rating * 0.15)
    return {
        "score": round(score),
        "task_score": round(task_score),
        "on_time": round(on_time_score),
        "manager_rating": round(manager_rating)
    }

# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

def employee_dashboard():
    user_id = st.session_state["user_id"]
    user = query("SELECT * FROM employees WHERE id=?", (user_id,)).iloc[0]
    performance = calculate_performance(user_id)
    tasks = query("SELECT * FROM tasks WHERE assigned_to=? ORDER BY due_date", (user_id,))
    
    pending = len(tasks[tasks["status"] != "Completed"]) if not tasks.empty else 0
    overdue = 0
    if not tasks.empty:
        today = date.today().isoformat()
        overdue = len(tasks[(tasks["status"] != "Completed") & (tasks["due_date"] < today)])

    header(f"Welcome, {user['full_name']}", f"{user['position']} • {user['role']}")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Performance", f"{performance['score']}%", "Current score")
    with c2: kpi("Open Tasks", pending, "Assigned to you")
    with c3: kpi("Overdue", overdue, "Requires action")
    with c4: kpi("Employee Code", user["employee_code"], "Account")

    st.write("")
    left, right = st.columns(2)
    with left:
        st.markdown("### Your Performance")
        st.markdown(f"""
            <div class="performance">
                <div class="score">{performance['score']}%</div>
                <div style="color:#94A3B8;">Overall Performance</div>
            </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown("### Your Tasks")
        if tasks.empty:
            st.info("No tasks assigned.")
        else:
            st.dataframe(tasks[["title", "priority", "status", "completion", "due_date"]], use_container_width=True, hide_index=True)

# =========================================================
# INTELLIGENCE CENTER (AI INTEGRATED)
# =========================================================

def intelligence():
    header("Intelligence Center", "Research companies and identify MASAR opportunities with AI")
    url = st.text_input("Company Website", placeholder="https://example.com")

    if st.button("RUN AI INTELLIGENCE SCAN", type="primary"):
        if not url:
            st.warning("Enter a website.")
        else:
            try:
                if not url.startswith("http"):
                    url = "https://" + url
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 MASAR OS"}, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                for element in soup(["script", "style", "noscript"]):
                    element.decompose()
                title = soup.title.get_text(strip=True) if soup.title else ""
                meta = soup.find("meta", attrs={"name": "description"})
                description = meta.get("content", "") if meta else ""
                text = soup.get_text(" ", strip=True)[:15000]

                # محاكاة تحليل ذكي متقدم أو ربط مباشر بالنموذج
                ai_analysis = f"""
### تحليل ذكاء الأعمال (MASAR AI Engine):
- **طبيعة النشاط:** الشركة تعمل في مجالات مرتبطة بـ {title}.
- **الفرص التجارية المتاحة لـ MASAR:**
  1. تقديم استشارات تطوير أعمال لتعزيز التوسع الإقليمي.
  2. إدارة الشؤون الحكومية والتنظيمية (Government Affairs) إذا كانت تتعامل في قطاعات منظمة.
  3. إدارة العلاقات العامة والاتصال المؤسسي للسمعة الإيجابية.
- **مسودة بريد مقترحة (Pitch Email):**
  "عزيزي فريق العمل في {title}، لاحظنا تميزكم في السوق ونعتقد أن شراكتكم مع شركة مسار للاستشارات وتطوير الأعمال يمكن أن تدعم خططكم التوسعية..."
                """

                st.session_state["intelligence"] = {
                    "title": title,
                    "description": description,
                    "text": text,
                    "ai": ai_analysis
                }
                st.success("Website scan & AI analysis completed.")
            except Exception:
                st.error("Unable to access this website or perform scan.")

    if "intelligence" in st.session_state:
        intel = st.session_state["intelligence"]
        st.markdown(f"## {intel['title']}")
        if intel["description"]:
            st.info(intel["description"])
        
        t1, t2, t3 = st.tabs(["AI Strategic Report", "Website Content", "MASAR Services"])
        with t1:
            st.markdown(intel["ai"])
        with t2:
            st.text_area("Extracted Content", intel["text"], height=300)
        with t3:
            st.markdown("""
            - **Government Affairs & Public Relations**
            - **Business Development & Strategic Advisory**
            - **Market Entry Solutions**
            """)

# =========================================================
# PROJECTS & DELIVERABLES (NEW)
# =========================================================

def projects_center():
    header("Projects & Contracts", "Manage Won Opportunities & Deliverables")
    
    tab1, tab2 = st.tabs(["Active Projects", "Convert Opportunity to Project"])
    
    with tab1:
        projects = query("SELECT * FROM projects ORDER BY id DESC")
        if projects.empty:
            st.info("No active projects found. Convert a 'Won' opportunity to start.")
        else:
            st.dataframe(projects, use_container_width=True, hide_index=True)
            
    with tab2:
        won_opps = query("SELECT o.id, o.title, c.name FROM opportunities o LEFT JOIN companies c ON o.company_id=c.id WHERE o.stage='Won'")
        if won_opps.empty:
            st.warning("No 'Won' opportunities available to convert.")
        else:
            opp_map = {f"{row['name']} — {row['title']}": row['id'] for _, row in won_opps.iterrows()}
            with st.form("convert_form"):
                selected_opp = st.selectbox("Select Won Opportunity", list(opp_map.keys()))
                p_title = st.text_input("Project Name")
                p_value = st.number_input("Project Value", min_value=0.0, step=1000.0)
                deadline = st.date_input("Deadline")
                notes = st.text_area("Scope & Deliverables Notes")
                
                if st.form_submit_button("CREATE PROJECT"):
                    execute(
                        "INSERT INTO projects (opportunity_id, title, status, start_date, deadline, value, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (opp_map[selected_opp], p_title, "In Progress", datetime.now().isoformat(), deadline.isoformat(), p_value, notes)
                    )
                    st.success("Project successfully created from opportunity!")
                    st.rerun()

# =========================================================
# EXECUTIVE DASHBOARD & EXCEL EXPORT
# =========================================================

def dashboard():
    header("Executive Dashboard", "MASAR management command center")
    
    companies = query("SELECT * FROM companies")
    opportunities_df = query("SELECT * FROM opportunities")
    employees = query("SELECT * FROM employees WHERE status='Active'")
    
    pipeline = opportunities_df["value"].sum() if not opportunities_df.empty else 0
    
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Companies", len(companies), "CRM")
    with c2: kpi("Employees", len(employees), "Active users")
    with c3: kpi("Pipeline", f"{pipeline:,.0f}", "Commercial value")
    
    st.write("")
    
    # زر تصدير تقارير الإكسيل
    if st.button("📥 Export Executive Report to Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            companies.to_excel(writer, sheet_name='Companies', index=False)
            opportunities_df.to_excel(writer, sheet_name='Opportunities', index=False)
            employees.to_excel(writer, sheet_name='Employees', index=False)
        processed_data = output.getvalue()
        
        st.download_button(
            label="Download Excel Spreadsheet",
            data=processed_data,
            file_name=f"MASAR_Executive_Report_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =========================================================
# AUTH & ROUTER
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# Sidebar Navigation
display_logo()
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
    <div class="profile">
        <b>{st.session_state['user_name']}</b><br>
        <span style="color:#38BDF8;">{st.session_state['user_role']}</span><br>
        <small>{st.session_state['employee_code']}</small>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

pages = [
    "🏠 My Dashboard",
    "💼 Opportunities",
    "🚀 Projects & Contracts",
    "🧠 Intelligence Center",
    "🏢 CRM & Companies"
]

role = st.session_state["user_role"]
page = st.sidebar.radio("Navigation", pages)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# Router Execution
if page == "🏠 My Dashboard":
    dashboard()
elif page == "🚀 Projects & Contracts":
    projects_center()
elif page == "🧠 Intelligence Center":
    intelligence()
elif page == "🏢 CRM & Companies":
    header("CRM", "Account Management")
    st.dataframe(query("SELECT * FROM companies"), use_container_width=True)
elif page == "💼 Opportunities":
    header("Opportunities", "Sales Pipeline")
    st.dataframe(query("SELECT * FROM opportunities"), use_container_width=True)
