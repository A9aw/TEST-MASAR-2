# ============================================================

# MASAR INTELLIGENCE OS

# V4.1 - STABLE SINGLE FILE EDITION

# ============================================================

import streamlit as st

import sqlite3

import pandas as pd

import plotly.express as px

import hashlib

import secrets

import string

import base64

import imaplib

import email

import os

from email.header import decode_header

from datetime import datetime, date

from html import unescape

from bs4 import BeautifulSoup

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

def executemany(sql, data, commit=True):

    conn = get_db()

    cur = conn.cursor()

    cur.executemany(sql, data)

    if commit:

        conn.commit()

    conn.close()

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

    # ========================================================
    # EMPLOYEES
    # ========================================================

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

    # ========================================================
    # MESSAGES
    # ========================================================

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

    # ========================================================
    # TASKS
    # ========================================================

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
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================================
    # PERFORMANCE
    # ========================================================

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

    # ========================================================
    # JOB DESCRIPTIONS
    # ========================================================

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

    # ========================================================
    # SETTINGS
    # ========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # ========================================================
    # COMPANIES
    # ========================================================

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

    # ========================================================
    # CONTACTS
    # ========================================================

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

    # ========================================================
    # OPPORTUNITIES
    # ========================================================

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

    # ========================================================
    # PROJECTS
    # ========================================================

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

    # ========================================================
    # GOVERNANCE
    # ========================================================

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

    # ========================================================
    # LOGIN LOGS
    # ========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            employee_code TEXT,
            event TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

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

    # ========================================================
    # EMAILS
    # ========================================================

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

    # ========================================================
    # SAFE MIGRATION FOR OLD DATABASES
    # ========================================================

    migrations = {

        "employees": {
            "employee_code": "TEXT",
            "full_name": "TEXT",
            "mobile": "TEXT",
            "email": "TEXT",
            "role": "TEXT DEFAULT 'Employee'",
            "pin_hash": "TEXT",
            "active": "INTEGER DEFAULT 1",
            "must_change_pin": "INTEGER DEFAULT 0",
            "created_at": "TEXT"
        },

        "messages": {
            "sender_id": "INTEGER",
            "receiver_id": "INTEGER",
            "message": "TEXT",
            "created_at": "TEXT",
            "is_read": "INTEGER DEFAULT 0"
        },

        "tasks": {
            "title": "TEXT",
            "description": "TEXT",
            "assigned_to": "INTEGER",
            "created_by": "INTEGER",
            "priority": "TEXT DEFAULT 'Medium'",
            "status": "TEXT DEFAULT 'Pending'",
            "due_date": "TEXT",
            "completed_at": "TEXT",
            "created_at": "TEXT"
        },

        "performance_reviews": {
            "employee_id": "INTEGER",
            "rating": "REAL DEFAULT 0",
            "notes": "TEXT",
            "review_date": "TEXT",
            "reviewer_id": "INTEGER"
        },

        "job_descriptions": {
            "employee_id": "INTEGER",
            "job_title": "TEXT",
            "file_name": "TEXT",
            "file_path": "TEXT",
            "uploaded_by": "INTEGER",
            "created_at": "TEXT"
        }
    }

    # Add missing columns without destroying existing data
    for table, columns in migrations.items():

        try:

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                f"PRAGMA table_info({table})"
            )

            existing_columns = {
                row[1]
                for row in cur.fetchall()
            }

            for column, definition in columns.items():

                if column not in existing_columns:

                    try:

                        cur.execute(
                            f"""
                            ALTER TABLE {table}
                            ADD COLUMN {column} {definition}
                            """
                        )

                    except Exception:
                        pass

            conn.commit()
            conn.close()

        except Exception:
            pass

    # ========================================================
    # CREATE DEFAULT ADMIN
    # ========================================================

    admin = query_one("""
        SELECT id
        FROM employees
        WHERE employee_code = ?
    """, ("ADMIN",))

    if not admin:

        execute("""
            INSERT INTO employees
            (
                employee_code,
                full_name,
                mobile,
                email,
                role,
                pin_hash,
                active,
                must_change_pin
            )
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

# SECURITY

# ============================================================

def hash_pin(pin):

    return hashlib.sha256(

        str(pin).encode("utf-8")

    ).hexdigest()

def verify_pin(pin, stored_hash):

    return hash_pin(pin) == stored_hash

def generate_temp_pin(length=6):

    chars = string.digits

    return "".join(secrets.choice(chars) for _ in range(length))

# ============================================================

# SETTINGS

# ============================================================

def get_setting(key, default=None):

    row = query_one(

        "SELECT value FROM settings WHERE key = ?",

        (key,)

    )

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

# ============================================================

# LOGGING

# ============================================================

def log_event(employee_id, employee_code, event):

    execute("""

        INSERT INTO login_logs(employee_id, employee_code, event)

        VALUES (?, ?, ?)

    """, (

        employee_id,

        employee_code,

        event

    ))

# ============================================================

# NOTIFICATIONS

# ============================================================

def create_notification(

    employee_id,

    title,

    message,

    notification_type="Info"

):

    execute("""

        INSERT INTO notifications

        (

            employee_id,

            title,

            message,

            notification_type

        )

        VALUES (?, ?, ?, ?)

    """, (

        employee_id,

        title,

        message,

        notification_type

    ))

def unread_notifications(employee_id):

    row = query_one("""

        SELECT COUNT(*) AS total

        FROM notifications

        WHERE employee_id = ?

        AND is_read = 0

    """, (employee_id,))

    return int(row["total"]) if row else 0

# ============================================================

# LOGO

# ============================================================

def get_logo():

    return get_setting("logo")

def display_logo():

    logo = get_logo()

    if logo:

        try:

            st.sidebar.image(

                base64.b64decode(logo),

                width=170

            )

        except Exception:

            pass

    else:

        st.sidebar.markdown(

            """

            <div class="brand-mark">◆</div>

            """,

            unsafe_allow_html=True

        )

# ============================================================

# CSS

# ============================================================

st.markdown("""

<style>

@import url(

'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'

);

html, body, [class*="css"] {

    font-family: 'Inter', sans-serif;

}

.stApp {

    background:

        radial-gradient(

            circle at 10% 0%,

            rgba(56,189,248,0.07),

            transparent 30%

        ),

        radial-gradient(

            circle at 90% 10%,

            rgba(30,58,138,0.12),

            transparent 35%

        ),

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

    background:

        linear-gradient(

            145deg,

            rgba(15,34,56,0.96),

            rgba(8,23,39,0.96)

        );

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

.status-good {

    color: #4ade80;

    font-weight: 700;

}

.status-warning {

    color: #fbbf24;

    font-weight: 700;

}

.status-danger {

    color: #fb7185;

    font-weight: 700;

}

.small-muted {

    color: #94a3b8;

    font-size: 12px;

}

div[data-testid="stMetric"] {

    background: rgba(10,28,46,0.8);

    padding: 12px;

    border-radius: 14px;

}

</style>

""", unsafe_allow_html=True)

# ============================================================

# UI HELPERS

# ============================================================

def page_header(title, subtitle=""):

    st.markdown(

        f'<div class="main-title">{title}</div>',

        unsafe_allow_html=True

    )

    if subtitle:

        st.markdown(

            f'<div class="sub-title">{subtitle}</div>',

            unsafe_allow_html=True

        )

def kpi(label, value):

    st.markdown(

        f"""

        <div class="kpi-card">

            <div class="kpi-label">{label}</div>

            <div class="kpi-value">{value}</div>

        </div>

        """,

        unsafe_allow_html=True

    )

def safe_text(value):

    if value is None:

        return ""

    return str(value)

# ============================================================

# PERFORMANCE ENGINE

# ============================================================

def calculate_employee_performance(employee_id):

    total_row = query_one("""

        SELECT COUNT(*) AS total

        FROM tasks

        WHERE assigned_to = ?

    """, (employee_id,))

    completed_row = query_one("""

        SELECT COUNT(*) AS total

        FROM tasks

        WHERE assigned_to = ?

        AND status = 'Completed'

    """, (employee_id,))

    total = int(total_row["total"]) if total_row else 0

    completed = int(completed_row["total"]) if completed_row else 0

    completion_score = (

        (completed / total) * 100

        if total > 0 else 0

    )

    overdue_row = query_one("""

        SELECT COUNT(*) AS total

        FROM tasks

        WHERE assigned_to = ?

        AND due_date IS NOT NULL

        AND due_date < ?

        AND status != 'Completed'

    """, (

        employee_id,

        str(date.today())

    ))

    overdue = int(overdue_row["total"]) if overdue_row else 0

    if total > 0:

        on_time_score = max(

            0,

            100 - ((overdue / total) * 100)

        )

    else:

        on_time_score = 0

    rating_row = query_one("""

        SELECT rating

        FROM performance_reviews

        WHERE employee_id = ?

        ORDER BY id DESC

        LIMIT 1

    """, (employee_id,))

    rating_score = (

        float(rating_row["rating"]) * 20

        if rating_row else 0

    )

    if total == 0 and not rating_row:

        return 0

    performance = (

        completion_score * 0.60

        + on_time_score * 0.25

        + rating_score * 0.15

    )

    return round(min(max(performance, 0), 100), 1)

# ============================================================

# LOGIN

# ============================================================

def login_page():

    st.markdown(

        """

        <div class="login-box">

            <h1 style="text-align:center;">MASAR</h1>

            <p style="text-align:center;color:#94a3b8;">

                Intelligence OS

            </p>

        </div>

        """,

        unsafe_allow_html=True

    )

    tab1, tab2 = st.tabs(

        ["Employee Login", "Forgot PIN"]

    )

    with tab1:

        with st.form("login_form"):

            code = st.text_input(

                "Employee Code",

                placeholder="Example: EMP001"

            )

            pin = st.text_input(

                "PIN",

                type="password"

            )

            submit = st.form_submit_button(

                "LOGIN",

                use_container_width=True

            )

            if submit:

                code = code.strip().upper()

                employee = query_one("""

                    SELECT *

                    FROM employees

                    WHERE employee_code = ?

                    AND active = 1

                """, (code,))

                if employee and verify_pin(

                    pin,

                    employee["pin_hash"]

                ):

                    st.session_state.user = dict(employee)

                    st.session_state.logged_in = True

                    log_event(

                        employee["id"],

                        employee["employee_code"],

                        "LOGIN_SUCCESS"

                    )

                    st.rerun()

                else:

                    if employee:

                        log_event(

                            employee["id"],

                            employee["employee_code"],

                            "LOGIN_FAILED"

                        )

                    else:

                        log_event(

                            None,

                            code,

                            "LOGIN_FAILED"

                        )

                    st.error(

                        "Invalid employee code or PIN."

                    )

    with tab2:

        st.info(

            "Enter your employee code and registered mobile number."

        )

        with st.form("forgot_form"):

            code = st.text_input(

                "Employee Code",

                key="forgot_code"

            )

            mobile = st.text_input(

                "Registered Mobile",

                key="forgot_mobile"

            )

            submit = st.form_submit_button(

                "RESET PIN",

                use_container_width=True

            )

            if submit:

                employee = query_one("""

                    SELECT *

                    FROM employees

                    WHERE employee_code = ?

                    AND mobile = ?

                    AND active = 1

                """, (

                    code.strip().upper(),

                    mobile.strip()

                ))

                if employee:

                    temp_pin = generate_temp_pin()

                    execute("""

                        UPDATE employees

                        SET pin_hash = ?,

                            must_change_pin = 1

                        WHERE id = ?

                    """, (

                        hash_pin(temp_pin),

                        employee["id"]

                    ))

                    create_notification(

                        employee["id"],

                        "Temporary PIN",

                        "Your PIN has been reset. Change it after login.",

                        "Security"

                    )

                    log_event(

                        employee["id"],

                        employee["employee_code"],

                        "PIN_RESET"

                    )

                    st.success(

                        "Temporary PIN generated."

                    )

                    st.warning(

                        f"Temporary PIN: {temp_pin}"

                    )

                    st.caption(

                        "For real SMS delivery, connect Twilio "

                        "or another SMS provider."

                    )

                else:

                    st.error(

                        "Employee code/mobile combination not found."

                    )

# ============================================================

# FORCE PIN CHANGE

# ============================================================

def force_change_pin():

    user = st.session_state.user

    page_header(

        "Security",

        "You must change your temporary PIN before continuing."

    )

    with st.form("change_pin"):

        old_pin = st.text_input(

            "Current PIN",

            type="password"

        )

        new_pin = st.text_input(

            "New PIN",

            type="password"

        )

        confirm = st.text_input(

            "Confirm New PIN",

            type="password"

        )

        submit = st.form_submit_button(

            "Change PIN",

            use_container_width=True

        )

        if submit:

            if not verify_pin(

                old_pin,

                user["pin_hash"]

            ):

                st.error("Current PIN is incorrect.")

                return

            if len(new_pin) < 4:

                st.error(

                    "PIN must contain at least 4 characters."

                )

                return

            if new_pin != confirm:

                st.error("PIN confirmation does not match.")

                return

            execute("""

                UPDATE employees

                SET pin_hash = ?,

                    must_change_pin = 0

                WHERE id = ?

            """, (

                hash_pin(new_pin),

                user["id"]

            ))

            updated = query_one(

                "SELECT * FROM employees WHERE id = ?",

                (user["id"],)

            )

            st.session_state.user = dict(updated)

            st.success("PIN changed successfully.")

            st.rerun()

# ============================================================

# DASHBOARD

# ============================================================

def dashboard():

    user = st.session_state.user

    page_header(

        "Executive Dashboard",

        f"Welcome back, {user['full_name']}"

    )

    employees = query(

        "SELECT * FROM employees WHERE active = 1"

    )

    companies = query(

        "SELECT * FROM companies"

    )

    opportunities = query(

        "SELECT * FROM opportunities"

    )

    tasks = query(

        "SELECT * FROM tasks"

    )

    projects = query(

        "SELECT * FROM projects"

    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        kpi(

            "Employees",

            len(employees)

        )

    with c2:

        kpi(

            "Companies",

            len(companies)

        )

    with c3:

        kpi(

            "Open Opportunities",

            len(

                opportunities[

                    opportunities["stage"] != "Won"

                ]

            ) if not opportunities.empty else 0

        )

    with c4:

        kpi(

            "Projects",

            len(projects)

        )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])

    with left:

        st.markdown(

            '<div class="card"><h3>Pipeline</h3>',

            unsafe_allow_html=True

        )

        if not opportunities.empty:

            pipeline = (

                opportunities

                .groupby("stage", as_index=False)["value"]

                .sum()

            )

            fig = px.bar(

                pipeline,

                x="stage",

                y="value",

                title="Opportunity Value by Stage"

            )

            fig.update_layout(

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)",

                font_color="#e2e8f0"

            )

            st.plotly_chart(

                fig,

                use_container_width=True

            )

        else:

            st.info("No opportunities yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:

        st.markdown(

            '<div class="card"><h3>Task Status</h3>',

            unsafe_allow_html=True

        )

        if not tasks.empty:

            task_status = (

                tasks

                .groupby("status")

                .size()

                .reset_index(name="count")

            )

            fig = px.pie(

                task_status,

                names="status",

                values="count",

                hole=0.55

            )

            fig.update_layout(

                paper_bgcolor="rgba(0,0,0,0)",

                font_color="#e2e8f0"

            )

            st.plotly_chart(

                fig,

                use_container_width=True

            )

        else:

            st.info("No tasks yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    # Recent activity

    st.subheader("Recent Activity")

    logs = query("""

        SELECT

            created_at,

            employee_code,

            event

        FROM login_logs

        ORDER BY id DESC

        LIMIT 10

    """)

    if not logs.empty:

        st.dataframe(

            logs,

            use_container_width=True,

            hide_index=True

        )

# ============================================================

# EMPLOYEE DASHBOARD

# ============================================================

def employee_dashboard():

    user = st.session_state.user

    performance = calculate_employee_performance(

        user["id"]

    )

    page_header(

        "My Workspace",

        "Your tasks, performance and notifications."

    )

    c1, c2, c3 = st.columns(3)

    with c1:

        kpi(

            "Performance",

            f"{performance}%"

        )

    my_tasks = query("""

        SELECT *

        FROM tasks

        WHERE assigned_to = ?

        ORDER BY

            CASE priority

                WHEN 'High' THEN 1

                WHEN 'Medium' THEN 2

                ELSE 3

            END,

            due_date

    """, (user["id"],))

    with c2:

        kpi(

            "My Tasks",

            len(my_tasks)

        )

    with c3:

        unread = unread_notifications(

            user["id"]

        )

        kpi(

            "Notifications",

            unread

        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("My Tasks")

    if my_tasks.empty:

        st.info("No tasks assigned to you.")

    else:

        display = my_tasks[

            [

                "title",

                "priority",

                "status",

                "due_date"

            ]

        ].copy()

        st.dataframe(

            display,

            use_container_width=True,

            hide_index=True

        )

    st.subheader("Performance Breakdown")

    st.progress(

        performance / 100

    )

    st.caption(

        "Performance formula: 60% task completion + "

        "25% delivery discipline + 15% manager rating."

    )

    st.subheader("Notifications")

    notifications = query("""

        SELECT *

        FROM notifications

        WHERE employee_id = ?

        ORDER BY id DESC

        LIMIT 20

    """, (user["id"],))

    if notifications.empty:

        st.info("No notifications.")

    else:

        for _, row in notifications.iterrows():

            st.markdown(

                f"""

                <div class="card">

                    <b>{safe_text(row['title'])}</b><br>

                    <span class="small-muted">

                        {safe_text(row['created_at'])}

                    </span>

                    <p>{safe_text(row['message'])}</p>

                </div>

                """,

                unsafe_allow_html=True

            )

# ============================================================

# TASK ORGANIZER

# ============================================================

def task_organizer():

    user = st.session_state.user

    page_header(

        "Task Organizer",

        "Create, assign, monitor and manage employee tasks."

    )

    if user["role"] == "Admin":

        tabs = st.tabs([

            "My Tasks",

            "Task Board",

            "Create Task",

            "Edit / Delete",

            "Performance Reviews"

        ])

        with tabs[0]:

            my_tasks_view(user)

        with tabs[1]:

            task_board()

        with tabs[2]:

            create_task()

        with tabs[3]:

            edit_delete_task()

        with tabs[4]:

            performance_reviews()

    else:

        my_tasks_view(user)

def my_tasks_view(user):

    tasks = query("""

        SELECT *

        FROM tasks

        WHERE assigned_to = ?

        ORDER BY due_date

    """, (user["id"],))

    if tasks.empty:

        st.info("No tasks found.")

        return

    for _, task in tasks.iterrows():

        st.markdown(

            f"""

            <div class="card">

                <h4>{safe_text(task['title'])}</h4>

                <p>{safe_text(task['description'])}</p>

                <b>Priority:</b> {safe_text(task['priority'])}

                &nbsp;&nbsp;

                <b>Status:</b> {safe_text(task['status'])}

                &nbsp;&nbsp;

                <b>Due:</b> {safe_text(task['due_date'])}

            </div>

            """,

            unsafe_allow_html=True

        )

        if task["status"] != "Completed":

            if st.button(

                f"Mark Completed #{task['id']}",

                key=f"complete_{task['id']}"

            ):

                execute("""

                    UPDATE tasks

                    SET status = 'Completed',

                        completed_at = ?

                    WHERE id = ?

                """, (

                    datetime.now().isoformat(),

                    task["id"]

                ))

                create_notification(

                    user["id"],

                    "Task Completed",

                    f"Task '{task['title']}' was marked completed.",

                    "Task"

                )

                st.rerun()

def task_board():

    tasks = query("""

        SELECT

            tasks.*,

            employees.full_name

        FROM tasks

        LEFT JOIN employees

            ON employees.id = tasks.assigned_to

        ORDER BY tasks.due_date

    """)

    if tasks.empty:

        st.info("No tasks.")

        return

    st.dataframe(

        tasks,

        use_container_width=True,

        hide_index=True

    )

def create_task():

    employees = query("""

        SELECT id, full_name, employee_code

        FROM employees

        WHERE active = 1

        AND role != 'Admin'

        ORDER BY full_name

    """)

    if employees.empty:

        st.warning("Create an employee first.")

        return

    employee_options = {

        f"{r['full_name']} ({r['employee_code']})": r["id"]

        for _, r in employees.iterrows()

    }

    with st.form("create_task_form"):

        title = st.text_input("Task Title")

        description = st.text_area(

            "Description"

        )

        assignee = st.selectbox(

            "Assign To",

            list(employee_options.keys())

        )

        priority = st.selectbox(

            "Priority",

            ["Low", "Medium", "High", "Critical"]

        )

        due_date = st.date_input(

            "Due Date",

            value=date.today()

        )

        submit = st.form_submit_button(

            "Create Task",

            use_container_width=True

        )

        if submit:

            if not title.strip():

                st.error("Task title is required.")

                return

            employee_id = employee_options[assignee]

            task_id = execute("""

                INSERT INTO tasks

                (

                    title,

                    description,

                    assigned_to,

                    created_by,

                    priority,

                    status,

                    due_date

                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

            """, (

                title.strip(),

                description,

                employee_id,

                st.session_state.user["id"],

                priority,

                "Pending",

                str(due_date)

            ))

            create_notification(

                employee_id,

                "New Task",

                f"You have been assigned: {title}",

                "Task"

            )

            st.success(

                f"Task #{task_id} created."

            )

def edit_delete_task():

    tasks = query("""

        SELECT id, title, status

        FROM tasks

        ORDER BY id DESC

    """)

    if tasks.empty:

        st.info("No tasks.")

        return

    options = {

        f"#{r['id']} - {r['title']}": r["id"]

        for _, r in tasks.iterrows()

    }

    selected = st.selectbox(

        "Select Task",

        list(options.keys())

    )

    task_id = options[selected]

    task = query_one(

        "SELECT * FROM tasks WHERE id = ?",

        (task_id,)

    )

    if not task:

        return

    with st.form("edit_task"):

        title = st.text_input(

            "Title",

            value=task["title"]

        )

        description = st.text_area(

            "Description",

            value=task["description"] or ""

        )

        status_options = [

            "Pending",

            "In Progress",

            "Completed",

            "Cancelled"

        ]

        current_status = (

            task["status"]

            if task["status"] in status_options

            else "Pending"

        )

        status = st.selectbox(

            "Status",

            status_options,

            index=status_options.index(current_status)

        )

        priority_options = [

            "Low",

            "Medium",

            "High",

            "Critical"

        ]

        current_priority = (

            task["priority"]

            if task["priority"] in priority_options

            else "Medium"

        )

        priority = st.selectbox(

            "Priority",

            priority_options,

            index=priority_options.index(current_priority)

        )

        submit = st.form_submit_button(

            "Save Changes",

            use_container_width=True

        )

        if submit:

            execute("""

                UPDATE tasks

                SET title = ?,

                    description = ?,

                    status = ?,

                    priority = ?

                WHERE id = ?

            """, (

                title,

                description,

                status,

                priority,

                task_id

            ))

            st.success("Task updated.")

            st.rerun()

    st.divider()

    if st.button(

        "Delete This Task",

        type="secondary"

    ):

        execute(

            "DELETE FROM tasks WHERE id = ?",

            (task_id,)

        )

        st.success("Task deleted.")

        st.rerun()

def performance_reviews():

    employees = query("""

        SELECT *

        FROM employees

        WHERE active = 1

        AND role != 'Admin'

        ORDER BY full_name

    """)

    if employees.empty:

        st.info("No employees.")

        return

    options = {

        f"{r['full_name']} ({r['employee_code']})": r["id"]

        for _, r in employees.iterrows()

    }

    selected = st.selectbox(

        "Employee",

        list(options.keys())

    )

    employee_id = options[selected]

    performance = calculate_employee_performance(

        employee_id

    )

    st.metric(

        "Calculated Performance",

        f"{performance}%"

    )

    with st.form("performance_form"):

        rating = st.slider(

            "Manager Rating",

            min_value=0.0,

            max_value=5.0,

            value=3.0,

            step=0.5

        )

        notes = st.text_area(

            "Manager Notes"

        )

        submit = st.form_submit_button(

            "Save Review",

            use_container_width=True

        )

        if submit:

            execute("""

                INSERT INTO performance_reviews

                (

                    employee_id,

                    rating,

                    notes,

                    reviewer_id

                )

                VALUES (?, ?, ?, ?)

            """, (

                employee_id,

                rating,

                notes,

                st.session_state.user["id"]

            ))

            create_notification(

                employee_id,

                "Performance Review",

                f"A new performance review was added. Rating: {rating}/5",

                "Performance"

            )

            st.success("Performance review saved.")

            st.rerun()

# ============================================================

# INTERNAL CHAT

# ============================================================

def internal_chat():

    user = st.session_state.user

    page_header(

        "Internal Chat",

        "Secure employee-to-employee communication."

    )

    employees = query("""

        SELECT id, full_name, employee_code

        FROM employees

        WHERE active = 1

        AND id != ?

        ORDER BY full_name

    """, (user["id"],))

    if employees.empty:

        st.info("No other employees available.")

        return

    options = {

        f"{r['full_name']} ({r['employee_code']})": r["id"]

        for _, r in employees.iterrows()

    }

    selected = st.selectbox(

        "Chat With",

        list(options.keys())

    )

    receiver_id = options[selected]

    messages = query("""

        SELECT *

        FROM messages

        WHERE

            (sender_id = ? AND receiver_id = ?)

            OR

            (sender_id = ? AND receiver_id = ?)

        ORDER BY id

    """, (

        user["id"],

        receiver_id,

        receiver_id,

        user["id"]

    ))

    st.markdown(

        '<div class="card">',

        unsafe_allow_html=True

    )

    if messages.empty:

        st.info("No messages yet.")

    else:

        for _, msg in messages.iterrows():

            sender = (

                "You"

                if msg["sender_id"] == user["id"]

                else selected

            )

            st.markdown(

                f"""

                <div style="margin:10px 0;">

                    <b>{safe_text(sender)}</b>

                    <span class="small-muted">

                        {safe_text(msg['created_at'])}

                    </span>

                    <br>

                    {safe_text(msg['message'])}

                </div>

                """,

                unsafe_allow_html=True

            )

    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("send_message"):

        message = st.text_area(

            "Message",

            height=100

        )

        send = st.form_submit_button(

            "Send",

            use_container_width=True

        )

        if send and message.strip():

            execute("""

                INSERT INTO messages

                (

                    sender_id,

                    receiver_id,

                    message

                )

                VALUES (?, ?, ?)

            """, (

                user["id"],

                receiver_id,

                message.strip()

            ))

            create_notification(

                receiver_id,

                "New Message",

                f"New message from {user['full_name']}",

                "Chat"

            )

            st.rerun()

# ============================================================

# JOB DESCRIPTIONS

# ============================================================

def job_description_library():

    user = st.session_state.user

    page_header(

        "Job Description Library",

        "Upload and manage Word-format job descriptions."

    )

    if user["role"] == "Admin":

        with st.form(

            "upload_jd",

            clear_on_submit=True

        ):

            employees = query("""

                SELECT id, full_name, employee_code

                FROM employees

                WHERE active = 1

                ORDER BY full_name

            """)

            employee_options = {

                f"{r['full_name']} ({r['employee_code']})": r["id"]

                for _, r in employees.iterrows()

            }

            if employee_options:

                employee_name = st.selectbox(

                    "Employee / Position",

                    list(employee_options.keys())

                )

            else:

                employee_name = None

            job_title = st.text_input(

                "Job Title"

            )

            uploaded_file = st.file_uploader(

                "Upload Job Description",

                type=["docx", "doc"]

            )

            submit = st.form_submit_button(

                "Upload",

                use_container_width=True

            )

            if submit:

                if not uploaded_file:

                    st.error("Please upload a Word file.")

                    return

                filename = uploaded_file.name

                safe_name = (

                    datetime.now().strftime("%Y%m%d%H%M%S")

                    + "_"

                    + filename.replace("/", "_")

                    .replace("\\", "_")

                )

                path = os.path.join(

                    UPLOAD_DIR,

                    safe_name

                )

                with open(path, "wb") as f:

                    f.write(uploaded_file.getbuffer())

                employee_id = (

                    employee_options[employee_name]

                    if employee_name

                    else None

                )

                execute("""

                    INSERT INTO job_descriptions

                    (

                        employee_id,

                        job_title,

                        file_name,

                        file_path,

                        uploaded_by

                    )

                    VALUES (?, ?, ?, ?, ?)

                """, (

                    employee_id,

                    job_title,

                    filename,

                    path,

                    user["id"]

                ))

                st.success(

                    "Job description uploaded successfully."

                )

    jds = query("""

        SELECT

            job_descriptions.*,

            employees.full_name

        FROM job_descriptions

        LEFT JOIN employees

            ON employees.id = job_descriptions.employee_id

        ORDER BY job_descriptions.id DESC

    """)

    st.subheader("Library")

    if jds.empty:

        st.info("No job descriptions uploaded.")

    else:

        for _, row in jds.iterrows():

            st.markdown(

                f"""

                <div class="card">

                    <b>{safe_text(row['job_title'])}</b><br>

                    Employee:

                    {safe_text(row['full_name'])}<br>

                    File:

                    {safe_text(row['file_name'])}

                </div>

                """,

                unsafe_allow_html=True

            )

            path = row["file_path"]

            if path and os.path.exists(path):

                with open(path, "rb") as f:

                    data = f.read()

                st.download_button(

                    "Download Word File",

                    data=data,

                    file_name=row["file_name"],

                    key=f"download_jd_{row['id']}"

                )

# ============================================================

# CRM - COMPANIES

# ============================================================

def crm():

    user = st.session_state.user

    page_header(

        "CRM",

        "Companies, contacts and commercial relationships."

    )

    tabs = st.tabs([

        "Companies",

        "Add Company",

        "Edit / Delete",

        "Contacts"

    ])

    with tabs[0]:

        companies = query("""

            SELECT *

            FROM companies

            ORDER BY id DESC

        """)

        if companies.empty:

            st.info("No companies yet.")

        else:

            st.dataframe(

                companies,

                use_container_width=True,

                hide_index=True

            )

    with tabs[1]:

        with st.form("add_company"):

            name = st.text_input(

                "Company Name"

            )

            website = st.text_input(

                "Website"

            )

            industry = st.text_input(

                "Industry"

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

            notes = st.text_area(

                "Notes"

            )

            submit = st.form_submit_button(

                "Add Company",

                use_container_width=True

            )

            if submit:

                if not name.strip():

                    st.error("Company name is required.")

                else:

                    execute("""

                        INSERT INTO companies

                        (

                            name,

                            website,

                            industry,

                            status,

                            notes

                        )

                        VALUES (?, ?, ?, ?, ?)

                    """, (

                        name.strip(),

                        website.strip(),

                        industry.strip(),

                        status,

                        notes

                    ))

                    st.success(

                        "Company added successfully."

                    )

                    st.rerun()

    with tabs[2]:

        companies = query("""

            SELECT *

            FROM companies

            ORDER BY name

        """)

        if companies.empty:

            st.info("No companies to edit.")

        else:

            company_options = {

                f"{r['name']} #{r['id']}": r["id"]

                for _, r in companies.iterrows()

            }

            selected = st.selectbox(

                "Select Company",

                list(company_options.keys())

            )

            company_id = company_options[selected]

            company = query_one(

                "SELECT * FROM companies WHERE id = ?",

                (company_id,)

            )

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

            status_options = [

                "Prospect",

                "Target",

                "Active Client",

                "Partner",

                "Dormant"

            ]

            current_status = company["status"]

            if current_status not in status_options:

                current_status = "Prospect"

            status = st.selectbox(

                "Status",

                status_options,

                index=status_options.index(current_status)

            )

            notes = st.text_area(

                "Notes",

                value=company["notes"] or ""

            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(

                    "Save Changes",

                    use_container_width=True

                ):

                    execute("""

                        UPDATE companies

                        SET name = ?,

                            website = ?,

                            industry = ?,

                            status = ?,

                            notes = ?

                        WHERE id = ?

                    """, (

                        name,

                        website,

                        industry,

                        status,

                        notes,

                        company_id

                    ))

                    st.success("Company updated.")

                    st.rerun()

            with col2:

                if st.button(

                    "Delete Company",

                    use_container_width=True

                ):

                    execute(

                        "DELETE FROM companies WHERE id = ?",

                        (company_id,)

                    )

                    st.success("Company deleted.")

                    st.rerun()

    with tabs[3]:

        companies = query(

            "SELECT id, name FROM companies ORDER BY name"

        )

        if companies.empty:

            st.info("Add a company first.")

        else:

            company_options = {

                f"{r['name']} #{r['id']}": r["id"]

                for _, r in companies.iterrows()

            }

            company_name = st.selectbox(

                "Company",

                list(company_options.keys())

            )

            company_id = company_options[company_name]

            with st.form("add_contact"):

                name = st.text_input(

                    "Contact Name"

                )

                title = st.text_input(

                    "Job Title"

                )

                mobile = st.text_input(

                    "Mobile"

                )

                contact_email = st.text_input(

                    "Email"

                )

                notes = st.text_area(

                    "Notes"

                )

                submit = st.form_submit_button(

                    "Add Contact",

                    use_container_width=True

                )

                if submit:

                    if not name.strip():

                        st.error("Contact name is required.")

                    else:

                        execute("""

                            INSERT INTO contacts

                            (

                                company_id,

                                name,

                                title,

                                mobile,

                                email,

                                notes

                            )

                            VALUES (?, ?, ?, ?, ?, ?)

                        """, (

                            company_id,

                            name,

                            title,

                            mobile,

                            contact_email,

                            notes

                        ))

                        st.success(

                            "Contact added."

                        )

                        st.rerun()

            contacts = query("""

                SELECT

                    contacts.*,

                    companies.name AS company_name

                FROM contacts

                LEFT JOIN companies

                    ON companies.id = contacts.company_id

                ORDER BY contacts.id DESC

            """)

            if not contacts.empty:

                st.dataframe(

                    contacts,

                    use_container_width=True,

                    hide_index=True

                )

# ============================================================

# OPPORTUNITIES

# ============================================================

def opportunities():

    page_header(

        "Opportunities",

        "Manage your commercial pipeline."

    )

    companies = query(

        "SELECT id, name FROM companies ORDER BY name"

    )

    if companies.empty:

        st.warning(

            "Create companies in CRM first."

        )

        return

    tabs = st.tabs([

        "Pipeline",

        "New Opportunity"

    ])

    with tabs[0]:

        data = query("""

            SELECT

                opportunities.*,

                companies.name AS company_name

            FROM opportunities

            LEFT JOIN companies

                ON companies.id = opportunities.company_id

            ORDER BY opportunities.id DESC

        """)

        if data.empty:

            st.info("No opportunities.")

        else:

            st.dataframe(

                data,

                use_container_width=True,

                hide_index=True

            )

    with tabs[1]:

        company_options = {

            f"{r['name']} #{r['id']}": r["id"]

            for _, r in companies.iterrows()

        }

        with st.form("new_opportunity"):

            company_name = st.selectbox(

                "Company",

                list(company_options.keys())

            )

            title = st.text_input(

                "Opportunity Title"

            )

            value = st.number_input(

                "Value",

                min_value=0.0,

                step=1000.0

            )

            stage = st.selectbox(

                "Stage",

                [

                    "New",

                    "Qualified",

                    "Proposal",

                    "Negotiation",

                    "Won",

                    "Lost"

                ]

            )

            probability = st.slider(

                "Probability %",

                0,

                100,

                25

            )

            expected_close = st.date_input(

                "Expected Close"

            )

            notes = st.text_area(

                "Notes"

            )

            submit = st.form_submit_button(

                "Create Opportunity",

                use_container_width=True

            )

            if submit:

                execute("""

                    INSERT INTO opportunities

                    (

                        company_id,

                        title,

                        value,

                        stage,

                        probability,

                        owner_id,

                        expected_close,

                        notes

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    company_options[company_name],

                    title,

                    value,

                    stage,

                    probability,

                    st.session_state.user["id"],

                    str(expected_close),

                    notes

                ))

                st.success(

                    "Opportunity created."

                )

                st.rerun()

# ============================================================

# PROJECTS

# ============================================================

def projects():

    page_header(

        "Projects",

        "Track delivery and strategic engagements."

    )

    companies = query(

        "SELECT id, name FROM companies ORDER BY name"

    )

    if companies.empty:

        st.warning("Create a company first.")

        return

    tabs = st.tabs([

        "Projects",

        "New Project"

    ])

    with tabs[0]:

        data = query("""

            SELECT

                projects.*,

                companies.name AS company_name,

                employees.full_name AS owner_name

            FROM projects

            LEFT JOIN companies

                ON companies.id = projects.company_id

            LEFT JOIN employees

                ON employees.id = projects.owner_id

            ORDER BY projects.id DESC

        """)

        if data.empty:

            st.info("No projects.")

        else:

            st.dataframe(

                data,

                use_container_width=True,

                hide_index=True

            )

    with tabs[1]:

        company_options = {

            f"{r['name']} #{r['id']}": r["id"]

            for _, r in companies.iterrows()

        }

        with st.form("new_project"):

            company_name = st.selectbox(

                "Company",

                list(company_options.keys())

            )

            name = st.text_input(

                "Project Name"

            )

            status = st.selectbox(

                "Status",

                [

                    "Planning",

                    "Active",

                    "On Hold",

                    "Completed",

                    "Cancelled"

                ]

            )

            progress = st.slider(

                "Progress %",

                0,

                100,

                0

            )

            start_date = st.date_input(

                "Start Date"

            )

            end_date = st.date_input(

                "End Date"

            )

            notes = st.text_area(

                "Notes"

            )

            submit = st.form_submit_button(

                "Create Project",

                use_container_width=True

            )

            if submit:

                execute("""

                    INSERT INTO projects

                    (

                        company_id,

                        name,

                        status,

                        progress,

                        owner_id,

                        start_date,

                        end_date,

                        notes

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """, (

                    company_options[company_name],

                    name,

                    status,

                    progress,

                    st.session_state.user["id"],

                    str(start_date),

                    str(end_date),

                    notes

                ))

                st.success("Project created.")

                st.rerun()

# ============================================================

# GOVERNANCE

# ============================================================

def governance():

    page_header(

        "Governance",

        "Policies, procedures and governance records."

    )

    tabs = st.tabs([

        "Library",

        "Add Record"

    ])

    with tabs[0]:

        data = query("""

            SELECT

                governance.*,

                employees.full_name AS owner_name

            FROM governance

            LEFT JOIN employees

                ON employees.id = governance.owner_id

            ORDER BY governance.id DESC

        """)

        if data.empty:

            st.info("No governance records.")

        else:

            st.dataframe(

                data,

                use_container_width=True,

                hide_index=True

            )

    with tabs[1]:

        with st.form("governance_form"):

            title = st.text_input(

                "Title"

            )

            category = st.selectbox(

                "Category",

                [

                    "Policy",

                    "Procedure",

                    "Governance",

                    "Compliance",

                    "Other"

                ]

            )

            description = st.text_area(

                "Description"

            )

            review_date = st.date_input(

                "Review Date"

            )

            status = st.selectbox(

                "Status",

                [

                    "Active",

                    "Under Review",

                    "Archived"

                ]

            )

            submit = st.form_submit_button(

                "Add Record",

                use_container_width=True

            )

            if submit:

                execute("""

                    INSERT INTO governance

                    (

                        title,

                        category,

                        description,

                        owner_id,

                        review_date,

                        status

                    )

                    VALUES (?, ?, ?, ?, ?, ?)

                """, (

                    title,

                    category,

                    description,

                    st.session_state.user["id"],

                    str(review_date),

                    status

                ))

                st.success(

                    "Governance record added."

                )

                st.rerun()

# ============================================================

# EMAIL ASSISTANT

# ============================================================

def decode_email_subject(subject):

    if not subject:

        return ""

    decoded = decode_header(subject)

    result = []

    for part, encoding in decoded:

        if isinstance(part, bytes):

            try:

                result.append(

                    part.decode(

                        encoding or "utf-8",

                        errors="ignore"

                    )

                )

            except Exception:

                result.append(

                    part.decode(

                        "utf-8",

                        errors="ignore"

                    )

                )

        else:

            result.append(str(part))

    return "".join(result)

def extract_email_body(message):

    body = ""

    if message.is_multipart():

        for part in message.walk():

            content_type = part.get_content_type()

            disposition = str(

                part.get("Content-Disposition", "")

            )

            if (

                content_type == "text/plain"

                and "attachment" not in disposition.lower()

            ):

                payload = part.get_payload(

                    decode=True

                )

                if payload:

                    body += payload.decode(

                        "utf-8",

                        errors="ignore"

                    )

    else:

        payload = message.get_payload(

            decode=True

        )

        if isinstance(payload, bytes):

            body = payload.decode(

                "utf-8",

                errors="ignore"

            )

        elif payload:

            body = str(payload)

    if not body:

        html_part = ""

        if message.is_multipart():

            for part in message.walk():

                if part.get_content_type() == "text/html":

                    payload = part.get_payload(

                        decode=True

                    )

                    if payload:

                        html_part += payload.decode(

                            "utf-8",

                            errors="ignore"

                        )

        if html_part:

            soup = BeautifulSoup(

                html_part,

                "html.parser"

            )

            body = soup.get_text(

                "\n",

                strip=True

            )

    return unescape(body).strip()

def simple_email_summary(subject, body):

    text = " ".join(

        body.replace("\n", " ").split()

    )

    if len(text) > 700:

        text = text[:700] + "..."

    if not text:

        text = "No readable email body."

    return (

        f"Subject: {subject}\n\n"

        f"Summary: {text}"

    )

def sync_emails():

    host = get_setting("imap_host", "")

    port = int(

        get_setting("imap_port", "993") or 993

    )

    username = get_setting("imap_username", "")

    password = get_setting("imap_password", "")

    if not host or not username or not password:

        return False, (

            "Configure IMAP settings first."

        )

    try:

        mail = imaplib.IMAP4_SSL(

            host,

            port

        )

        mail.login(

            username,

            password

        )

        mail.select("INBOX")

        status, data = mail.search(

            None,

            "ALL"

        )

        if status != "OK":

            mail.logout()

            return False, (

                "Unable to read mailbox."

            )

        email_ids = data[0].split()

        # Process latest 30 emails

        email_ids = email_ids[-30:]

        added = 0

        for uid in email_ids:

            uid_text = uid.decode(

                errors="ignore"

            )

            exists = query_one(

                "SELECT id FROM emails WHERE message_uid = ?",

                (uid_text,)

            )

            if exists:

                continue

            status, msg_data = mail.fetch(

                uid,

                "(RFC822)"

            )

            if status != "OK":

                continue

            raw_email = None

            for response_part in msg_data:

                if isinstance(

                    response_part,

                    tuple

                ):

                    raw_email = response_part[1]

                    break

            if not raw_email:

                continue

            msg = email.message_from_bytes(

                raw_email

            )

            subject = decode_email_subject(

                msg.get("Subject", "")

            )

            sender = msg.get(

                "From",

                ""

            )

            body = extract_email_body(

                msg

            )

            received = msg.get(

                "Date",

                ""

            )

            summary = simple_email_summary(

                subject,

                body

            )

            execute("""

                INSERT OR IGNORE INTO emails

                (

                    message_uid,

                    sender,

                    subject,

                    received_at,

                    body,

                    summary

                )

                VALUES (?, ?, ?, ?, ?, ?)

            """, (

                uid_text,

                sender,

                subject,

                received,

                body,

                summary

            ))

            added += 1

        mail.logout()

        return True, (

            f"{added} new emails imported."

        )

    except Exception as exc:

        return False, (

            f"Email connection error: {exc}"

        )

def email_assistant():

    page_header(

        "Email Intelligence",

        "Email-only assistant for mailbox monitoring and summaries."

    )

    st.info(

        "This module is intentionally limited to email processing."

    )

    if st.session_state.user["role"] != "Admin":

        st.warning(

            "Only Admin can configure the mailbox."

        )

    tabs = st.tabs([

        "Inbox Intelligence",

        "Mailbox Settings"

    ])

    with tabs[0]:

        if st.button(

            "Sync Inbox",

            use_container_width=True

        ):

            ok, message = sync_emails()

            if ok:

                st.success(message)

            else:

                st.error(message)

        emails_df = query("""

            SELECT *

            FROM emails

            ORDER BY id DESC

            LIMIT 50

        """)

        if emails_df.empty:

            st.info(

                "No emails imported yet."

            )

        else:

            for _, row in emails_df.iterrows():

                with st.expander(

                    f"{row['subject']} — {row['sender']}"

                ):

                    st.caption(

                        row["received_at"]

                    )

                    st.markdown(

                        "### Summary"

                    )

                    st.write(

                        row["summary"]

                    )

                    st.markdown(

                        "### Original Email"

                    )

                    st.write(

                        row["body"][:5000]

                    )

    with tabs[1]:

        if st.session_state.user["role"] != "Admin":

            st.info(

                "Admin access required."

            )

        else:

            with st.form("email_settings"):

                host = st.text_input(

                    "IMAP Host",

                    value=get_setting(

                        "imap_host",

                        ""

                    )

                )

                port = st.number_input(

                    "IMAP Port",

                    min_value=1,

                    max_value=65535,

                    value=int(

                        get_setting(

                            "imap_port",

                            "993"

                        )

                    )

                )

                username = st.text_input(

                    "Mailbox Username",

                    value=get_setting(

                        "imap_username",

                        ""

                    )

                )

                password = st.text_input(

                    "Mailbox Password",

                    type="password",

                    value=get_setting(

                        "imap_password",

                        ""

                    )

                )

                save = st.form_submit_button(

                    "Save Mailbox Settings",

                    use_container_width=True

                )

                if save:

                    set_setting(

                        "imap_host",

                        host

                    )

                    set_setting(

                        "imap_port",

                        str(port)

                    )

                    set_setting(

                        "imap_username",

                        username

                    )

                    set_setting(

                        "imap_password",

                        password

                    )

                    st.success(

                        "Mailbox settings saved."

                    )

# ============================================================

# ADMIN CONTROL CENTER

# ============================================================

def admin_center():

    user = st.session_state.user

    if user["role"] != "Admin":

        st.error(

            "Administrator access required."

        )

        return

    page_header(

        "Admin Control Center",

        "Manage employees, branding, security and system activity."

    )

    tabs = st.tabs([

        "Employees",

        "Create Employee",

        "Edit Employee",

        "Branding",

        "Login Audit"

    ])

    # --------------------------------------------------------

    # Employees

    # --------------------------------------------------------

    with tabs[0]:

        employees = query("""

            SELECT

                id,

                employee_code,

                full_name,

                mobile,

                email,

                role,

                active,

                must_change_pin,

                created_at

            FROM employees

            ORDER BY id DESC

        """)

        st.dataframe(

            employees,

            use_container_width=True,

            hide_index=True

        )

        st.caption(

            "For security, stored PINs are hashed and the current "

            "PIN is not displayed. Admin can reset a PIN."

        )

    # --------------------------------------------------------

    # Create Employee

    # --------------------------------------------------------

    with tabs[1]:

        with st.form("create_employee"):

            code = st.text_input(

                "Employee Code",

                placeholder="EMP001"

            )

            full_name = st.text_input(

                "Full Name"

            )

            mobile = st.text_input(

                "Mobile Number"

            )

            employee_email = st.text_input(

                "Work Email"

            )

            role = st.selectbox(

                "Role",

                [

                    "Employee",

                    "Manager",

                    "Admin"

                ]

            )

            initial_pin = st.text_input(

                "Initial PIN",

                value=generate_temp_pin(),

                type="password"

            )

            submit = st.form_submit_button(

                "Create Employee",

                use_container_width=True

            )

            if submit:

                code = code.strip().upper()

                if not code or not full_name.strip():

                    st.error(

                        "Employee code and full name are required."

                    )

                elif query_one(

                    "SELECT id FROM employees WHERE employee_code = ?",

                    (code,)

                ):

                    st.error(

                        "Employee code already exists."

                    )

                else:

                    employee_id = execute("""

                        INSERT INTO employees

                        (

                            employee_code,

                            full_name,

                            mobile,

                            email,

                            role,

                            pin_hash,

                            active,

                            must_change_pin

                        )

                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                    """, (

                        code,

                        full_name.strip(),

                        mobile.strip(),

                        employee_email.strip(),

                        role,

                        hash_pin(initial_pin),

                        1,

                        1

                    ))

                    create_notification(

                        employee_id,

                        "Welcome to MASAR",

                        "Your employee account has been created.",

                        "System"

                    )

                    st.success(

                        f"Employee created successfully. "

                        f"Temporary PIN: {initial_pin}"

                    )

    # --------------------------------------------------------

    # Edit Employee

    # --------------------------------------------------------

    with tabs[2]:

        employees = query("""

            SELECT *

            FROM employees

            ORDER BY full_name

        """)

        if employees.empty:

            st.info("No employees.")

        else:

            options = {

                f"{r['full_name']} ({r['employee_code']})":

                r["id"]

                for _, r in employees.iterrows()

            }

            selected = st.selectbox(

                "Select Employee",

                list(options.keys()),

                key="admin_employee_select"

            )

            employee_id = options[selected]

            employee = query_one(

                "SELECT * FROM employees WHERE id = ?",

                (employee_id,)

            )

            full_name = st.text_input(

                "Full Name",

                value=employee["full_name"],

                key="edit_name"

            )

            mobile = st.text_input(

                "Mobile",

                value=employee["mobile"] or "",

                key="edit_mobile"

            )

            employee_email = st.text_input(

                "Email",

                value=employee["email"] or "",

                key="edit_email"

            )

            role_options = [

                "Employee",

                "Manager",

                "Admin"

            ]

            current_role = (

                employee["role"]

                if employee["role"] in role_options

                else "Employee"

            )

            role = st.selectbox(

                "Role",

                role_options,

                index=role_options.index(current_role),

                key="edit_role"

            )

            active = st.checkbox(

                "Active Account",

                value=bool(employee["active"]),

                key="edit_active"

            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(

                    "Save Employee",

                    use_container_width=True

                ):

                    execute("""

                        UPDATE employees

                        SET full_name = ?,

                            mobile = ?,

                            email = ?,

                            role = ?,

                            active = ?

                        WHERE id = ?

                    """, (

                        full_name,

                        mobile,

                        employee_email,

                        role,

                        int(active),

                        employee_id

                    ))

                    st.success(

                        "Employee updated."

                    )

                    st.rerun()

            with col2:

                if st.button(

                    "Reset PIN",

                    use_container_width=True

                ):

                    new_pin = generate_temp_pin()

                    execute("""

                        UPDATE employees

                        SET pin_hash = ?,

                            must_change_pin = 1

                        WHERE id = ?

                    """, (

                        hash_pin(new_pin),

                        employee_id

                    ))

                    st.success(

                        f"Temporary PIN: {new_pin}"

                    )

    # --------------------------------------------------------

    # Branding

    # --------------------------------------------------------

    with tabs[3]:

        st.subheader(

            "Company Branding"

        )

        uploaded_logo = st.file_uploader(

            "Upload Company Logo",

            type=[

                "png",

                "jpg",

                "jpeg",

                "webp"

            ]

        )

        if uploaded_logo:

            encoded = base64.b64encode(

                uploaded_logo.getvalue()

            ).decode("utf-8")

            if st.button(

                "Save Logo",

                use_container_width=True

            ):

                set_setting(

                    "logo",

                    encoded

                )

                st.success(

                    "Logo updated successfully."

                )

                st.rerun()

        current_logo = get_logo()

        if current_logo:

            st.subheader(

                "Current Logo"

            )

            try:

                st.image(

                    base64.b64decode(current_logo),

                    width=220

                )

            except Exception:

                st.error(

                    "Unable to display logo."

                )

    # --------------------------------------------------------

    # Audit

    # --------------------------------------------------------

    with tabs[4]:

        logs = query("""

            SELECT *

            FROM login_logs

            ORDER BY id DESC

            LIMIT 300

        """)

        if logs.empty:

            st.info("No login activity.")

        else:

            st.dataframe(

                logs,

                use_container_width=True,

                hide_index=True

            )

# ============================================================

# NOTIFICATIONS CENTER

# ============================================================

def notifications_center():

    user = st.session_state.user

    page_header(

        "Notifications",

        "System notifications and employee alerts."

    )

    notifications = query("""

        SELECT *

        FROM notifications

        WHERE employee_id = ?

        ORDER BY id DESC

    """, (user["id"],))

    if notifications.empty:

        st.info("No notifications.")

        return

    if st.button(

        "Mark All as Read",

        use_container_width=True

    ):

        execute("""

            UPDATE notifications

            SET is_read = 1

            WHERE employee_id = ?

        """, (user["id"],))

        st.rerun()

    for _, row in notifications.iterrows():

        st.markdown(

            f"""

            <div class="card">

                <b>{safe_text(row['title'])}</b>

                <span class="small-muted">

                    {safe_text(row['created_at'])}

                </span>

                <p>{safe_text(row['message'])}</p>

            </div>

            """,

            unsafe_allow_html=True

        )

# ============================================================

# EMPLOYEE PERFORMANCE CENTER

# ============================================================

def performance_center():

    user = st.session_state.user

    page_header(

        "Performance Center",

        "Employee performance overview."

    )

    if user["role"] == "Admin":

        employees = query("""

            SELECT *

            FROM employees

            WHERE active = 1

            ORDER BY full_name

        """)

        rows = []

        for _, employee in employees.iterrows():

            score = calculate_employee_performance(

                employee["id"]

            )

            rows.append({

                "Employee": employee["full_name"],

                "Code": employee["employee_code"],

                "Role": employee["role"],

                "Performance %": score

            })

        if rows:

            df = pd.DataFrame(rows)

            st.dataframe(

                df,

                use_container_width=True,

                hide_index=True

            )

            fig = px.bar(

                df,

                x="Employee",

                y="Performance %",

                range_y=[0, 100],

                title="Employee Performance"

            )

            fig.update_layout(

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)",

                font_color="#e2e8f0"

            )

            st.plotly_chart(

                fig,

                use_container_width=True

            )

    else:

        score = calculate_employee_performance(

            user["id"]

        )

        kpi(

            "My Performance",

            f"{score}%"

        )

        st.progress(

            score / 100

        )

# ============================================================

# SYSTEM SEARCH

# ============================================================

def global_search():

    page_header(

        "Search",

        "Search companies, contacts, opportunities and projects."

    )

    term = st.text_input(

        "Search",

        placeholder="Type a company, person or opportunity..."

    )

    if not term.strip():

        return

    pattern = f"%{term.strip()}%"

    companies = query("""

        SELECT *

        FROM companies

        WHERE name LIKE ?

        OR industry LIKE ?

        OR website LIKE ?

    """, (

        pattern,

        pattern,

        pattern

    ))

    contacts = query("""

        SELECT *

        FROM contacts

        WHERE name LIKE ?

        OR email LIKE ?

        OR title LIKE ?

    """, (

        pattern,

        pattern,

        pattern

    ))

    opportunities_df = query("""

        SELECT *

        FROM opportunities

        WHERE title LIKE ?

        OR notes LIKE ?

    """, (

        pattern,

        pattern

    ))

    st.subheader("Companies")

    if companies.empty:

        st.caption("No company matches.")

    else:

        st.dataframe(

            companies,

            use_container_width=True,

            hide_index=True

        )

    st.subheader("Contacts")

    if contacts.empty:

        st.caption("No contact matches.")

    else:

        st.dataframe(

            contacts,

            use_container_width=True,

            hide_index=True

        )

    st.subheader("Opportunities")

    if opportunities_df.empty:

        st.caption("No opportunity matches.")

    else:

        st.dataframe(

            opportunities_df,

            use_container_width=True,

            hide_index=True

        )

# ============================================================

# SIDEBAR

# ============================================================

def sidebar():

    user = st.session_state.user

    display_logo()

    st.sidebar.markdown(

        f"""

        <div style="text-align:center;">

            <b>{COMPANY_NAME}</b>

            <br>

            <span class="small-muted">

                Intelligence OS

            </span>

        </div>

        """,

        unsafe_allow_html=True

    )

    st.sidebar.divider()

    st.sidebar.markdown(

        f"**{user['full_name']}**"

    )

    st.sidebar.caption(

        f"{user['employee_code']} • {user['role']}"

    )

    unread = unread_notifications(

        user["id"]

    )

    menu = [

        "Dashboard",

        "My Workspace",

        "Tasks",

        "Internal Chat",

        "CRM",

        "Opportunities",

        "Projects",

        "Performance",

        "Job Descriptions",

        "Email Intelligence",

        "Notifications",

        "Search"

    ]

    if user["role"] == "Admin":

        menu += [

            "Admin Control Center",

            "Governance"

        ]

    selected = st.sidebar.radio(

        "Navigation",

        menu

    )

    st.sidebar.divider()

    st.sidebar.caption(

        f"Notifications: {unread}"

    )

    if st.sidebar.button(

        "Logout",

        use_container_width=True

    ):

        log_event(

            user["id"],

            user["employee_code"],

            "LOGOUT"

        )

        st.session_state.clear()

        st.rerun()

    return selected

# ============================================================

# MAIN

# ============================================================

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

# ============================================================

# ROUTER

# ============================================================

if page == "Dashboard":

    dashboard()

elif page == "My Workspace":

    employee_dashboard()

elif page == "Tasks":

    task_organizer()

elif page == "Internal Chat":

    internal_chat()

elif page == "CRM":

    crm()

elif page == "Opportunities":

    opportunities()

elif page == "Projects":

    projects()

elif page == "Performance":

    performance_center()

elif page == "Job Descriptions":

    job_description_library()

elif page == "Email Intelligence":

    email_assistant()

elif page == "Notifications":

    notifications_center()

elif page == "Search":

    global_search()

elif page == "Admin Control Center":

    admin_center()

elif page == "Governance":

    governance()

# ============================================================

# FOOTER

# ============================================================

st.markdown(

    """

    <div style="

        text-align:center;

        color:#64748b;

        margin-top:50px;

        padding:20px;

        font-size:11px;

    ">

        MASAR Intelligence OS • Internal Business Platform

    </div>

    """,

    unsafe_allow_html=True

)