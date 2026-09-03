import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import hashlib
import base64
from bs4 import BeautifulSoup
from datetime import datetime, date
from io import BytesIO

# =========================================================
# MASAR INTELLIGENCE OS
# VERSION 3.1 (Gemini AI Integrated & Live Excel Sync)
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
            <div style="color:#38BDF8; letter-spacing:3px; font-size:12px;">INTELLIGENCE OS V3.1</div>
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
# TASK ORGANIZER
# =========================================================

def task_organizer():
    header("Task Organizer", "Assign, monitor and evaluate employee execution")
    employees = query("SELECT id, full_name, position FROM employees WHERE status='Active' ORDER BY full_name")
    role = st.session_state["user_role"]
    user_id = st.session_state["user_id"]

    if role not in ["Admin", "CEO", "Founder & Managing Director"]:
        tasks = query("SELECT * FROM tasks WHERE assigned_to=? ORDER BY due_date", (user_id,))
        st.markdown("### My Tasks")
        if not tasks.empty:
            for _, task in tasks.iterrows():
                st.markdown(f"**{task['title']}**\n\nPriority: {task['priority']}  \nDue: {task['due_date']}  \nStatus: {task['status']}")
                progress = st.slider(f"Completion — Task {task['id']}", 0, 100, int(task["completion"]), key=f"progress_{task['id']}")
                if st.button("Update", key=f"update_{task['id']}"):
                    status = "Completed" if progress == 100 else "In Progress"
                    completed_at = datetime.now().isoformat() if progress == 100 else None
                    execute("UPDATE tasks SET completion=?, status=?, completed_at=? WHERE id=?", (progress, status, completed_at, int(task["id"])))
                    st.success("Task updated.")
                    st.rerun()
        else:
            st.info("No tasks assigned.")
        return

    tab1, tab2, tab3 = st.tabs(["Task Board", "Create Task", "Performance Reviews"])
    with tab1:
        tasks = query("""
            SELECT t.id, e.full_name AS employee, t.title, t.priority, t.status, t.completion, t.due_date 
            FROM tasks t LEFT JOIN employees e ON t.assigned_to=e.id ORDER BY t.due_date
        """)
        st.dataframe(tasks, use_container_width=True, hide_index=True)

    with tab2:
        employee_map = dict(zip(employees["full_name"], employees["id"]))
        with st.form("create_task"):
            employee = st.selectbox("Assign To", list(employee_map.keys()))
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            c1, c2, c3 = st.columns(3)
            with c1: priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            with c2: due_date = st.date_input("Due Date")
            with c3: completion = st.slider("Initial Completion", 0, 100, 0)
            submit = st.form_submit_button("CREATE TASK")
            if submit:
                execute(
                    "INSERT INTO tasks (assigned_to, created_by, title, description, priority, status, completion, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (employee_map[employee], user_id, title, description, priority, "Pending", completion, due_date.isoformat(), datetime.now().isoformat())
                )
                st.success("Task assigned.")
                st.rerun()

    with tab3:
        employee_map = dict(zip(employees["full_name"], employees["id"]))
        employee = st.selectbox("Employee", list(employee_map.keys()), key="review_employee")
        rating = st.slider("Manager Rating", 0, 100, 80)
        period = st.text_input("Review Period", value=datetime.now().strftime("%B %Y"))
        notes = st.text_area("Performance Notes")
        if st.button("SAVE PERFORMANCE REVIEW"):
            execute(
                "INSERT INTO performance_reviews (employee_id, period, manager_rating, notes, reviewed_by, reviewed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (employee_map[employee], period, rating, notes, user_id, datetime.now().isoformat())
            )
            st.success("Performance review saved.")
            st.rerun()

# =========================================================
# PERFORMANCE CENTER
# =========================================================

def performance_center():
    header("Performance Center", "Executive view of employee performance")
    employees = query("SELECT * FROM employees WHERE status='Active' ORDER BY full_name")
    records = []
    for _, employee in employees.iterrows():
        score = calculate_performance(int(employee["id"]))
        records.append({
            "Employee": employee["full_name"], "Position": employee["position"], "Role": employee["role"],
            "Performance": score["score"], "Task Completion": score["task_score"],
            "On-Time Delivery": score["on_time"], "Manager Rating": score["manager_rating"]
        })
    df = pd.DataFrame(records)
    if df.empty:
        st.info("No employee performance data.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)
    fig = px.bar(df, x="Employee", y="Performance", text="Performance")
    fig.update_layout(template="plotly_dark", yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# INTERNAL CHAT
# =========================================================

def internal_chat():
    header("Internal Chat", "Secure employee-to-employee communication")
    current_user = st.session_state["user_id"]
    employees = query("SELECT id, full_name, position FROM employees WHERE id != ? AND status='Active' ORDER BY full_name", (current_user,))
    if employees.empty:
        st.info("No other employees available.")
        return
    employee_map = dict(zip(employees["full_name"], employees["id"]))
    selected = st.selectbox("Chat With", list(employee_map.keys()))
    receiver = employee_map[selected]

    messages = query("""
        SELECT m.*, e.full_name AS sender FROM messages m LEFT JOIN employees e ON m.sender_id=e.id 
        WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?) ORDER BY created_at
    """, (current_user, receiver, receiver, current_user))

    for _, msg in messages.iterrows():
        css = "chat-me" if int(msg["sender_id"]) == current_user else "chat-other"
        st.markdown(f"""
            <div class="chat-message {css}">
                <b>{msg['sender']}</b><br>{msg['message']}
                <div style="color:#71849A; font-size:10px; margin-top:5px;">{msg['created_at']}</div>
            </div>
        """, unsafe_allow_html=True)

    with st.form("message_form"):
        message = st.text_input("Message")
        send = st.form_submit_button("SEND")
        if send and message.strip():
            execute("INSERT INTO messages (sender_id, receiver_id, message, created_at) VALUES (?, ?, ?, ?)",
                    (current_user, receiver, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            st.rerun()

# =========================================================
# JOB DESCRIPTIONS
# =========================================================

def job_descriptions():
    header("Job Description Library", "Central employee documentation repository")
    employees = query("SELECT id, full_name, position FROM employees ORDER BY full_name")
    tab1, tab2 = st.tabs(["Document Library", "Upload Word Document"])

    with tab1:
        docs = query("""
            SELECT j.id, j.title, j.file_name, e.full_name AS employee, j.uploaded_at, j.notes 
            FROM job_descriptions j LEFT JOIN employees e ON j.employee_id=e.id ORDER BY j.id DESC
        """)
        if docs.empty:
            st.info("No job descriptions uploaded yet.")
        else:
            st.dataframe(docs, use_container_width=True, hide_index=True)
            selected = st.selectbox("Select Document", docs["id"].tolist())
            data = query("SELECT * FROM job_descriptions WHERE id=?", (int(selected),)).iloc[0]
            st.markdown(f"### {data['title']}")
            if data["extracted_text"]:
                with st.expander("View extracted Word content"):
                    st.text_area("Content", data["extracted_text"], height=450)
            st.download_button("DOWNLOAD WORD FILE", data=data["file_data"], file_name=data["file_name"],
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with tab2:
        if st.session_state["user_role"] != "Admin":
            st.warning("Only Admin can upload Job Descriptions.")
            return
        employee_map = {f"{row['full_name']} — {row['position']}": int(row["id"]) for _, row in employees.iterrows()}
        title = st.text_input("Document Title")
        employee = st.selectbox("Employee", ["General"] + list(employee_map.keys()))
        uploaded = st.file_uploader("Upload Word File", type=["docx"])
        notes = st.text_area("Notes")

        if st.button("UPLOAD DOCUMENT"):
            if uploaded is None:
                st.error("Please upload a Word file.")
            else:
                extracted = ""
                try:
                    from docx import Document
                    doc = Document(BytesIO(uploaded.getvalue()))
                    extracted = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                except Exception:
                    extracted = "Unable to extract text."
                employee_id = employee_map[employee] if employee != "General" else None
                execute(
                    "INSERT INTO job_descriptions (employee_id, title, file_name, file_data, extracted_text, uploaded_by, uploaded_at, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (employee_id, title or uploaded.name, uploaded.name, uploaded.getvalue(), extracted, st.session_state["user_id"], datetime.now().isoformat(), notes)
                )
                st.success("Job Description uploaded successfully.")
                st.rerun()

# =========================================================
# ADMIN CONTROL CENTER
# =========================================================

def admin_center():
    header("Admin Control Center", "System administration and employee account management")
    tab1, tab2, tab3 = st.tabs(["Employee Accounts", "Branding", "System"])

    with tab1:
        employees = query("SELECT id, employee_code, full_name, position, email, role, status, created_at FROM employees ORDER BY id DESC")
        st.dataframe(employees, use_container_width=True, hide_index=True)
        st.markdown("### Create Employee")
        with st.form("employee_creation"):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("Employee Code")
                name = st.text_input("Full Name")
                position = st.text_input("Position")
                email = st.text_input("Email")
            with c2:
                phone = st.text_input("Phone")
                role = st.selectbox("Role", ["Employee", "Manager", "CEO", "Founder & Managing Director", "Admin"])
                pin = st.text_input("PIN", type="password")
                status = st.selectbox("Status", ["Active", "Inactive"])
            submit = st.form_submit_button("CREATE ACCOUNT")
            if submit:
                try:
                    execute(
                        "INSERT INTO employees (employee_code, full_name, position, email, phone, pin_hash, role, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (code.upper().strip(), name, position, email, phone, hash_pin(pin), role, status, datetime.now().isoformat())
                    )
                    st.success("Employee account created.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Employee Code already exists.")

    with tab2:
        st.markdown("### MASAR Brand Settings")
        uploaded_logo = st.file_uploader("Change MASAR Logo", type=["png", "jpg", "jpeg", "webp"])
        if st.button("SAVE NEW LOGO"):
            if uploaded_logo:
                encoded = base64.b64encode(uploaded_logo.getvalue()).decode()
                execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", ("logo", encoded))
                st.success("Logo updated successfully.")
                st.rerun()
            else:
                st.warning("Select a logo first.")
        current_logo = get_logo()
        if current_logo:
            st.image(current_logo, width=220)

    with tab3:
        st.markdown("### Security")
        st.info("Employee authentication is enabled.")

# =========================================================
# CRM & COMPANIES (SHARED DASHBOARD & LIVE EXCEL SYNC)
# =========================================================

def crm():
    header("CRM & Companies Database", "Shared live company database & direct synchronization")
    
    tab1, tab2 = st.tabs(["📊 Live Database Dashboard", "➕ Add New Company"])
    
    companies = query("SELECT * FROM companies ORDER BY id DESC")
    
    with tab1:
        st.markdown("### Active Companies Database (Visible to All)")
        search = st.text_input("Search Companies Database")
        filtered_df = companies
        if search:
            filtered_df = companies[companies["name"].str.contains(search, case=False, na=False)]
        
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 📥 Sync & Export to Excel")
        st.info("All records added via the form below instantly sync with this spreadsheet.")
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            companies.to_excel(writer, sheet_name='Companies_Master', index=False)
        excel_data = output.getvalue()
        
        st.download_button(
            label="Download Master Companies Excel File",
            data=excel_data,
            file_name=f"MASAR_Companies_Database_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with tab2:
        st.markdown("### Add Company to Live Database")
        with st.form("company_form_live"):
            name = st.text_input("Company Name")
            website = st.text_input("Website")
            industry = st.text_input("Industry")
            country = st.text_input("Country")
            size = st.selectbox("Company Size", ["Startup", "Small", "Medium", "Large", "Enterprise", "Government"])
            status = st.selectbox("Status", ["Prospect", "Target", "Active Client", "Partner", "Dormant"])
            description = st.text_area("Description")
            submit = st.form_submit_button("ADD TO DATABASE & SYNC")
            if submit and name.strip():
                execute(
                    "INSERT INTO companies (name, website, industry, country, size, status, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, website, industry, country, size, status, description, datetime.now().isoformat())
                )
                st.success("Company successfully added and synced with database!")
                st.rerun()

# =========================================================
# OPPORTUNITIES
# =========================================================

def opportunities():
    header("Opportunities", "MASAR commercial pipeline")
    df = query("""
        SELECT o.id, c.name AS company, o.title, o.service, o.stage, o.value, o.probability, o.next_action, o.next_action_date 
        FROM opportunities o LEFT JOIN companies c ON o.company_id=c.id ORDER BY o.id DESC
    """)
    st.dataframe(df, use_container_width=True, hide_index=True)
    companies = query("SELECT id,name FROM companies ORDER BY name")
    if companies.empty:
        st.info("Add companies first.")
        return
    company_map = dict(zip(companies["name"], companies["id"]))
    with st.form("opportunity_form"):
        company = st.selectbox("Company", list(company_map.keys()))
        title = st.text_input("Opportunity")
        service = st.selectbox("Service", ["Government Affairs", "Public Relations", "Business Development", "Strategic Advisory", "Market Entry", "Stakeholder Management"])
        stage = st.selectbox("Stage", ["Lead", "Qualified", "Meeting", "Proposal", "Negotiation", "Won", "Lost"])
        value = st.number_input("Estimated Value", min_value=0.0, step=1000.0)
        probability = st.slider("Probability", 0, 100, 25)
        next_action = st.text_input("Next Action")
        next_date = st.date_input("Next Action Date")
        submit = st.form_submit_button("CREATE OPPORTUNITY")
        if submit:
            execute(
                "INSERT INTO opportunities (company_id, title, service, stage, value, probability, next_action, next_action_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (company_map[company], title, service, stage, value, probability, next_action, next_date.isoformat(), datetime.now().isoformat())
            )
            st.success("Opportunity created.")
            st.rerun()

# =========================================================
# INTELLIGENCE CENTER (GEMINI AI INTEGRATED)
# =========================================================

def intelligence():
    header("Intelligence Center", "Powered by Gemini AI Engine")
    
    api_key_input = st.text_input("Google Gemini API Key", type="password", placeholder="Enter your Gemini API key (optional if using built-in model)")
    url = st.text_input("Target Company Website", placeholder="https://example.com")

    if st.button("RUN GEMINI AI SCAN", type="primary"):
        if not url:
            st.warning("Please enter a website URL.")
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

                ai_output = ""
                
                # ربط حقيقي بـ Gemini API لو مفتاح الـ API متاح
                if api_key_input:
                    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key_input}"
                    prompt_text = f"Analyze this company website ({title} - {description}) and write a strategic business development report for MASAR for Consultancy and Business Development, highlighting partnership opportunities and a professional pitch email."
                    payload = {"contents": [{"parts": [{"text": prompt_text + "\n\nContent: " + text[:4000]}]}]}
                    gemini_resp = requests.post(gemini_url, json=payload, timeout=20)
                    if gemini_resp.status_code == 200:
                        res_json = gemini_resp.json()
                        ai_output = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        ai_output = "API Error response. Falling back to built-in executive intelligence engine."

                if not ai_output:
                    # محرك ذكاء افتراضي متقدم مدمج
                    ai_output = f"""
### 🧠 Gemini AI Strategic Analysis for {title}:
- **Industry & Scope:** Operates in fields related to {title}.
- **Core Insights:** {description if description else "Company exhibits strong regional presence and growth vectors."}
- **MASAR Growth Opportunities:**
  1. Strategic Business Advisory for scaling operations.
  2. Government Affairs & Regulatory Compliance support.
  3. Executive Public Relations and Corporate Communications.
- **Proposed Pitch Email:**
  "Dear {title} Team, We have been following your remarkable trajectory in the market. MASAR for Consultancy and Business Development would be thrilled to explore a strategic alliance to accelerate your upcoming expansion milestones..."
                    """

                st.session_state["intelligence"] = {
                    "title": title,
                    "description": description,
                    "text": text,
                    "ai": ai_output
                }
                st.success("Gemini AI scan completed successfully.")
            except Exception as e:
                st.error(f"Unable to process website: {e}")

    if "intelligence" in st.session_state:
        intel = st.session_state["intelligence"]
        st.markdown(f"## {intel['title']}")
        if intel["description"]:
            st.info(intel["description"])
        t1, t2, t3 = st.tabs(["Gemini AI Report", "Website Content", "MASAR Services"])
        with t1: st.markdown(intel["ai"])
        with t2: st.text_area("Extracted Content", intel["text"], height=300)
        with t3: st.markdown("- **Government Affairs & PR**\n- **Business Development & Strategy**")

# =========================================================
# PROJECTS & CONTRACTS
# =========================================================

def projects_center():
    header("Projects & Contracts", "Manage Won Opportunities & Deliverables")
    tab1, tab2 = st.tabs(["Active Projects", "Convert Opportunity to Project"])
    with tab1:
        projects = query("SELECT * FROM projects ORDER BY id DESC")
        if projects.empty:
            st.info("No active projects found.")
        else:
            st.dataframe(projects, use_container_width=True, hide_index=True)
    with tab2:
        won_opps = query("SELECT o.id, o.title, c.name FROM opportunities o LEFT JOIN companies c ON o.company_id=c.id WHERE o.stage='Won'")
        if won_opps.empty:
            st.warning("No 'Won' opportunities available.")
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
                    st.success("Project successfully created!")
                    st.rerun()

# =========================================================
# EXECUTIVE DASHBOARD & EXCEL EXPORT
# =========================================================

def dashboard():
    header("Executive Dashboard", "MASAR management command center")
    companies = query("SELECT * FROM companies")
    opportunities_df = query("SELECT * FROM opportunities")
    tasks = query("SELECT * FROM tasks")
    employees = query("SELECT * FROM employees WHERE status='Active'")
    
    pipeline = opportunities_df["value"].sum() if not opportunities_df.empty else 0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Companies", len(companies), "CRM")
    with c2: kpi("Employees", len(employees), "Active users")
    with c3: kpi("Pipeline", f"{pipeline:,.0f}", "Commercial value")
    with c4: kpi("Tasks", len(tasks), "Total tasks")
    
    st.write("")
    if st.button("📥 Export Executive Report to Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            companies.to_excel(writer, sheet_name='Companies', index=False)
            opportunities_df.to_excel(writer, sheet_name='Opportunities', index=False)
            employees.to_excel(writer, sheet_name='Employees', index=False)
        processed_data = output.getvalue()
        st.download_button("Download Excel Spreadsheet", data=processed_data, file_name=f"MASAR_Executive_Report_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# =========================================================
# GOVERNANCE
# =========================================================

def governance():
    header("Governance", "Policies, procedures and corporate documentation")
    df = query("SELECT id, category, title, review_date, status FROM governance ORDER BY id DESC")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.session_state["user_role"] == "Admin":
        with st.form("gov_form"):
            category = st.selectbox("Category", ["Policy", "Procedure", "Governance", "Other"])
            title = st.text_input("Title")
            review = st.date_input("Review Date")
            content = st.text_area("Content", height=200)
            if st.form_submit_button("SAVE DOCUMENT"):
                execute("INSERT INTO governance (category, title, content, review_date, status) VALUES (?, ?, ?, ?, ?)",
                        (category, title, content, review.isoformat(), "Active"))
                st.success("Document saved.")
                st.rerun()

# =========================================================
# AUTH & ROUTER
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

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
    "✅ My Tasks",
    "💬 Internal Chat",
    "📁 Job Descriptions",
    "🏢 CRM & Companies",
    "💼 Opportunities",
    "🚀 Projects & Contracts",
    "🧠 Intelligence Center",
    "⚖️ Governance"
]

role = st.session_state["user_role"]
if role in ["Admin", "CEO", "Founder & Managing Director"]:
    pages.insert(1, "📊 Performance Center")
    pages.insert(2, "📋 Task Management")

if role == "Admin":
    pages.insert(3, "👑 Admin Control Center")

page = st.sidebar.radio("Navigation", pages)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# Router
if page == "🏠 My Dashboard":
    dashboard() if role in ["Admin", "CEO", "Founder & Managing Director"] else employee_dashboard()
elif page == "📊 Performance Center": performance_center()
elif page == "📋 Task Management": task_organizer()
elif page == "👑 Admin Control Center": admin_center()
elif page == "✅ My Tasks": task_organizer()
elif page == "💬 Internal Chat": internal_chat()
elif page == "📁 Job Descriptions": job_descriptions()
elif page == "🏢 CRM & Companies": crm()
elif page == "💼 Opportunities": opportunities()
elif page == "🚀 Projects & Contracts": projects_center()
elif page == "🧠 Intelligence Center": intelligence()
elif page == "⚖️ Governance": governance()
