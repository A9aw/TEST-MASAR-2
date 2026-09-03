import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import hashlib
import base64
import secrets
import string
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from datetime import datetime, date
from io import BytesIO
from html import unescape


# =========================================================
# MASAR INTELLIGENCE OS
# VERSION 4.0
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


def generate_temp_pin(length=6):
    chars = string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db()
    cur = conn.cursor()

    # -------------------------
    # Employees
    # -------------------------

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
        must_change_pin INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # Migration for old databases
    try:
        cur.execute(
            "ALTER TABLE employees ADD COLUMN must_change_pin INTEGER DEFAULT 0"
        )
    except:
        pass

    # -------------------------
    # Messages
    # -------------------------

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

    # -------------------------
    # Tasks
    # -------------------------

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

    # -------------------------
    # Performance
    # -------------------------

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

    # -------------------------
    # Job Descriptions
    # -------------------------

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

    # -------------------------
    # Settings
    # -------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # -------------------------
    # Companies
    # -------------------------

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

    # -------------------------
    # Opportunities
    # -------------------------

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

    # -------------------------
    # Projects
    # -------------------------

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

    # -------------------------
    # Governance
    # -------------------------

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

    # =====================================================
    # NEW V4 TABLES
    # =====================================================

    # Login audit
    cur.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        employee_code TEXT,
        full_name TEXT,
        login_time TEXT,
        success INTEGER DEFAULT 1,
        ip_address TEXT,
        device TEXT
    )
    """)

    # Notifications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        title TEXT,
        message TEXT,
        notification_type TEXT DEFAULT 'Info',
        created_at TEXT,
        is_read INTEGER DEFAULT 0
    )
    """)

    # Emails
    cur.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_uid TEXT UNIQUE,
        sender TEXT,
        recipient TEXT,
        subject TEXT,
        email_date TEXT,
        body TEXT,
        summary TEXT,
        priority TEXT DEFAULT 'Normal',
        category TEXT DEFAULT 'General',
        action_required INTEGER DEFAULT 0,
        ai_processed INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

    # =====================================================
    # CREATE DEFAULT ADMIN
    # =====================================================

    admins = query(
        "SELECT id FROM employees WHERE role='Admin'"
    )

    if admins.empty:
        execute(
            """
            INSERT INTO employees
            (
                employee_code,
                full_name,
                position,
                email,
                phone,
                pin_hash,
                role,
                status,
                must_change_pin,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ADMIN",
                "MASAR Administrator",
                "System Administrator",
                "",
                "",
                hash_pin("1234"),
                "Admin",
                "Active",
                0,
                datetime.now().isoformat()
            )
        )


init_db()


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(56,189,248,.07),
            transparent 25%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(30,58,138,.14),
            transparent 25%
        ),
        #0B1220;
}

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #07111F 0%,
            #0B1E36 100%
        );
    border-right:
        1px solid rgba(56,189,248,.15);
}

section[data-testid="stSidebar"] * {
    color:#E5EEF8;
}

h1,h2,h3 {
    color:#F5F9FF !important;
}

p,label {
    color:#B7C5D6 !important;
}

.header {
    padding:20px 0 25px;
}

.title {
    font-size:34px;
    font-weight:850;
    color:white;
}

.subtitle {
    color:#38BDF8;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:2px;
}

.kpi {
    background:
        linear-gradient(
            145deg,
            rgba(20,36,58,.96),
            rgba(10,25,43,.96)
        );
    border:
        1px solid rgba(56,189,248,.13);
    border-radius:18px;
    padding:20px;
    min-height:125px;
}

.kpi-label {
    color:#8FA6BF;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:1px;
}

.kpi-value {
    color:white;
    font-size:31px;
    font-weight:850;
    margin-top:8px;
}

.kpi-note {
    color:#38BDF8;
    font-size:12px;
}

.profile {
    background:
        linear-gradient(
            145deg,
            #10243D,
            #0B1E36
        );
    border:
        1px solid rgba(56,189,248,.13);
    border-radius:18px;
    padding:18px;
}

.chat-message {
    padding:14px;
    margin:8px 0;
    border-radius:15px;
    background:#10243A;
}

.chat-me {
    border-left:3px solid #38BDF8;
}

.chat-other {
    border-left:3px solid #64748B;
}

.performance {
    background:
        linear-gradient(
            145deg,
            #10243D,
            #0B1E36
        );
    border-radius:20px;
    padding:25px;
    text-align:center;
    border:
        1px solid rgba(56,189,248,.15);
}

.score {
    font-size:58px;
    font-weight:900;
    color:#38BDF8;
}

.email-card {
    background:
        linear-gradient(
            145deg,
            #10243D,
            #0B1E36
        );
    border:
        1px solid rgba(56,189,248,.13);
    border-radius:18px;
    padding:20px;
    margin-bottom:12px;
}

.notification {
    background:#10243A;
    border-radius:14px;
    padding:15px;
    margin:8px 0;
}

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
            <div style="color:#8295AA;">
                {subtitle}
            </div>
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

    row = query(
        "SELECT value FROM settings WHERE key='logo'"
    )

    if row.empty:
        return None

    try:
        return base64.b64decode(
            row.iloc[0]["value"]
        )
    except:
        return None


def display_logo():

    logo = get_logo()

    if logo:
        st.sidebar.image(
            logo,
            width=150
        )

    else:

        st.sidebar.markdown(
            """
            <div class="masar-logo">
                ◈ MASAR
            </div>
            <div class="masar-tag">
                INTELLIGENCE OS
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# NOTIFICATIONS
# =========================================================

def create_notification(
    employee_id,
    title,
    message,
    notification_type="Info"
):

    execute(
        """
        INSERT INTO notifications
        (
            employee_id,
            title,
            message,
            notification_type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            employee_id,
            title,
            message,
            notification_type,
            datetime.now().isoformat()
        )
    )


def notification_center():

    header(
        "Notifications",
        "Your latest MASAR activity"
    )

    user_id = st.session_state["user_id"]

    notifications = query(
        """
        SELECT *
        FROM notifications
        WHERE employee_id=?
        ORDER BY id DESC
        LIMIT 50
        """,
        (user_id,)
    )

    if notifications.empty:
        st.info("No notifications.")
        return

    for _, n in notifications.iterrows():

        st.markdown(
            f"""
            <div class="notification">
                <b>{n['title']}</b><br>
                {n['message']}
                <br>
                <small style="color:#71849A;">
                    {n['created_at']}
                </small>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button("MARK ALL AS READ"):

        execute(
            """
            UPDATE notifications
            SET is_read=1
            WHERE employee_id=?
            """,
            (user_id,)
        )

        st.success("Notifications marked as read.")
        st.rerun()


# =========================================================
# LOGIN AUDIT
# =========================================================

def log_login(
    employee_id,
    employee_code,
    full_name,
    success=1
):

    execute(
        """
        INSERT INTO login_logs
        (
            employee_id,
            employee_code,
            full_name,
            login_time,
            success,
            device
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            employee_id,
            employee_code,
            full_name,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            success,
            "Web Browser"
        )
    )


# =========================================================
# LOGIN
# =========================================================

def login():

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:90px;
        ">
            <div style="
                font-size:65px;
                font-weight:900;
                color:white;
            ">
                ◈
            </div>

            <div style="
                font-size:38px;
                font-weight:900;
                color:white;
            ">
                MASAR
            </div>

            <div style="
                color:#38BDF8;
                letter-spacing:3px;
                font-size:12px;
            ">
                INTELLIGENCE OS V4.0
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with center:

        st.markdown(
            "### Secure Employee Login"
        )

        with st.form("login_form"):

            code = st.text_input(
                "Employee Code"
            )

            pin = st.text_input(
                "PIN",
                type="password"
            )

            submit = st.form_submit_button(
                "SIGN IN",
                use_container_width=True
            )

            if submit:

                users = query(
                    """
                    SELECT *
                    FROM employees
                    WHERE employee_code=?
                    AND status='Active'
                    """,
                    (
                        code.upper().strip(),
                    )
                )

                if users.empty:

                    st.error(
                        "Invalid employee code."
                    )

                else:

                    user = users.iloc[0]

                    if verify_pin(
                        pin,
                        user["pin_hash"]
                    ):

                        log_login(
                            int(user["id"]),
                            user["employee_code"],
                            user["full_name"],
                            1
                        )

                        st.session_state[
                            "authenticated"
                        ] = True

                        st.session_state[
                            "user_id"
                        ] = int(user["id"])

                        st.session_state[
                            "user_name"
                        ] = user["full_name"]

                        st.session_state[
                            "user_role"
                        ] = user["role"]

                        st.session_state[
                            "employee_code"
                        ] = user["employee_code"]

                        st.session_state[
                            "must_change_pin"
                        ] = int(
                            user["must_change_pin"]
                        )

                        st.rerun()

                    else:

                        log_login(
                            int(user["id"]),
                            user["employee_code"],
                            user["full_name"],
                            0
                        )

                        st.error(
                            "Invalid PIN."
                        )

        st.markdown("---")

        if st.button(
            "🔐 Forgot Password?",
            use_container_width=True
        ):

            st.session_state[
                "forgot_password"
            ] = True

    if st.session_state.get(
        "forgot_password",
        False
    ):

        forgot_password()


# =========================================================
# FORGOT PASSWORD
# =========================================================

def forgot_password():

    st.markdown(
        "## Password Recovery"
    )

    st.info(
        "Enter your registered mobile number. "
        "A temporary PIN will be generated."
    )

    phone = st.text_input(
        "Registered Mobile Number",
        key="reset_phone"
    )

    if st.button(
        "GENERATE TEMPORARY PIN"
    ):

        users = query(
            """
            SELECT *
            FROM employees
            WHERE phone=?
            AND status='Active'
            """,
            (phone.strip(),)
        )

        if users.empty:

            st.error(
                "No active employee account is linked to this mobile number."
            )

        else:

            user = users.iloc[0]

            temp_pin = generate_temp_pin()

            execute(
                """
                UPDATE employees
                SET pin_hash=?,
                    must_change_pin=1
                WHERE id=?
                """,
                (
                    hash_pin(temp_pin),
                    int(user["id"])
                )
            )

            create_notification(
                int(user["id"]),
                "PIN Reset",
                "Your account PIN has been reset. Please change it after login.",
                "Security"
            )

            st.success(
                "A temporary PIN has been generated."
            )

            st.warning(
                f"Temporary PIN: {temp_pin}"
            )

            st.caption(
                "For production SMS delivery, connect an SMS provider such as Twilio."
            )


# =========================================================
# CHANGE PIN
# =========================================================

def change_pin():

    header(
        "Change PIN",
        "Update your account security credentials"
    )

    with st.form(
        "change_pin_form"
    ):

        new_pin = st.text_input(
            "New PIN",
            type="password"
        )

        confirm_pin = st.text_input(
            "Confirm New PIN",
            type="password"
        )

        submit = st.form_submit_button(
            "UPDATE PIN"
        )

        if submit:

            if len(new_pin) < 4:

                st.error(
                    "PIN must contain at least 4 characters."
                )

            elif new_pin != confirm_pin:

                st.error(
                    "PIN confirmation does not match."
                )

            else:

                execute(
                    """
                    UPDATE employees
                    SET pin_hash=?,
                        must_change_pin=0
                    WHERE id=?
                    """,
                    (
                        hash_pin(new_pin),
                        st.session_state[
                            "user_id"
                        ]
                    )
                )

                st.session_state[
                    "must_change_pin"
                ] = 0

                st.success(
                    "PIN updated successfully."
                )

                st.rerun()


# =========================================================
# PERFORMANCE ENGINE
# =========================================================

def calculate_performance(
    employee_id
):

    tasks = query(
        """
        SELECT *
        FROM tasks
        WHERE assigned_to=?
        """,
        (employee_id,)
    )

    if tasks.empty:

        task_score = 0
        on_time_score = 0

    else:

        task_score = tasks[
            "completion"
        ].mean()

        completed = tasks[
            tasks["status"] == "Completed"
        ]

        if completed.empty:

            on_time_score = 0

        else:

            on_time_count = 0

            for _, task in completed.iterrows():

                if not task["due_date"]:
                    continue

                completed_at = (
                    task["completed_at"]
                    or ""
                )

                if completed_at:

                    if (
                        completed_at[:10]
                        <=
                        task["due_date"]
                    ):
                        on_time_count += 1

            on_time_score = (
                on_time_count
                /
                len(completed)
            ) * 100

    reviews = query(
        """
        SELECT manager_rating
        FROM performance_reviews
        WHERE employee_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (employee_id,)
    )

    manager_rating = (
        float(
            reviews.iloc[0][
                "manager_rating"
            ]
        )
        if not reviews.empty
        else 0
    )

    score = (
        task_score * 0.60
        +
        on_time_score * 0.25
        +
        manager_rating * 0.15
    )

    return {
        "score": round(score),
        "task_score": round(
            task_score
        ),
        "on_time": round(
            on_time_score
        ),
        "manager_rating": round(
            manager_rating
        )
    }


# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

def employee_dashboard():

    user_id = st.session_state[
        "user_id"
    ]

    user = query(
        "SELECT * FROM employees WHERE id=?",
        (user_id,)
    ).iloc[0]

    performance = calculate_performance(
        user_id
    )

    tasks = query(
        """
        SELECT *
        FROM tasks
        WHERE assigned_to=?
        ORDER BY due_date
        """,
        (user_id,)
    )

    pending = (
        len(
            tasks[
                tasks["status"]
                !=
                "Completed"
            ]
        )
        if not tasks.empty
        else 0
    )

    overdue = 0

    if not tasks.empty:

        today = date.today().isoformat()

        overdue = len(
            tasks[
                (
                    tasks["status"]
                    !=
                    "Completed"
                )
                &
                (
                    tasks["due_date"]
                    < today
                )
            ]
        )

    header(
        f"Welcome, {user['full_name']}",
        f"{user['position']} • {user['role']}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi(
            "Performance",
            f"{performance['score']}%",
            "Current score"
        )

    with c2:
        kpi(
            "Open Tasks",
            pending,
            "Assigned to you"
        )

    with c3:
        kpi(
            "Overdue",
            overdue,
            "Requires action"
        )

    with c4:
        kpi(
            "Employee Code",
            user["employee_code"],
            "Account"
        )

    st.write("")

    left, right = st.columns(2)

    with left:

        st.markdown(
            "### Your Performance"
        )

        st.markdown(
            f"""
            <div class="performance">
                <div class="score">
                    {performance['score']}%
                </div>

                <div style="
                    color:#94A3B8;
                ">
                    Overall Performance
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with right:

        st.markdown(
            "### Your Tasks"
        )

        if tasks.empty:

            st.info(
                "No tasks assigned."
            )

        else:

            st.dataframe(
                tasks[
                    [
                        "title",
                        "priority",
                        "status",
                        "completion",
                        "due_date"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# TASK ORGANIZER
# =========================================================

def task_organizer():

    header(
        "Task Organizer",
        "Assign, monitor and evaluate employee execution"
    )

    employees = query(
        """
        SELECT id, full_name, position
        FROM employees
        WHERE status='Active'
        ORDER BY full_name
        """
    )

    role = st.session_state[
        "user_role"
    ]

    user_id = st.session_state[
        "user_id"
    ]

    # =====================================================
    # EMPLOYEE VIEW
    # =====================================================

    if role not in [
        "Admin",
        "CEO",
        "Founder & Managing Director"
    ]:

        tasks = query(
            """
            SELECT *
            FROM tasks
            WHERE assigned_to=?
            ORDER BY due_date
            """,
            (user_id,)
        )

        st.markdown(
            "### My Tasks"
        )

        if tasks.empty:

            st.info(
                "No tasks assigned."
            )

        else:

            for _, task in tasks.iterrows():

                st.markdown(
                    f"""
                    ### {task['title']}

                    **Priority:** {task['priority']}

                    **Due:** {task['due_date']}

                    **Status:** {task['status']}
                    """
                )

                progress = st.slider(
                    "Completion",
                    0,
                    100,
                    int(task["completion"]),
                    key=f"progress_{task['id']}"
                )

                if st.button(
                    "UPDATE TASK",
                    key=f"update_{task['id']}"
                ):

                    status = (
                        "Completed"
                        if progress == 100
                        else "In Progress"
                    )

                    completed_at = (
                        datetime.now().isoformat()
                        if progress == 100
                        else None
                    )

                    execute(
                        """
                        UPDATE tasks
                        SET completion=?,
                            status=?,
                            completed_at=?
                        WHERE id=?
                        """,
                        (
                            progress,
                            status,
                            completed_at,
                            int(task["id"])
                        )
                    )

                    st.success(
                        "Task updated."
                    )

                    st.rerun()

        return

    # =====================================================
    # MANAGEMENT VIEW
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Task Board",
            "Create Task",
            "Edit / Delete",
            "Performance Reviews"
        ]
    )

    with tab1:

        tasks = query(
            """
            SELECT
                t.id,
                e.full_name AS employee,
                t.title,
                t.priority,
                t.status,
                t.completion,
                t.due_date
            FROM tasks t
            LEFT JOIN employees e
            ON t.assigned_to=e.id
            ORDER BY t.due_date
            """
        )

        st.dataframe(
            tasks,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        employee_map = dict(
            zip(
                employees["full_name"],
                employees["id"]
            )
        )

        with st.form(
            "create_task"
        ):

            employee = st.selectbox(
                "Assign To",
                list(employee_map.keys())
            )

            title = st.text_input(
                "Task Title"
            )

            description = st.text_area(
                "Description"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                priority = st.selectbox(
                    "Priority",
                    [
                        "Low",
                        "Medium",
                        "High",
                        "Critical"
                    ]
                )

            with c2:

                due_date = st.date_input(
                    "Due Date"
                )

            with c3:

                completion = st.slider(
                    "Initial Completion",
                    0,
                    100,
                    0
                )

            submit = st.form_submit_button(
                "CREATE TASK"
            )

            if submit:

                status = (
                    "Completed"
                    if completion == 100
                    else "Pending"
                )

                task_id = execute(
                    """
                    INSERT INTO tasks
                    (
                        assigned_to,
                        created_by,
                        title,
                        description,
                        priority,
                        status,
                        completion,
                        due_date,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        employee_map[employee],
                        user_id,
                        title,
                        description,
                        priority,
                        status,
                        completion,
                        due_date.isoformat(),
                        datetime.now().isoformat()
                    )
                )

                create_notification(
                    employee_map[employee],
                    "New Task Assigned",
                    f"You have been assigned: {title}",
                    "Task"
                )

                st.success(
                    f"Task #{task_id} created."
                )

                st.rerun()

    with tab3:

        tasks = query(
            "SELECT * FROM tasks ORDER BY id DESC"
        )

        if tasks.empty:

            st.info(
                "No tasks available."
            )

        else:

            selected = st.selectbox(
                "Select Task",
                tasks["id"].tolist()
            )

            task = tasks[
                tasks["id"] == selected
            ].iloc[0]

            new_title = st.text_input(
                "Task Title",
                value=task["title"]
            )

            new_status = st.selectbox(
                "Status",
                [
                    "Pending",
                    "In Progress",
                    "Completed",
                    "Cancelled"
                ],
                index=[
                    "Pending",
                    "In Progress",
                    "Completed",
                    "Cancelled"
                ].index(
                    task["status"]
                )
                if task["status"]
                in [
                    "Pending",
                    "In Progress",
                    "Completed",
                    "Cancelled"
                ]
                else 0
            )

            new_completion = st.slider(
                "Completion",
                0,
                100,
                int(task["completion"])
            )

            c1, c2 = st.columns(2)

            with c1:

                if st.button(
                    "SAVE CHANGES"
                ):

                    execute(
                        """
                        UPDATE tasks
                        SET title=?,
                            status=?,
                            completion=?
                        WHERE id=?
                        """,
                        (
                            new_title,
                            new_status,
                            new_completion,
                            int(selected)
                        )
                    )

                    st.success(
                        "Task updated."
                    )

                    st.rerun()

            with c2:

                if st.button(
                    "DELETE TASK"
                ):

                    execute(
                        "DELETE FROM tasks WHERE id=?",
                        (int(selected),)
                    )

                    st.success(
                        "Task deleted."
                    )

                    st.rerun()

    with tab4:

        employee_map = dict(
            zip(
                employees["full_name"],
                employees["id"]
            )
        )

        if employee_map:

            employee = st.selectbox(
                "Employee",
                list(employee_map.keys()),
                key="review_employee"
            )

            rating = st.slider(
                "Manager Rating",
                0,
                100,
                80
            )

            period = st.text_input(
                "Review Period",
                value=datetime.now().strftime(
                    "%B %Y"
                )
            )

            notes = st.text_area(
                "Performance Notes"
            )

            if st.button(
                "SAVE PERFORMANCE REVIEW"
            ):

                execute(
                    """
                    INSERT INTO performance_reviews
                    (
                        employee_id,
                        period,
                        manager_rating,
                        notes,
                        reviewed_by,
                        reviewed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        employee_map[employee],
                        period,
                        rating,
                        notes,
                        user_id,
                        datetime.now().isoformat()
                    )
                )

                st.success(
                    "Performance review saved."
                )

                st.rerun()


# =========================================================
# PERFORMANCE CENTER
# =========================================================

def performance_center():

    header(
        "Performance Center",
        "Executive employee performance overview"
    )

    employees = query(
        """
        SELECT *
        FROM employees
        WHERE status='Active'
        ORDER BY full_name
        """
    )

    records = []

    for _, employee in employees.iterrows():

        score = calculate_performance(
            int(employee["id"])
        )

        records.append(
            {
                "Employee":
                    employee["full_name"],

                "Position":
                    employee["position"],

                "Role":
                    employee["role"],

                "Performance":
                    score["score"],

                "Task Completion":
                    score["task_score"],

                "On-Time Delivery":
                    score["on_time"],

                "Manager Rating":
                    score["manager_rating"]
            }
        )

    df = pd.DataFrame(records)

    if df.empty:

        st.info(
            "No employee performance data."
        )

        return

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    fig = px.bar(
        df,
        x="Employee",
        y="Performance",
        text="Performance"
    )

    fig.update_layout(
        template="plotly_dark",
        yaxis_range=[0, 100]
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# =========================================================
# INTERNAL CHAT
# =========================================================

def internal_chat():

    header(
        "Internal Chat",
        "Secure employee-to-employee communication"
    )

    current_user = st.session_state[
        "user_id"
    ]

    employees = query(
        """
        SELECT id, full_name, position
        FROM employees
        WHERE id != ?
        AND status='Active'
        ORDER BY full_name
        """,
        (current_user,)
    )

    if employees.empty:

        st.info(
            "No other employees available."
        )

        return

    employee_map = dict(
        zip(
            employees["full_name"],
            employees["id"]
        )
    )

    selected = st.selectbox(
        "Chat With",
        list(employee_map.keys())
    )

    receiver = employee_map[selected]

    messages = query(
        """
        SELECT
            m.*,
            e.full_name AS sender
        FROM messages m
        LEFT JOIN employees e
        ON m.sender_id=e.id

        WHERE
        (
            m.sender_id=?
            AND
            m.receiver_id=?
        )

        OR

        (
            m.sender_id=?
            AND
            m.receiver_id=?
        )

        ORDER BY created_at
        """,
        (
            current_user,
            receiver,
            receiver,
            current_user
        )
    )

    for _, msg in messages.iterrows():

        css = (
            "chat-me"
            if int(msg["sender_id"])
            == current_user
            else
            "chat-other"
        )

        st.markdown(
            f"""
            <div class="chat-message {css}">
                <b>{msg['sender']}</b>
                <br>
                {msg['message']}
                <div style="
                    color:#71849A;
                    font-size:10px;
                    margin-top:5px;
                ">
                    {msg['created_at']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.form(
        "message_form"
    ):

        message = st.text_input(
            "Message"
        )

        send = st.form_submit_button(
            "SEND"
        )

        if send and message.strip():

            execute(
                """
                INSERT INTO messages
                (
                    sender_id,
                    receiver_id,
                    message,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    current_user,
                    receiver,
                    message,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

            create_notification(
                receiver,
                "New Message",
                f"{st.session_state['user_name']} sent you a message.",
                "Message"
            )

            st.rerun()


# =========================================================
# JOB DESCRIPTIONS
# =========================================================

def job_descriptions():

    header(
        "Job Description Library",
        "Central employee documentation repository"
    )

    employees = query(
        """
        SELECT id, full_name, position
        FROM employees
        ORDER BY full_name
        """
    )

    tab1, tab2 = st.tabs(
        [
            "Document Library",
            "Upload Word Document"
        ]
    )

    with tab1:

        docs = query(
            """
            SELECT
                j.id,
                j.title,
                j.file_name,
                e.full_name AS employee,
                j.uploaded_at,
                j.notes
            FROM job_descriptions j
            LEFT JOIN employees e
            ON j.employee_id=e.id
            ORDER BY j.id DESC
            """
        )

        if docs.empty:

            st.info(
                "No job descriptions uploaded yet."
            )

        else:

            st.dataframe(
                docs,
                use_container_width=True,
                hide_index=True
            )

            selected = st.selectbox(
                "Select Document",
                docs["id"].tolist()
            )

            data = query(
                """
                SELECT *
                FROM job_descriptions
                WHERE id=?
                """,
                (int(selected),)
            ).iloc[0]

            st.markdown(
                f"### {data['title']}"
            )

            if data["extracted_text"]:

                with st.expander(
                    "View extracted Word content"
                ):

                    st.text_area(
                        "Content",
                        data["extracted_text"],
                        height=450
                    )

            st.download_button(
                "DOWNLOAD WORD FILE",
                data=data["file_data"],
                file_name=data["file_name"],
                mime=
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            if st.session_state[
                "user_role"
            ] == "Admin":

                if st.button(
                    "DELETE DOCUMENT"
                ):

                    execute(
                        """
                        DELETE FROM job_descriptions
                        WHERE id=?
                        """,
                        (int(selected),)
                    )

                    st.success(
                        "Document deleted."
                    )

                    st.rerun()

    with tab2:

        if st.session_state[
            "user_role"
        ] != "Admin":

            st.warning(
                "Only Admin can upload Job Descriptions."
            )

            return

        employee_map = {
            f"{row['full_name']} — {row['position']}":
            int(row["id"])
            for _, row in employees.iterrows()
        }

        title = st.text_input(
            "Document Title"
        )

        employee = st.selectbox(
            "Employee",
            ["General"] +
            list(employee_map.keys())
        )

        uploaded = st.file_uploader(
            "Upload Word File",
            type=["docx"]
        )

        notes = st.text_area(
            "Notes"
        )

        if st.button(
            "UPLOAD DOCUMENT"
        ):

            if uploaded is None:

                st.error(
                    "Please upload a Word file."
                )

            else:

                extracted = ""

                try:

                    from docx import Document

                    doc = Document(
                        BytesIO(
                            uploaded.getvalue()
                        )
                    )

                    extracted = "\n".join(
                        p.text
                        for p in doc.paragraphs
                        if p.text.strip()
                    )

                except Exception:

                    extracted = (
                        "Unable to extract text."
                    )

                employee_id = (
                    employee_map[employee]
                    if employee != "General"
                    else None
                )

                execute(
                    """
                    INSERT INTO job_descriptions
                    (
                        employee_id,
                        title,
                        file_name,
                        file_data,
                        extracted_text,
                        uploaded_by,
                        uploaded_at,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        employee_id,
                        title or uploaded.name,
                        uploaded.name,
                        uploaded.getvalue(),
                        extracted,
                        st.session_state["user_id"],
                        datetime.now().isoformat(),
                        notes
                    )
                )

                st.success(
                    "Job Description uploaded successfully."
                )

                st.rerun()


# =========================================================
# ADMIN CONTROL CENTER
# =========================================================

def admin_center():

    header(
        "Admin Control Center",
        "Complete system administration"
    )

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Employee Accounts",
            "Branding",
            "Login Audit",
            "Email Settings"
        ]
    )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    with tab1:

        employees = query(
            """
            SELECT
                id,
                employee_code,
                full_name,
                position,
                email,
                phone,
                role,
                status,
                created_at
            FROM employees
            ORDER BY id DESC
            """
        )

        st.dataframe(
            employees,
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            "## Create Employee Account"
        )

        with st.form(
            "employee_creation"
        ):

            c1, c2 = st.columns(2)

            with c1:

                code = st.text_input(
                    "Employee Code"
                )

                name = st.text_input(
                    "Full Name"
                )

                position = st.text_input(
                    "Position"
                )

                email_address = st.text_input(
                    "Work Email"
                )

                phone = st.text_input(
                    "Mobile Number"
                )

            with c2:

                role = st.selectbox(
                    "Role",
                    [
                        "Employee",
                        "Manager",
                        "CEO",
                        "Founder & Managing Director",
                        "Admin"
                    ]
                )

                pin = st.text_input(
                    "Initial PIN",
                    type="password"
                )

                status = st.selectbox(
                    "Status",
                    [
                        "Active",
                        "Inactive"
                    ]
                )

            submit = st.form_submit_button(
                "CREATE ACCOUNT"
            )

            if submit:

                if not code or not name or not pin:

                    st.error(
                        "Employee Code, Name and PIN are required."
                    )

                else:

                    try:

                        employee_id = execute(
                            """
                            INSERT INTO employees
                            (
                                employee_code,
                                full_name,
                                position,
                                email,
                                phone,
                                pin_hash,
                                role,
                                status,
                                must_change_pin,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                code.upper().strip(),
                                name,
                                position,
                                email_address,
                                phone,
                                hash_pin(pin),
                                role,
                                status,
                                0,
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            f"Employee account #{employee_id} created."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Employee Code already exists."
                        )

        # =================================================
        # EDIT / DELETE
        # =================================================

        st.markdown(
            "## Manage Existing Employees"
        )

        employee_ids = employees[
            "id"
        ].tolist()

        if employee_ids:

            selected_id = st.selectbox(
                "Select Employee",
                employee_ids
            )

            selected_employee = employees[
                employees["id"]
                ==
                selected_id
            ].iloc[0]

            new_name = st.text_input(
                "Full Name",
                value=selected_employee["full_name"],
                key="edit_name"
            )

            new_position = st.text_input(
                "Position",
                value=selected_employee["position"] or "",
                key="edit_position"
            )

            new_email = st.text_input(
                "Email",
                value=selected_employee["email"] or "",
                key="edit_email"
            )

            new_phone = st.text_input(
                "Phone",
                value=selected_employee["phone"] or "",
                key="edit_phone"
            )

            new_role = st.selectbox(
                "Role",
                [
                    "Employee",
                    "Manager",
                    "CEO",
                    "Founder & Managing Director",
                    "Admin"
                ],
                index=[
                    "Employee",
                    "Manager",
                    "CEO",
                    "Founder & Managing Director",
                    "Admin"
                ].index(
                    selected_employee["role"]
                )
            )

            new_status = st.selectbox(
                "Status",
                [
                    "Active",
                    "Inactive"
                ],
                index=
                0
                if selected_employee["status"]
                == "Active"
                else 1
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                if st.button(
                    "SAVE EMPLOYEE CHANGES"
                ):

                    execute(
                        """
                        UPDATE employees
                        SET full_name=?,
                            position=?,
                            email=?,
                            phone=?,
                            role=?,
                            status=?
                        WHERE id=?
                        """,
                        (
                            new_name,
                            new_position,
                            new_email,
                            new_phone,
                            new_role,
                            new_status,
                            int(selected_id)
                        )
                    )

                    st.success(
                        "Employee updated."
                    )

                    st.rerun()

            with c2:

                if st.button(
                    "GENERATE NEW PIN"
                ):

                    temp_pin = generate_temp_pin()

                    execute(
                        """
                        UPDATE employees
                        SET pin_hash=?,
                            must_change_pin=1
                        WHERE id=?
                        """,
                        (
                            hash_pin(temp_pin),
                            int(selected_id)
                        )
                    )

                    st.warning(
                        f"Temporary PIN: {temp_pin}"
                    )

                    st.info(
                        "Give this temporary PIN to the employee. "
                        "It will not be stored as readable text."
                    )

            with c3:

                if selected_employee["role"] != "Admin":

                    if st.button(
                        "DELETE EMPLOYEE"
                    ):

                        execute(
                            "DELETE FROM employees WHERE id=?",
                            (int(selected_id),)
                        )

                        st.success(
                            "Employee deleted."
                        )

                        st.rerun()

    # =====================================================
    # BRANDING
    # =====================================================

    with tab2:

        st.markdown(
            "## MASAR Brand Settings"
        )

        uploaded_logo = st.file_uploader(
            "Change MASAR Logo",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ]
        )

        if st.button(
            "SAVE NEW LOGO"
        ):

            if uploaded_logo:

                encoded = base64.b64encode(
                    uploaded_logo.getvalue()
                ).decode()

                execute(
                    """
                    INSERT OR REPLACE
                    INTO settings
                    (key,value)
                    VALUES (?,?)
                    """,
                    (
                        "logo",
                        encoded
                    )
                )

                st.success(
                    "Logo updated successfully."
                )

                st.rerun()

            else:

                st.warning(
                    "Select a logo first."
                )

        current_logo = get_logo()

        if current_logo:

            st.image(
                current_logo,
                width=220
            )

    # =====================================================
    # LOGIN AUDIT
    # =====================================================

    with tab3:

        st.markdown(
            "## Login Audit Log"
        )

        logs = query(
            """
            SELECT
                full_name AS Employee,
                employee_code AS Code,
                login_time AS Login_Time,
                success AS Successful,
                device AS Device
            FROM login_logs
            ORDER BY id DESC
            LIMIT 500
            """
        )

        if logs.empty:

            st.info(
                "No login activity recorded."
            )

        else:

            logs["Successful"] = logs[
                "Successful"
            ].map(
                {
                    1: "YES",
                    0: "NO"
                }
            )

            st.dataframe(
                logs,
                use_container_width=True,
                hide_index=True
            )

            st.markdown(
                "### Login Activity"
            )

            activity = query(
                """
                SELECT
                    substr(login_time,1,10) AS Day,
                    COUNT(*) AS Logins
                FROM login_logs
                WHERE success=1
                GROUP BY substr(login_time,1,10)
                ORDER BY Day
                """
            )

            if not activity.empty:

                fig = px.bar(
                    activity,
                    x="Day",
                    y="Logins",
                    text="Logins"
                )

                fig.update_layout(
                    template="plotly_dark"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

    # =====================================================
    # EMAIL SETTINGS
    # =====================================================

    with tab4:

        st.markdown(
            "## Work Email Connection"
        )

        st.info(
            """
            Email credentials should preferably be stored in
            Streamlit Secrets rather than inside the database.
            """
        )

        st.code(
            """
[email]
imap_server = "imap.yourcompany.com"
imap_port = 993
email_address = "your@email.com"
email_password = "YOUR_PASSWORD"

[ai]
gemini_api_key = "YOUR_GEMINI_API_KEY"
gemini_model = "gemini-2.5-flash"
            """
        )

        st.markdown(
            """
            In Streamlit Cloud use:

            **Manage app → Settings → Secrets**
            """
        )


# =========================================================
# CRM
# =========================================================

def crm():

    header(
        "CRM & Companies Database",
        "Shared MASAR company database"
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Database",
            "Add Company",
            "Edit / Delete"
        ]
    )

    companies = query(
        "SELECT * FROM companies ORDER BY id DESC"
    )

    with tab1:

        search = st.text_input(
            "Search Companies"
        )

        filtered_df = companies

        if search:

            filtered_df = companies[
                companies["name"]
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form(
            "company_form_live"
        ):

            name = st.text_input(
                "Company Name"
            )

            website = st.text_input(
                "Website"
            )

            industry = st.text_input(
                "Industry"
            )

            country = st.text_input(
                "Country"
            )

            size = st.selectbox(
                "Company Size",
                [
                    "Startup",
                    "Small",
                    "Medium",
                    "Large",
                    "Enterprise",
                    "Government"
                ]
            )

            status = st.selectbox(
                "Status",
                [
                    "Prospect",
                    "Target",
                    "Active Client",
                    "Partner",
                    "Dormant"
                ]
            )

            description = st.text_area(
                "Description"
            )

            submit = st.form_submit_button(
                "ADD COMPANY"
            )

            if submit and name.strip():

                execute(
                    """
                    INSERT INTO companies
                    (
                        name,
                        website,
                        industry,
                        country,
                        size,
                        status,
                        description,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        website,
                        industry,
                        country,
                        size,
                        status,
                        description,
                        datetime.now().isoformat()
                    )
                )

                st.success(
                    "Company added."
                )

                st.rerun()

    with tab3:

        if companies.empty:

            st.info(
                "No companies."
            )

        else:

            selected = st.selectbox(
                "Select Company",
                companies["id"].tolist()
            )

            company = companies[
                companies["id"] == selected
            ].iloc[0]

            name = st.text_input(
                "Company Name",
                value=company["name"]
            )

            website = st.text_input(
                "Website",
                value=company["website"] or ""
            )

            industry = st.text_input(
                "Industry",
                value=company["industry"] or ""
            )

            status = st.selectbox(
                "Status",
                [
                    "Prospect",
                    "Target",
                    "Active Client",
                    "Partner",
                    "Dormant"
                ],
                index=[
                    "