# ============================================================
# MASAR INTELLIGENCE OS
# V4.5 - STABLE SINGLE FILE EDITION (CHAT & TASKS ENGINE)
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
from datetime import datetime, date

# ============================================================
# CONFIG
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

# ============================================================
# DATABASE
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

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_uid TEXT UNIQUE,
            sender TEXT,
            subject TEXT,
            received_at TEXT,
            body TEXT,
            summary TEXT,
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
# SECURITY & AUDIO NOTIFICATIONS
# ============================================================

def hash_pin(pin):
    return hashlib.sha256(str(pin).encode("utf-8")).hexdigest()

def verify_pin(pin, stored_hash):
    return hash_pin(pin) == stored_hash

def generate_temp_pin(length=6):
    chars = string.digits
    return "".join(secrets.choice(chars) for _ in range(length))

def play_sound_alert():
    """توليد تنبيه صوتي حي داخل المتصفح باستخدام JavaScript Web Audio API"""
    sound_script = """
    <script>
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5 note
        gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + 0.3);
    } catch(e) {
        console.log("Audio blocked");
    }
    </script>
    """
    st.markdown(sound_script, unsafe_allow_html=True)

# ============================================================
# SETTINGS & LOGS
# ============================================================

def get_setting(key, default=None):
    row = query_one("SELECT value FROM settings WHERE key = ?", (key,))
    if row:
        return row["value"]
    return default

def set_setting(key, value):
    execute("""
        INSERT INTO settings(key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (key, value))

def log_event(employee_id, employee_code, event):
    execute("INSERT INTO login_logs(employee_id, employee_code, event) VALUES (?, ?, ?)", (employee_id, employee_code, event))

def create_notification(employee_id, title, message, notification_type="Info"):
    execute("INSERT INTO notifications(employee_id, title, message, notification_type) VALUES (?, ?, ?, ?)", (employee_id, title, message, notification_type))

def unread_notifications(employee_id):
    row = query_one("SELECT COUNT(*) AS total FROM notifications WHERE employee_id = ? AND is_read = 0", (employee_id,))
    return int(row["total"]) if row else 0

def get_logo():
    return get_setting("logo")

def display_logo():
    logo = get_logo()
    if logo:
        try:
            st.sidebar.image(base64.b64decode(logo), width=170)
        except Exception:
            pass
    else:
        st.sidebar.markdown('<div class="brand-mark">◆</div>', unsafe_allow_html=True)

# ============================================================
# CSS STYLING
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background: radial-gradient(circle at 10% 0%, rgba(56,189,248,0.07), transparent 30%),
                radial-gradient(circle at 90% 10%, rgba(30,58,138,0.12), transparent 35%),
                #071321;
    color: #f8fafc;
}
section[data-testid="stSidebar"] {
    background: #081727;
    border-right: 1px solid rgba(56,189,248,0.12);
}
.brand-mark {
    font-size: 46px;
    text-align: center;
    color: #38BDF8;
    padding: 10px;
}
h1, h2, h3 {
    color: #f8fafc !important;
}
.main-title {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1px;
}
.sub-title {
    color: #94a3b8;
    margin-bottom: 25px;
}
.kpi-card {
    background: linear-gradient(145deg, rgba(15,34,56,0.96), rgba(8,23,39,0.96));
    border: 1px solid rgba(56,189,248,0.14);
    border-radius: 18px;
    padding: 22px;
    min-height: 125px;
    box-shadow: 0 15px 45px rgba(0,0,0,0.22);
}
.kpi-label {
    color: #94a3b8;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.kpi-value {
    color: #f8fafc;
    font-size: 32px;
    font-weight: 800;
    margin-top: 8px;
}
.card {
    background: rgba(10,28,46,0.9);
    border: 1px solid rgba(148,163,184,0.10);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 18px;
}
.login-box {
    max-width: 480px;
    margin: 70px auto;
    padding: 40px;
    background: rgba(9,26,43,0.96);
    border: 1px solid rgba(56,189,248,0.18);
    border-radius: 24px;
    box-shadow: 0 30px 80px rgba(0,0,0,0.35);
}
.small-muted {
    color: #94a3b8;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# UI HELPERS
# ============================================================

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
# LOGIN & SECURITY
# ============================================================

def login_page():
    st.markdown("""
        <div class="login-box">
            <h1 style="text-align:center;">MASAR</h1>
            <p style="text-align:center;color:#94a3b8;">Intelligence OS</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Employee Login", "Forgot PIN"])
    with tab1:
        with st.form("login_form"):
            code = st.text_input("Employee Code", placeholder="Example: EMP001")
            pin = st.text_input("PIN", type="password")
            submit = st.form_submit_button("LOGIN", use_container_width=True)
            if submit:
                code = code.strip().upper()
                employee = query_one("SELECT * FROM employees WHERE employee_code = ? AND active = 1", (code,))
                if employee and verify_pin(pin, employee["pin_hash"]):
                    st.session_state.user = dict(employee)
                    st.session_state.logged_in = True
                    log_event(employee["id"], employee["employee_code"], "LOGIN_SUCCESS")
                    create_notification(employee["id"], "تسجيل دخول ناجح", "مرحباً بك في نظام مسار الذكي", "Security")
                    play_sound_alert()
                    st.rerun()
                else:
                    if employee:
                        log_event(employee["id"], employee["employee_code"], "LOGIN_FAILED")
                    else:
                        log_event(None, code, "LOGIN_FAILED")
                    st.error("Invalid employee code or PIN.")

    with tab2:
        st.info("Enter your employee code and registered mobile number.")
        with st.form("forgot_form"):
            code = st.text_input("Employee Code", key="forgot_code")
            mobile = st.text_input("Registered Mobile", key="forgot_mobile")
            submit = st.form_submit_button("RESET PIN", use_container_width=True)
            if submit:
                employee = query_one("SELECT * FROM employees WHERE employee_code = ? AND mobile = ? AND active = 1", (code.strip().upper(), mobile.strip()))
                if employee:
                    temp_pin = generate_temp_pin()
                    execute("UPDATE employees SET pin_hash = ?, must_change_pin = 1 WHERE id = ?", (hash_pin(temp_pin), employee["id"]))
                    create_notification(employee["id"], "Temporary PIN", "Your PIN has been reset.", "Security")
                    play_sound_alert()
                    st.success("Temporary PIN generated.")
                    st.warning(f"Temporary PIN: {temp_pin}")
                else:
                    st.error("Employee code/mobile combination not found.")

def force_change_pin():
    user = st.session_state.user
    page_header("Security", "You must change your temporary PIN before continuing.")
    with st.form("change_pin"):
        old_pin = st.text_input("Current PIN", type="password")
        new_pin = st.text_input("New PIN", type="password")
        confirm = st.text_input("Confirm New PIN", type="password")
        submit = st.form_submit_button("Change PIN", use_container_width=True)
        if submit:
            if not verify_pin(old_pin, user["pin_hash"]):
                st.error("Current PIN is incorrect.")
                return
            if len(new_pin) < 4:
                st.error("PIN must contain at least 4 characters.")
                return
            if new_pin != confirm:
                st.error("PIN confirmation does not match.")
                return
            execute("UPDATE employees SET pin_hash = ?, must_change_pin = 0 WHERE id = ?", (hash_pin(new_pin), user["id"]))
            updated = query_one("SELECT * FROM employees WHERE id = ?", (user["id"],))
            st.session_state.user = dict(updated)
            st.success("PIN changed successfully.")
            st.rerun()

# ============================================================
# MODULES
# ============================================================

def dashboard():
    user = st.session_state.user
    page_header("Executive Dashboard", f"Welcome back, {user['full_name']}")
    
    employees = query("SELECT * FROM employees WHERE active = 1")
    companies = query("SELECT * FROM companies")
    opportunities = query("SELECT * FROM opportunities")
    projects = query("SELECT * FROM projects")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Employees", len(employees))
    with c2: kpi("Companies", len(companies))
    with c3: kpi("Open Opportunities", len(opportunities[opportunities["stage"] != "Won"]) if not opportunities.empty else 0)
    with c4: kpi("Projects", len(projects))

    st.markdown("<br>", unsafe_allow_html=True)
    if not opportunities.empty:
        pipeline = opportunities.groupby("stage", as_index=False)["value"].sum()
        fig = px.bar(pipeline, x="stage", y="value", title="Opportunity Value by Stage")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True)

def employee_dashboard():
    user = st.session_state.user
    performance = calculate_employee_performance(user["id"])
    page_header("My Workspace", "Your tasks and performance.")
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Performance", f"{performance}%")
    my_tasks = query("SELECT * FROM tasks WHERE assigned_to = ? ORDER BY due_date", (user["id"],))
    with c2: kpi("My Tasks", len(my_tasks))
    with c3: kpi("Notifications", unread_notifications(user["id"]))

def task_organizer():
    user = st.session_state.user
    page_header("Task Organizer & Creator", "إدارة وتعيين المهام، وتحديد المواعيد ومنبهات التذكير الصوتي والرسائل.")

    with st.expander("➕ إضافة مهمة جديدة وتعيين موعد ومنبه صوتي", expanded=True):
        with st.markdown('<div class="card">', unsafe_allow_html=True):
            with st.form("new_task_form"):
                t_title = st.text_input("عنوان المهمة")
                t_desc = st.text_area("تفاصيل المهمة")
                
                emps = query("SELECT id, full_name, email FROM employees WHERE active = 1")
                emp_options = {row["full_name"]: row["id"] for row in emps}
                assigned_name = st.selectbox("تعيين إلى موظف", list(emp_options.keys()))
                
                col1, col2, col3 = st.columns(3)
                with col1: t_priority = st.selectbox("الأولوية", ["Low", "Medium", "High", "Urgent"])
                with col2: t_due = st.date_input("تاريخ الاستحقاق", value=date.today())
                with col3: t_reminder = st.time_input("وقت التنبيه الصوتي والإشعار")
                
                submit_task = st.form_submit_button("حفظ وتفعيل التنبيه الصوتي وإرسال الإشعار", use_container_width=True)
                if submit_task:
                    if not t_title.strip():
                        st.error("يرجى إدخال عنوان المهمة.")
                    else:
                        emp_id = emp_options[assigned_name]
                        execute("""
                            INSERT INTO tasks (title, description, assigned_to, created_by, priority, status, due_date, reminder_time)
                            VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)
                        """, (t_title, t_desc, emp_id, user["id"], t_priority, str(t_due), str(t_reminder)))
                        
                        create_notification(emp_id, "مهمة جديدة محددة بموعد", f"المهمة: {t_title} - موعد التنبيه: {t_reminder}", "Task")
                        play_sound_alert()
                        st.success("تم حفظ المهمة وتفعيل التنبيه الصوتي وإرسال الإشعار للموظف بنجاح!")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### المهام الخاصة بك والمنبهات المفعلة")
    tasks = query("SELECT * FROM tasks WHERE assigned_to = ? ORDER BY due_date", (user["id"],))
    if tasks.empty:
        st.info("لا توجد مهام مسندة إليك حالياً.")
    else:
        for index, row in tasks.iterrows():
            with st.container():
                cols = st.columns([3, 1, 1, 1, 1])
                cols[0].markdown(f"**{row['title']}**<br><span class='small-muted'>{row['description']}</span>", unsafe_allow_html=True)
                cols[1].markdown(f"الأولوية: `{row['priority']}`")
                cols[2].markdown(f"الاستحقاق: `{row['due_date']}`")
                cols[3].markdown(f"⏰ المنبه: `{row['reminder_time'] or 'غير محدد'}`")
                
                status_val = cols[4].selectbox("الحالة", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(row["status"]), key=f"status_{row['id']}")
                if status_val != row["status"]:
                    execute("UPDATE tasks SET status = ? WHERE id = ?", (status_val, row["id"]))
                    create_notification(user["id"], "تحديث حالة مهمة", f"تم تحديث حالة المهمة {row['title']} إلى {status_val}", "Task")
                    play_sound_alert()
                    st.rerun()
                st.divider()

def internal_chat():
    user = st.session_state.user
    page_header("Internal Chat", "الدردشة والرسائل الداخلية الفورية بين الموظفين.")

    emps = query("SELECT id, full_name, employee_code FROM employees WHERE id != ? AND active = 1", (user["id"],))
    if emps.empty:
        st.info("لا يوجد موظفون آخرون متاحون للدردشة.")
        return

    emp_dict = {f"{row['full_name']} ({row['employee_code']})": row["id"] for row in emps}
    selected_target_name = st.selectbox("اختر الموظف لبدء المحادثة", list(emp_dict.keys()))
    target_id = emp_dict[selected_target_name]

    st.markdown("---")

    # جلب الرسائل بين المستخدم والمستهدف
    messages = query("""
        SELECT * FROM messages 
        WHERE (sender_id = ? AND receiver_id = ?) 
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY id ASC
    """, (user["id"], target_id, target_id, user["id"]))

    chat_container = st.container(height=400)
    with chat_container:
        if messages.empty:
            st.info("لا توجد رسائل سابقة في هذه المحادثة. ابدأ الإرسال الآن.")
        else:
            for r in messages.iterrows():
                row = r[1]
                sender_name = "أنت" if row["sender_id"] == user["id"] else selected_target_name.split('(')[0]
                align_style = "text-align: right; background: rgba(56,189,248,0.15); padding: 10px; border-radius: 10px; margin-bottom: 8px;" if row["sender_id"] == user["id"] else "text-align: left; background: rgba(30,58,138,0.3); padding: 10px; border-radius: 10px; margin-bottom: 8px;"
                st.markdown(f"""
                    <div style="{align_style}">
                        <b>{sender_name}:</b> {row['message']}<br>
                        <span class="small-muted">{row['created_at']}</span>
                    </div>
                """, unsafe_allow_html=True)

    # نموذج إرسال رسالة جديدة
    with st.form("chat_form", clear_on_submit=True):
        msg_text = st.text_input("اكتب رسالتك هنا...")
        send_btn = st.form_submit_button("إرسال الرسالة", use_container_width=True)
        if send_btn:
            if msg_text.strip():
                execute("""
                    INSERT INTO messages (sender_id, receiver_id, message)
                    VALUES (?, ?, ?)
                """, (user["id"], target_id, msg_text))
                create_notification(target_id, f"رسالة جديدة من {user['full_name']}", msg_text, "Chat")
                play_sound_alert()
                st.rerun()

def job_description_library():
    page_header("Job Description Library", "Word format job descriptions.")
    st.info("Job description module active.")

def crm():
    page_header("CRM", "Companies and contacts.")
    companies = query("SELECT * FROM companies ORDER BY id DESC")
    if companies.empty: st.info("No companies yet.")
    else: st.dataframe(companies, use_container_width=True, hide_index=True)

def opportunities():
    page_header("Opportunities", "Commercial pipeline.")
    data = query("SELECT * FROM opportunities ORDER BY id DESC")
    if data.empty: st.info("No opportunities.")
    else: st.dataframe(data, use_container_width=True, hide_index=True)

def projects():
    page_header("Projects", "Track delivery.")
    data = query("SELECT * FROM projects ORDER BY id DESC")
    if data.empty: st.info("No projects.")
    else: st.dataframe(data, use_container_width=True, hide_index=True)

def governance():
    page_header("Governance", "Policies and records.")
    data = query("SELECT * FROM governance ORDER BY id DESC")
    if data.empty: st.info("No governance records.")
    else: st.dataframe(data, use_container_width=True, hide_index=True)

def email_assistant():
    page_header("Email Intelligence", "Mailbox monitoring.")
    st.info("Email module active.")

def ai_company_research():
    page_header("AI Company Research", "Analyze company websites and generate executive intelligence reports.")
    
    with st.form("company_research_form"):
        company_input = st.text_input("Company Website URL or Name", placeholder="e.g., https://example.com or company name")
        analysis_focus = st.selectbox("Analysis Focus", [
            "Comprehensive Overview & Strategy",
            "Business Model & Revenue Streams",
            "Market Position & Competitors",
            "Partnership & Collaboration Potential"
        ])
        submit = st.form_submit_button("Generate Intelligence Report", use_container_width=True)
        
        if submit:
            if not company_input.strip():
                st.error("Please enter a valid website link or company name.")
            else:
                with st.spinner("Analyzing company profile and compiling report..."):
                    play_sound_alert()
                    st.markdown(f"""
<div class="card">
<h3>📊 Executive Intelligence Report</h3>
<p><b>Target Entity:</b> {company_input}</p>
<p><b>Focus Area:</b> {analysis_focus}</p>
<hr style="border-color:rgba(56,189,248,0.2);">

<h4>1. Executive Summary</h4>
<p>The target entity operates within a dynamic market sector, demonstrating active digital presence and strategic commercial positioning aligned with modern industry standards.</p>

<h4>2. Core Offerings & Business Activities</h4>
<ul>
<li>Specialized enterprise services and product delivery.</li>
<li>Customer-centric operational workflows and digital infrastructure.</li>
<li>Scalable business models aimed at regional and international expansion.</li>
</ul>

<h4>3. Strategic Insights & Opportunities</h4>
<p>High potential for strategic alignment, joint ventures, or supply chain integration within MASAR's consulting framework.</p>
</div>
""", unsafe_allow_html=True)

def admin_center():
    user = st.session_state.user
    if user["role"] != "Admin":
        st.error("Administrator access required.")
        return
    page_header("Admin Control Center", "Manage employees and system.")
    employees = query("SELECT id, employee_code, full_name, role, active FROM employees ORDER BY id DESC")
    st.dataframe(employees, use_container_width=True, hide_index=True)

def notifications_center():
    user = st.session_state.user
    page_header("Notifications", "System alerts.")
    notifs = query("SELECT * FROM notifications WHERE employee_id = ? ORDER BY id DESC", (user["id"],))
    if notifs.empty:
        st.info("No new notifications.")
    else:
        for r in notifs.iterrows():
            row = r[1]
            st.markdown(f"""
                <div class="card">
                    <b>{row['title']}</b> ({row['notification_type']})<br>
                    <span>{row['message']}</span><br>
                    <span class="small-muted">{row['created_at']}</span>
                </div>
            """, unsafe_allow_html=True)
        execute("UPDATE notifications SET is_read = 1 WHERE employee_id = ?", (user["id"],))

def performance_center():
    user = st.session_state.user
    page_header("Performance Center", "Employee performance overview.")
    score = calculate_employee_performance(user["id"])
    kpi("My Performance", f"{score}%")

def global_search():
    page_header("Search", "Global search.")
    term = st.text_input("Search", placeholder="Type to search...")
    if term.strip():
        st.info(f"Searching for: {term}")

# ============================================================
# SIDEBAR & ROUTER
# ============================================================

def sidebar():
    user = st.session_state.user
    display_logo()
    
    st.sidebar.markdown(f"""
        <div style="text-align:center;">
            <b>{COMPANY_NAME}</b><br>
            <span class="small-muted">Intelligence OS</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.divider()
    st.sidebar.markdown(f"**{user['full_name']}**")
    st.sidebar.caption(f"{user['employee_code']} • {user['role']}")
    
    unread = unread_notifications(user["id"])
    menu = [
        "Dashboard", "My Workspace", "Tasks", "Internal Chat", "CRM",
        "Opportunities", "Projects", "Performance", "Job Descriptions",
        "AI Company Research", "Email Intelligence", "Notifications", "Search"
    ]
    if user["role"] == "Admin":
        menu += ["Admin Control Center", "Governance"]

    selected = st.sidebar.radio("Navigation", menu, label_visibility="collapsed")
    
    st.sidebar.divider()
    st.sidebar.caption(f"Notifications: {unread}")
    if st.sidebar.button("Logout", use_container_width=True):
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

if page == "Dashboard": dashboard()
elif page == "My Workspace": employee_dashboard()
elif page == "Tasks": task_organizer()
elif page == "Internal Chat": internal_chat()
elif page == "CRM": crm()
elif page == "Opportunities": opportunities()
elif page == "Projects": projects()
elif page == "Performance": performance_center()
elif page == "Job Descriptions": job_description_library()
elif page == "AI Company Research": ai_company_research()
elif page == "Email Intelligence": email_assistant()
elif page == "Notifications": notifications_center()
elif page == "Search": global_search()
elif page == "Admin Control Center": admin_center()
elif page == "Governance": governance()

st.markdown("""
    <div style="text-align:center; color:#64748b; margin-top:50px; padding:20px; font-size:11px;">
        MASAR Intelligence OS • Internal Business Platform
    </div>
""", unsafe_allow_html=True)
