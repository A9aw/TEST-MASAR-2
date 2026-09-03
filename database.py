import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "data/masar_os.db"


def get_db():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def hash_pin(pin):
    return hashlib.sha256(str(pin).encode()).hexdigest()


def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(sql, params)

    conn.commit()

    result = cur.lastrowid

    conn.close()

    return result


def query(sql, params=()):
    import pandas as pd

    conn = get_db()

    df = pd.read_sql_query(
        sql,
        conn,
        params=params
    )

    conn.close()

    return df


def init_database():

    conn = get_db()
    cur = conn.cursor()

    # =====================================================
    # EMPLOYEES
    # =====================================================

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

        created_at TEXT,

        updated_at TEXT

    )
    """)

    # =====================================================
    # LOGIN AUDIT
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER,

        employee_code TEXT,

        login_time TEXT,

        ip_address TEXT,

        device TEXT,

        status TEXT

    )
    """)

    # =====================================================
    # PASSWORD RESET
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        employee_id INTEGER,

        reset_code TEXT,

        created_at TEXT,

        expires_at TEXT,

        used INTEGER DEFAULT 0

    )
    """)

    # =====================================================
    # MESSAGES
    # =====================================================

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

    # =====================================================
    # TASKS
    # =====================================================

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

    # =====================================================
    # PERFORMANCE
    # =====================================================

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

    # =====================================================
    # JOB DESCRIPTIONS
    # =====================================================

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

    # =====================================================
    # EMAILS
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS emails (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        message_uid TEXT UNIQUE,

        sender TEXT,

        recipient TEXT,

        subject TEXT,

        body TEXT,

        received_at TEXT,

        summary TEXT,

        category TEXT,

        priority TEXT DEFAULT 'Normal',

        is_read INTEGER DEFAULT 0,

        ai_processed INTEGER DEFAULT 0

    )
    """)

    # =====================================================
    # COMPANIES
    # =====================================================

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

    # =====================================================
    # OPPORTUNITIES
    # =====================================================

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

    # =====================================================
    # PROJECTS
    # =====================================================

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

    # =====================================================
    # GOVERNANCE
    # =====================================================

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
    # SETTINGS
    # =====================================================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (

        key TEXT PRIMARY KEY,

        value TEXT

    )
    """)

    conn.commit()

    conn.close()

    create_default_admin()


def create_default_admin():

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
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                datetime.now().isoformat()
            )
        )