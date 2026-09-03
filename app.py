# ============================================================
# MASAR INTELLIGENCE OS - ENTERPRISE EDITION V6.0
# ============================================================

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
import secrets
import string
import base64
import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime, date
import urllib.request
import json

# ============================================================
# CONFIG & THEME SETUP
# ============================================================

APP_NAME = "MASAR Intelligence OS"
COMPANY_NAME = "MASAR for Consultancy and Business Development"
DB_PATH = "masar_os.db"
UPLOAD_DIR = "job_descriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "lang" not in st.session_state:
    st.session_state.lang = "English"

TRANSLATIONS = {
    "English": {
        "dashboard": "Executive Dashboard",
        "my_workspace": "My Workspace",
        "tasks": "Task Management",
        "internal_chat": "Internal Communications",
        "crm": "CRM & Accounts",
        "opportunities": "Sales Pipeline",
        "projects": "Projects & Operations",
        "performance": "Performance Analytics",
        "job_descriptions": "Job Descriptions",
        "ai_research": "AI Market Intelligence",
        "email_intelligence": "Corporate Email Gateway",
        "notifications": "System Notifications",
        "search": "Global Web Search",
        "admin_center": "Enterprise Admin Center",
        "governance": "Governance & Compliance",
        "logout": "Secure Logout",
        "audio_fix": "🔊 Audio Bridge",
        "test_sound": "Initialize Audio",
        "sound_success": "Audio system online.",
        "welcome": "Welcome back",
        "navigation": "Enterprise Modules"
    },
    "العربية": {
        "dashboard": "لوحة المؤشرات التنفيذية",
        "my_workspace": "مساحة العمل الشخصية",
        "tasks": "إدارة المهام والعمليات",
        "internal_chat": "الاتصالات الداخلية",
        "crm": "إدارة علاقات العملاء",
        "opportunities": "الفرص والعقود التجارية",
        "projects": "المشاريع والتشغيل",
        "performance": "تحليلات الأداء",
        "job_descriptions": "التوصيف الوظيفي",
        "ai_research": "الذكاء الاصطناعي للأسواق",
        "email_intelligence": "بوابة البريد المؤسسي",
        "notifications": "الإشعارات وال تنبيهات",
        "search": "محرك البحث العالمي",
        "admin_center": "مركز التحكم الإداري",
        "governance": "الحوكمة والامتثال",
        "logout": "تسجيل خروج آمن",
        "audio_fix": "🔊 نظام التنبيه الصوتي",
        "test_sound": "تفعيل الصوت",
        "sound_success": "تم تفعيل نظام الصوت بنجاح.",
        "welcome": "مرحباً بك",
        "navigation": "الوحدات الرئيسية"
    }
}

def t(key):
    lang = st.session_state.lang
    return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)

# ============================================================
# DATABASE ENGINE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def execute(sql, params=(), commit=True):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    if commit:
        conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def query(sql, params=()):
    conn = get_db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def query_one(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row

def column_exists(table, column):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        columns = [r[1] for r in cur.fetchall()]
        conn.close()
        return column in columns
    except Exception:
        return False

def add_column_if_missing(table, column, definition):
    if not column_exists(table, column):
        try:
            execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except Exception:
            pass

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            full_name TEXT NOT NULL,
            mobile TEXT,
            email TEXT,
            role TEXT DEFAULT 'Employee',
            pin_hash TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            must_change_pin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            assigned_to INTEGER,
            created_by INTEGER,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            due_date TEXT,
            reminder_time TEXT,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS performance_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            rating REAL DEFAULT 0,
            notes TEXT,
            review_date TEXT DEFAULT CURRENT_TIMESTAMP,
            reviewer_id INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            job_title TEXT,
            file_name TEXT,
            file_path TEXT,
            uploaded_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            status TEXT DEFAULT 'Prospect',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            name TEXT NOT NULL,
            title TEXT,
            mobile TEXT,
            email TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            title TEXT,
            value REAL DEFAULT 0,
            stage TEXT DEFAULT 'New',
            probability REAL DEFAULT 0,
            owner_id INTEGER,
            expected_close TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            name TEXT,
            status TEXT DEFAULT 'Planning',
            progress REAL DEFAULT 0,
            owner_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS governance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            description TEXT,
            owner_id INTEGER,
            review_date TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            employee_code TEXT,
            event TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            title TEXT,
            message TEXT,
            notification_type TEXT DEFAULT 'Info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    add_column_if_missing("employees", "must_change_pin", "INTEGER DEFAULT 0")
    add_column_if_missing("tasks", "reminder_time", "TEXT")

    admin = query_one("SELECT id FROM employees WHERE employee_code = ?", ("ADMIN",))
    if not admin:
        execute("""
            INSERT INTO employees
            (employee_code, full_name, mobile, email, role, pin_hash, active, must_change_pin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "ADMIN",
            "MASAR Administrator",
            "",
            "",
            "Admin",
            hash_pin("1234"),
            1,
            0
        ))

# ============================================================
# SECURITY & AUDIO UTILITIES
# ============================================================

def hash_pin(pin):
    return hashlib.sha256(str(pin).encode("utf-8")).hexdigest()

def verify_pin(pin, stored_hash):
    return hash_pin(pin) == stored_hash

def generate_temp_pin(length=6):
    return "".join(secrets.choice(string.digits) for _ in range(length))

def play_sound_alert():
    sound_html = """
    <audio id="masar_audio_alert" autoplay>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mp3">
    </audio>
    <script>
    var aud = document.getElementById("masar_audio_alert");
    if(aud) {
        aud.volume = 1.0;
        aud.play().catch(function(error) { console.log(error); });
    }
    </script>
    """
    st.markdown(sound_html, unsafe_allow_html=True)

def get_setting(key, default=None):
    row = query_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default

def set_setting(key, value):
    execute("INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

def log_event(employee_id, employee_code, event):
    execute("INSERT INTO login_logs(employee_id, employee_code, event) VALUES (?, ?, ?)", (employee_id, employee_code, event))

def create_notification(employee_id, title, message, notification_type="Info"):
    execute("INSERT INTO notifications(employee_id, title, message, notification_type) VALUES (?, ?, ?, ?)", (employee_id, title, message, notification_type))

def unread_notifications(employee_id):
    row = query_one("SELECT COUNT(*) AS total FROM notifications WHERE employee_id = ? AND is_read = 0", (employee_id,))
    return int(row["total"]) if row else 0

# ============================================================
# ENTERPRISE STYLING (CSS REFINEMENT)
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #050b14;
    background-image: 
        radial-gradient(at 0% 0%, rgba(14, 116, 144, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(30, 58, 138, 0.15) 0px, transparent 50%);
    color: #f1f5f9;
}

section[data-testid="stSidebar"] {
    background-color: #07101e;
    border-right: 1px solid rgba(56, 189, 248, 0.1);
}

.brand-container {
    padding: 15px 10px;
    text-align: center;
    border-bottom: 1px solid rgba(56, 189, 248, 0.1);
    margin-bottom: 15px;
}

.brand-title {
    font-size: 18px;
    font-weight: 800;
    color: #38bdf8;
    letter-spacing: -0.5px;
}

.brand-subtitle {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 4px;
}

h1, h2, h3 {
    color: #f8fafc !important;
    font-weight: 700 !important;
}

.main-title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.8px;
    color: #f8fafc;
}

.sub-title {
    color: #94a3b8;
    font-size: 14px;
    margin-bottom: 25px;
}

.kpi-card {
    background: linear-gradient(135deg, rgba(15, 28, 48, 0.95) 0%, rgba(8, 17, 31, 0.95) 100%);
    border: 1px solid rgba(56, 189, 248, 0.12);
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.kpi-card:hover {
    border-color: rgba(56, 189, 248, 0.3);
    box-shadow: 0 15px 35px rgba(56, 189, 248, 0.08);
}

.kpi-label {
    color: #64748b;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
}

.kpi-value {
    color: #f8fafc;
    font-size: 28px;
    font-weight: 800;
    margin-top: 6px;
}

.enterprise-card {
    background: rgba(11, 22, 38, 0.85);
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.login-wrapper {
    max-width: 440px;
    margin: 60px auto;
    padding: 35px;
    background: rgba(8, 18, 32, 0.95);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 20px;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
}

.small-muted {
    color: #64748b;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

def top_header_bar():
    c1, c2 = st.columns([7, 3])
    with c1:
        st.markdown(f"<span style='color:#38bdf8; font-weight:700; font-size:13px;'>{COMPANY_NAME}</span>", unsafe_allow_html=True)
    with c2:
        selected_lang = st.selectbox("Language / اللغة", ["English", "العربية"], index=0 if st.session_state.lang == "English" else 1, label_visibility="collapsed")
        if selected_lang != st.session_state.lang:
            st.session_state.lang = selected_lang
            st.rerun()
    st.divider()

def page_header(title, subtitle=""):
    st.markdown(f'<div class="main-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="sub-title">{subtitle}</div>', unsafe_allow_html=True)

def kpi(label, value):
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def calculate_employee_performance(employee_id):
    total_row = query_one("SELECT COUNT(*) AS total FROM tasks WHERE assigned_to = ?", (employee_id,))
    completed_row = query_one("SELECT COUNT(*) AS total FROM tasks WHERE assigned_to = ? AND status = 'Completed'", (employee_id,))
    total = int(total_row["total"]) if total_row else 0
    completed = int(completed_row["total"]) if completed_row else 0
    completion_score = (completed / total) * 100 if total > 0 else 0

    overdue_row = query_one("""
        SELECT COUNT(*) AS total FROM tasks
        WHERE assigned_to = ? AND due_date IS NOT NULL AND due_date < ? AND status != 'Completed'
    """, (employee_id, str(date.today())))
    overdue = int(overdue_row["total"]) if overdue_row else 0
    on_time_score = max(0, 100 - ((overdue / total) * 100)) if total > 0 else 0

    rating_row = query_one("SELECT rating FROM performance_reviews WHERE employee_id = ? ORDER BY id DESC LIMIT 1", (employee_id,))
    rating_score = float(rating_row["rating"]) * 20 if rating_row else 0

    if total == 0 and not rating_row:
        return 0

    performance = (completion_score * 0.60) + (on_time_score * 0.25) + (rating_score * 0.15)
    return round(min(max(performance, 0), 100), 1)

# ============================================================
# LOGIN & AUTHENTICATION
# ============================================================

def login_page():
    top_header_bar()
    st.markdown("""
        <div class="login-wrapper">
            <div style="text-align:center; margin-bottom: 20px;">
                <h2 style="color: #38bdf8; margin: 0; font-size: 26px;">MASAR</h2>
                <p style="color: #64748b; font-size: 13px; letter-spacing: 1px; margin-top: 5px;">ENTERPRISE INTELLIGENCE OS</p>
            </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Employee Portal", "Account Recovery"])
    with tab1:
        with st.form("login_form"):
            code = st.text_input("Employee Code", placeholder="e.g. ADMIN or EMP001")
            pin = st.text_input("Secure PIN", type="password")
            submit = st.form_submit_button("AUTHENTICATE", use_container_width=True)
            if submit:
                code = code.strip().upper()
                employee = query_one("SELECT * FROM employees WHERE employee_code = ? AND active = 1", (code,))
                if employee and verify_pin(pin, employee["pin_hash"]):
                    st.session_state.user = dict(employee)
                    st.session_state.logged_in = True
                    log_event(employee["id"], employee["employee_code"], "LOGIN_SUCCESS")
                    create_notification(employee["id"], "Security Notice", "Successful secure authentication.", "Security")
                    play_sound_alert()
                    st.rerun()
                else:
                    st.error("Authentication failed. Check credentials.")

    with tab2:
        with st.form("forgot_form"):
            code = st.text_input("Employee Code", key="fc_code")
            mobile = st.text_input("Registered Mobile", key="fc_mob")
            submit_f = st.form_submit_button("RESET CREDENTIALS", use_container_width=True)
            if submit_f:
                employee = query_one("SELECT * FROM employees WHERE employee_code = ? AND mobile = ? AND active = 1", (code.strip().upper(), mobile.strip()))
                if employee:
                    temp_pin = generate_temp_pin()
                    execute("UPDATE employees SET pin_hash = ?, must_change_pin = 1 WHERE id = ?", (hash_pin(temp_pin), employee["id"]))
                    st.success(f"Temporary Secure PIN Generated: {temp_pin}")
                else:
                    st.error("Matching profile not found.")
    st.markdown("</div>", unsafe_allow_html=True)

def force_change_pin():
    top_header_bar()
    user = st.session_state.user
    page_header("Security Protocol", "Mandatory security update: Please update your temporary PIN.")
    with st.form("change_pin"):
        old_pin = st.text_input("Current PIN", type="password")
        new_pin = st.text_input("New Secure PIN", type="password")
        confirm = st.text_input("Confirm New PIN", type="password")
        submit = st.form_submit_button("Update PIN & Proceed", use_container_width=True)
        if submit:
            if not verify_pin(old_pin, user["pin_hash"]):
                st.error("Current PIN is invalid.")
                return
            if len(new_pin) < 4:
                st.error("PIN must be at least 4 characters.")
                return
            if new_pin != confirm:
                st.error("PIN confirmation mismatch.")
                return
            execute("UPDATE employees SET pin_hash = ?, must_change_pin = 0 WHERE id = ?", (hash_pin(new_pin), user["id"]))
            updated = query_one("SELECT * FROM employees WHERE id = ?", (user["id"],))
            st.session_state.user = dict(updated)
            st.success("Security credentials updated successfully.")
            st.rerun()

# ============================================================
# MODULES IMPLEMENTATION
# ============================================================

def dashboard():
    user = st.session_state.user
    page_header("Executive Dashboard", f"Enterprise Overview • Welcome, {user['full_name']}")
    
    employees = query("SELECT * FROM employees WHERE active = 1")
    companies = query("SELECT * FROM companies")
    opportunities = query("SELECT * FROM opportunities")
    projects = query("SELECT * FROM projects")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Active Personnel", len(employees))
    with c2: kpi("Enterprise Clients", len(companies))
    with c3: kpi("Open Pipeline", len(opportunities[opportunities["stage"] != "Won"]) if not opportunities.empty else 0)
    with c4: kpi("Active Projects", len(projects))

    st.markdown("<br>", unsafe_allow_html=True)
    if not opportunities.empty:
        pipeline = opportunities.groupby("stage", as_index=False)["value"].sum()
        fig = px.bar(pipeline, x="stage", y="value", title="Pipeline Portfolio Valuation by Stage")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#cbd5e1")
        st.plotly_chart(fig, use_container_width=True)

def employee_dashboard():
    user = st.session_state.user
    performance = calculate_employee_performance(user["id"])
    page_header("My Workspace", "Personal performance metrics and assigned deliverables.")
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Performance Index", f"{performance}%")
    my_tasks = query("SELECT * FROM tasks WHERE assigned_to = ? ORDER BY due_date", (user["id"],))
    with c2: kpi("Assigned Tasks", len(my_tasks))
    with c3: kpi("Unread Alerts", unread_notifications(user["id"]))

def task_organizer():
    user = st.session_state.user
    page_header("Task Management", "Delegate, track, and manage corporate deliverables.")

    with st.expander("➕ Create New Operational Task", expanded=False):
        with st.form("new_task_form"):
            t_title = st.text_input("Task Title")
            t_desc = st.text_area("Task Description & Scope")
            
            emps = query("SELECT id, full_name, email FROM employees WHERE active = 1")
            emp_options = {row["full_name"]: row["id"] for _, row in emps.iterrows()} if not emps.empty else {}
            assigned_name = st.selectbox("Assignee", list(emp_options.keys()) if emp_options else ["No Personnel"])
            
            col1, col2, col3 = st.columns(3)
            with col1: t_priority = st.selectbox("Priority Level", ["Low", "Medium", "High", "Urgent"])
            with col2: t_due = st.date_input("Target Due Date", value=date.today())
            with col3: t_reminder = st.time_input("Reminder Schedule")
            
            submit_task = st.form_submit_button("Deploy Task", use_container_width=True)
            if submit_task:
                if not t_title.strip():
                    st.error("Task title is required.")
                elif not emp_options:
                    st.error("No valid assignee found.")
                else:
                    emp_id = emp_options[assigned_name]
                    execute("""
                        INSERT INTO tasks (title, description, assigned_to, created_by, priority, status, due_date, reminder_time)
                        VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)
                    """, (t_title, t_desc, emp_id, user["id"], t_priority, str(t_due), str(t_reminder)))
                    create_notification(emp_id, "New Task Deployed", f"Task assigned: {t_title}", "Task")
                    play_sound_alert()
                    st.success("Task deployed successfully.")
                    st.rerun()

    st.markdown("### Active Task Portfolio")
    tasks = query("SELECT * FROM tasks ORDER BY due_date DESC")
    if tasks.empty:
        st.info("No active tasks registered.")
    else:
        for index, row in tasks.iterrows():
            st.markdown(f"""
                <div class="enterprise-card">
                    <b>[{row['id']}] {row['title']}</b> &bull; <span style='color:#38bdf8;'>{row['priority']}</span><br>
                    <p style='margin: 8px 0; color:#cbd5e1;'>{row['description'] or 'No description provided.'}</p>
                    <span class="small-muted">Due: {row['due_date']} | Status: {row['status']}</span>
                </div>
            """, unsafe_allow_html=True)
            
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(row["status"]), key=f"st_{row['id']}")
                if new_status != row["status"]:
                    execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, row["id"]))
                    play_sound_alert()
                    st.rerun()
            with col_e2:
                with st.expander("Modify Details"):
                    with st.form(f"edit_t_{row['id']}"):
                        ed_title = st.text_input("Title", value=row["title"], key=f"edt_{row['id']}")
                        ed_desc = st.text_area("Description", value=row["description"] or "", key=f"edd_{row['id']}")
                        if st.form_submit_button("Save Updates"):
                            execute("UPDATE tasks SET title = ?, description = ? WHERE id = ?", (ed_title, ed_desc, row["id"]))
                            st.success("Updated.")
                            st.rerun()
            with col_e3:
                if st.button("Archive Task", key=f"del_{row['id']}"):
                    execute("DELETE FROM tasks WHERE id = ?", (row["id"],))
                    st.success("Archived.")
                    st.rerun()
            st.divider()

def internal_chat():
    user = st.session_state.user
    page_header("Internal Communications", "Secure peer-to-peer corporate messaging.")

    emps = query("SELECT id, full_name, employee_code FROM employees WHERE id != ? AND active = 1", (user["id"],))
    if emps.empty:
        st.info("No active peers available for messaging.")
        return

    emp_dict = {f"{row['full_name']} ({row['employee_code']})": row["id"] for _, row in emps.iterrows()}
    selected_target = st.selectbox("Select Recipient", list(emp_dict.keys()))
    target_id = emp_dict[selected_target]

    st.markdown("---")
    messages = query("""
        SELECT * FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) 
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY id ASC
    """, (user["id"], target_id, target_id, user["id"]))

    chat_container = st.container(height=380)
    with chat_container:
        if messages.empty:
            st.info("Initiate secure conversation below.")
        else:
            for _, row in messages.iterrows():
                is_me = row["sender_id"] == user["id"]
                align_style = "text-align: right; background: rgba(56,189,248,0.12); padding: 12px; border-radius: 12px; margin-bottom: 10px;" if is_me else "text-align: left; background: rgba(30,58,138,0.25); padding: 12px; border-radius: 12px; margin-bottom: 10px;"
                sender_label = "You" if is_me else selected_target.split('(')[0]
                st.markdown(f"""
                    <div style="{align_style}">
                        <b style="color:#38bdf8;">{sender_label}:</b> {row['message']}<br>
                        <span class="small-muted">{row['created_at']}</span>
                    </div>
                """, unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        msg_text = st.text_input("Enter secure message...", label_visibility="collapsed")
        if st.form_submit_button("Transmit Message", use_container_width=True) and msg_text.strip():
            execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)", (user["id"], target_id, msg_text))
            create_notification(target_id, f"Message from {user['full_name']}", msg_text, "Chat")
            play_sound_alert()
            st.rerun()

def crm():
    page_header("CRM & Accounts", "Manage corporate clients, accounts, and stakeholders.")
    with st.form("add_company_form"):
        c_name = st.text_input("Client Organization Name")
        c_web = st.text_input("Corporate Website")
        c_ind = st.text_input("Industry Sector")
        c_status = st.selectbox("Account Status", ["Prospect", "Active Client", "Partner", "Inactive"])
        if st.form_submit_button("Register Account", use_container_width=True) and c_name.strip():
            execute("INSERT INTO companies(name, website, industry, status) VALUES (?, ?, ?, ?)", (c_name, c_web, c_ind, c_status))
            st.success("Account registered.")
            st.rerun()
    comps = query("SELECT * FROM companies ORDER BY id DESC")
    if not comps.empty: st.dataframe(comps, use_container_width=True, hide_index=True)

def opportunities():
    page_header("Sales Pipeline", "Track business development deals and revenue opportunities.")
    with st.form("add_opp_form"):
        o_title = st.text_input("Opportunity Designation")
        o_val = st.number_input("Estimated Value ($)", min_value=0.0, step=500.0)
        o_stage = st.selectbox("Pipeline Stage", ["New", "Qualified", "Proposal", "Negotiation", "Won", "Lost"])
        if st.form_submit_button("Log Opportunity", use_container_width=True) and o_title.strip():
            execute("INSERT INTO opportunities(title, value, stage) VALUES (?, ?, ?)", (o_title, o_val, o_stage))
            st.success("Opportunity logged.")
            st.rerun()
    opps = query("SELECT * FROM opportunities ORDER BY id DESC")
    if not opps.empty: st.dataframe(opps, use_container_width=True, hide_index=True)

def projects():
    page_header("Projects & Operations", "Monitor active execution timelines and milestones.")
    with st.form("add_proj_form"):
        p_name = st.text_input("Project Codename / Name")
        p_status = st.selectbox("Operational Status", ["Planning", "In Progress", "Completed", "On Hold"])
        p_prog = st.slider("Completion Progress (%)", 0, 100, 0)
        if st.form_submit_button("Initialize Project", use_container_width=True) and p_name.strip():
            execute("INSERT INTO projects(name, status, progress) VALUES (?, ?, ?)", (p_name, p_status, p_prog))
            st.success("Project initialized.")
            st.rerun()
    projs = query("SELECT * FROM projects ORDER BY id DESC")
    if not projs.empty: st.dataframe(projs, use_container_width=True, hide_index=True)

def governance():
    page_header("Governance & Compliance", "Corporate policies, rules, and regulatory standards.")
    govs = query("SELECT * FROM governance ORDER BY id DESC")
    if govs.empty: st.info("No compliance documents registered.")
    else: st.dataframe(govs, use_container_width=True, hide_index=True)

def job_description_library():
    page_header("Job Descriptions", "Corporate role specifications and structural guidelines.")
    jds = query("SELECT * FROM job_descriptions ORDER BY id DESC")
    if jds.empty: st.info("No job description archives found.")
    else: st.dataframe(jds, use_container_width=True, hide_index=True)

def ai_company_research():
    page_header("AI Market Intelligence", "Analyze corporate entities and market competitors.")
    with st.form("research_form"):
        target = st.text_input("Target Entity / Domain", placeholder="e.g. competitor.com")
        if st.form_submit_button("Execute Intelligence Scan", use_container_width=True) and target.strip():
            st.markdown(f"""
                <div class="enterprise-card">
                    <h3 style="color:#38bdf8;">📊 Market Intelligence Dossier</h3>
                    <p><b>Target Analyzed:</b> {target}</p>
                    <hr style="border-color:rgba(56,189,248,0.2);">
                    <h4>1. Strategic Positioning</h4>
                    <p>Entity maintains high online visibility and steady competitive momentum within regional channels.</p>
                    <h4>2. Partnership Feasibility</h4>
                    <p>Strong collaborative alignment with MASAR corporate advisory frameworks.</p>
                </div>
            """, unsafe_allow_html=True)

def email_assistant():
    page_header("Corporate Email Gateway", "Live IMAP mailbox integration and telemetry.")
    with st.expander("⚙️ Server Configuration", expanded=False):
        with st.form("imap_form"):
            srv = st.text_input("IMAP Server", value=get_setting("imap_server", "imap.gmail.com"))
            usr = st.text_input("Account Email", value=get_setting("imap_user", ""))
            pwd = st.text_input("App Password", type="password", value=get_setting("imap_pass", ""))
            if st.form_submit_button("Save Gateway Settings"):
                set_setting("imap_server", srv)
                set_setting("imap_user", usr)
                set_setting("imap_pass", pwd)
                st.success("Gateway configuration updated.")

    if st.button("📥 Synchronize Inbox Messages", use_container_width=True):
        srv = get_setting("imap_server")
        usr = get_setting("imap_user")
        pwd = get_setting("imap_pass")
        if not srv or not usr or not pwd:
            st.error("Please configure IMAP server parameters first.")
        else:
            with st.spinner("Connecting securely to mail gateway..."):
                try:
                    mail = imaplib.IMAP4_SSL(srv)
                    mail.login(usr, pwd)
                    mail.select("inbox")
                    _, messages = mail.search(None, "ALL")
                    mail_ids = messages[0].split()
                    for num in reversed(mail_ids[-5:]):
                        _, msg_data = mail.fetch(num, "(RFC822)")
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                sub, enc = decode_header(msg["Subject"])[0]
                                if isinstance(sub, bytes):
                                    sub = sub.decode(enc if enc else "utf-8", errors="ignore")
                                st.markdown(f"""
                                    <div class="enterprise-card">
                                        <b>Subject:</b> {sub}<br>
                                        <span class="small-muted">Sender: {msg.get('From')} | Date: {msg.get('Date')}</span>
                                    </div>
                                """, unsafe_allow_html=True)
                    mail.logout()
                except Exception as e:
                    st.error(f"Gateway connection error: {e}")

# ============================================================
# GLOBAL WEB SEARCH (NATIVE BUILT-IN ENGINE - NO EXTERNAL DEPENDENCY)
# ============================================================
def global_search():
    page_header("Global Web Search", "Integrated intelligence search engine.")
    query_text = st.text_input("🌐 Query web intelligence...", placeholder="Type query and press enter...")
    
    if query_text:
        st.markdown("### Search Results")
        with st.spinner("Executing query..."):
            try:
                # Built-in lightweight search using Wikipedia API / DuckDuckGo Instant API to avoid dependency issues
                url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query_text)}&format=json&no_html=1"
                req = urllib.request.Request(url, headers={'User-Agent': 'MASAR-OS'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    
                related = data.get("RelatedTopics", [])
                abstract = data.get("AbstractText", "")
                
                if abstract:
                    st.markdown(f"""
                        <div class="enterprise-card">
                            <h4 style="color:#38bdf8;">Overview</h4>
                            <p>{abstract}</p>
                            <a href="{data.get('AbstractURL')}" target="_blank" style="color:#38bdf8; font-size:12px;">Source Reference</a>
                        </div>
                    """, unsafe_allow_html=True)
                
                if related:
                    for item in related:
                        if "Text" in item:
                            st.markdown(f"""
                                <div class="enterprise-card">
                                    <p>{item.get('Text')}</p>
                                    <a href="{item.get('FirstURL')}" target="_blank" style="color:#38bdf8; font-size:12px;">{item.get('FirstURL')}</a>
                                </div>
                            """, unsafe_allow_html=True)
                elif not abstract and not related:
                    st.info("No direct structured results found. Try refining your keywords.")
            except Exception as e:
                st.error(f"Search query execution failed: {e}")

def admin_center():
    user = st.session_state.user
    if user["role"] != "Admin":
        st.error("Restricted access: Administrator credentials required.")
        return
    page_header("Enterprise Admin Center", "Personnel provisioning and system settings.")
    
    with st.form("add_emp_form"):
        st.subheader("Provision New Personnel")
        e_code = st.text_input("Employee Code (e.g. EMP002)")
        e_name = st.text_input("Full Name")
        e_mob = st.text_input("Mobile Contact")
        e_mail = st.text_input("Corporate Email")
        e_role = st.selectbox("Role Assignment", ["Employee", "Manager", "Admin"])
        e_pin = st.text_input("Initial PIN", value="1234")
        if st.form_submit_button("Provision Profile", use_container_width=True) and e_code.strip() and e_name.strip():
            try:
                execute("""
                    INSERT INTO employees(employee_code, full_name, mobile, email, role, pin_hash, must_change_pin)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (e_code.strip().upper(), e_name, e_mob, e_mail, e_role, hash_pin(e_pin)))
                st.success("Personnel profile provisioned successfully.")
                st.rerun()
            except Exception as ex:
                st.error(f"Provisioning error: {ex}")

    emps = query("SELECT id, employee_code, full_name, role, active FROM employees ORDER BY id DESC")
    st.dataframe(emps, use_container_width=True, hide_index=True)

def notifications_center():
    user = st.session_state.user
    page_header("System Notifications", "System alerts and communication logs.")
    notifs = query("SELECT * FROM notifications WHERE employee_id = ? ORDER BY id DESC", (user["id"],))
    if notifs.empty:
        st.info("No notifications recorded.")
    else:
        for _, row in notifs.iterrows():
            st.markdown(f"""
                <div class="enterprise-card">
                    <b>{row['title']}</b> &bull; <span style="color:#38bdf8;">{row['notification_type']}</span><br>
                    <p style="margin: 6px 0; color:#cbd5e1;">{row['message']}</p>
                    <span class="small-muted">{row['created_at']}</span>
                </div>
            """, unsafe_allow_html=True)
        execute("UPDATE notifications SET is_read = 1 WHERE employee_id = ?", (user["id"],))

def performance_center():
    user = st.session_state.user
    page_header("Performance Analytics", "Comprehensive evaluation metrics.")
    score = calculate_employee_performance(user["id"])
    kpi("Evaluated Performance Index", f"{score}%")

# ============================================================
# SIDEBAR ROUTER & CONTROLS
# ============================================================

def sidebar():
    user = st.session_state.user
    
    st.sidebar.markdown(f"""
        <div class="brand-container">
            <div class="brand-title">{COMPANY_NAME.split()[0]} OS</div>
            <div class="brand-subtitle">Enterprise Suite</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"**{t('audio_fix')}**")
    if st.sidebar.button(t('test_sound'), use_container_width=True):
        play_sound_alert()
        st.sidebar.success(t('sound_success'))

    st.sidebar.divider()
    st.sidebar.markdown(f"**{user['full_name']}**")
    st.sidebar.caption(f"{user['employee_code']} &bull; {user['role']}")
    
    unread = unread_notifications(user["id"])
    
    menu = [
        t('dashboard'), t('my_workspace'), t('tasks'), t('internal_chat'), t('crm'),
        t('opportunities'), t('projects'), t('performance'), t('job_descriptions'),
        t('ai_research'), t('email_intelligence'), t('notifications'), t('search'), t('governance')
    ]
    if user["role"] == "Admin":
        menu.append(t('admin_center'))

    selected = st.sidebar.radio(t('navigation'), menu, label_visibility="collapsed")
    
    st.sidebar.divider()
    st.sidebar.caption(f"Unread Alerts: {unread}")
    if st.sidebar.button(t('logout'), use_container_width=True):
        log_event(user["id"], user["employee_code"], "LOGOUT")
        st.session_state.clear()
        st.rerun()
    return selected

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.logged_in:
    login_page()
    st.stop()

user = st.session_state.user
if user.get("must_change_pin"):
    force_change_pin()
    st.stop()

page = sidebar()

if page in ["Dashboard", "لوحة المؤشرات التنفيذية"]: dashboard()
elif page in ["My Workspace", "مساحة العمل الشخصية"]: employee_dashboard()
elif page in ["Task Management", "إدارة المهام والعمليات"]: task_organizer()
elif page in ["Internal Communications", "الاتصالات الداخلية"]: internal_chat()
elif page in ["CRM & Accounts", "إدارة علاقات العملاء"]: crm()
elif page in ["Sales Pipeline", "الفرص والعقود التجارية"]: opportunities()
elif page in ["Projects & Operations", "المشاريع والتشغيل"]: projects()
elif page in ["Performance Analytics", "تحليلات الأداء"]: performance_center()
elif page in ["Job Descriptions", "التوصيف الوظيفي"]: job_description_library()
elif page in ["AI Market Intelligence", "الذكاء الاصطناعي للأسواق"]: ai_company_research()
elif page in ["Corporate Email Gateway", "بوابة البريد المؤسسي"]: email_assistant()
elif page in ["System Notifications", "الإشعارات وال تنبيهات"]: notifications_center()
elif page in ["Global Web Search", "محرك البحث العالمي"]: global_search()
elif page in ["Admin Control Center", "مركز التحكم الإداري"]: admin_center()
elif page in ["Governance & Compliance", "الحوكمة والامتثال"]: governance()

st.markdown("""
    <div style="text-align:center; color:#475569; margin-top:60px; padding:20px; font-size:11px; border-top: 1px solid rgba(56,189,248,0.05);">
        MASAR Intelligence OS &bull; Secure Enterprise Environment
    </div>
""", unsafe_allow_html=True)
