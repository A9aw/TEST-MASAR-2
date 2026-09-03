import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
import hashlib
import secrets
import os

from bs4 import BeautifulSoup
from datetime import datetime, date
from io import BytesIO
from pathlib import Path

# =========================================================
# MASAR INTELLIGENCE OS V2
# =========================================================

APP_NAME = "MASAR Intelligence OS"
COMPANY_NAME = "MASAR for Consultancy and Business Development"

DB_PATH = "masar_os.db"

UPLOAD_DIR = Path("uploads")
JD_DIR = UPLOAD_DIR / "job_descriptions"

UPLOAD_DIR.mkdir(exist_ok=True)
JD_DIR.mkdir(exist_ok=True)

# =========================================================
# PAGE
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
    df = pd.read_sql_query(
        sql,
        conn,
        params=params
    )
    conn.close()
    return df


# =========================================================
# SECURITY
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db()
    cur = conn.cursor()

    # -----------------------------------------------------
    # EMPLOYEES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CHAT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # JOB DESCRIPTION FILES
    # -----------------------------------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS job_description_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        title TEXT,
        file_name TEXT,
        file_path TEXT,
        file_size INTEGER,
        uploaded_by INTEGER,
        uploaded_at TEXT,
        notes TEXT
    )
    """)

    # -----------------------------------------------------
    # COMPANIES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # OPPORTUNITIES
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CONTACTS
    # -----------------------------------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        name TEXT,
        position TEXT,
        email TEXT,
        phone TEXT,
        relationship TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    # -----------------------------------------------------
    # MEETINGS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # FOLLOWUPS
    # -----------------------------------------------------

    cur.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        title TEXT,
        due_date TEXT,
        priority TEXT,
        status TEXT DEFAULT 'Open',
        owner TEXT,
        notes TEXT
    )
    """)

    # -----------------------------------------------------
    # GOVERNANCE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CREATE DEFAULT ADMIN
    # -----------------------------------------------------

    admins = query(
        "SELECT id FROM employees WHERE role='Admin'"
    )

    if admins.empty:

        admin_pin = "1234"

        execute(
            """
            INSERT INTO employees
            (
                employee_code,
                full_name,
                position,
                email,
                pin_hash,
                role,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ADMIN",
                "MASAR Administrator",
                "System Administrator",
                "",
                hash_password(admin_pin),
                "Admin",
                "Active",
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
            rgba(30,58,138,.10),
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
    border-right:1px solid rgba(56,189,248,.15);
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

.masar-logo {
    font-size:30px;
    font-weight:900;
    color:white;
}

.masar-tag {
    font-size:11px;
    color:#38BDF8;
    letter-spacing:2px;
}

.header {
    padding:20px 0 25px 0;
}

.title {
    font-size:34px;
    font-weight:850;
    color:white;
}

.subtitle {
    color:#38BDF8;
    font-size:12px;
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
    border:1px solid rgba(56,189,248,.13);
    border-radius:18px;
    padding:20px;
    min-height:120px;
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

.chat-message {
    padding:13px 16px;
    border-radius:15px;
    margin:8px 0;
    background:rgba(20,36,58,.85);
    border:1px solid rgba(56,189,248,.08);
}

.chat-me {
    border-left:3px solid #38BDF8;
}

.chat-other {
    border-left:3px solid #64748B;
}

.profile-card {
    background:
        linear-gradient(
            145deg,
            #10243D,
            #0B1E36
        );
    padding:25px;
    border-radius:20px;
    border:1px solid rgba(56,189,248,.12);
}

.score {
    font-size:55px;
    font-weight:900;
    color:#38BDF8;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HELPERS
# =========================================================

def page_header(title, subtitle=""):

    st.markdown(
        f"""
        <div class="header">
            <div class="subtitle">
                {COMPANY_NAME}
            </div>
            <div class="title">
                {title}
            </div>
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


# =========================================================
# LOGIN
# =========================================================

def login_screen():

    st.markdown(
        """
        <div style="
            max-width:520px;
            margin:80px auto;
            text-align:center;
        ">
            <div style="
                font-size:55px;
                font-weight:900;
                color:white;
            ">
                ◈
            </div>

            <div style="
                font-size:34px;
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
                INTELLIGENCE OS
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Secure Login")

    with st.form("login"):

        code = st.text_input(
            "Employee Code",
            placeholder="e.g. EMP001"
        )

        pin = st.text_input(
            "PIN",
            type="password",
            placeholder="Enter your PIN"
        )

        login = st.form_submit_button(
            "SIGN IN",
            use_container_width=True
        )

        if login:

            user = query(
                """
                SELECT *
                FROM employees
                WHERE employee_code=?
                AND status='Active'
                """,
                (code.upper().strip(),)
            )

            if user.empty:

                st.error(
                    "Invalid employee code or account inactive."
                )

            else:

                employee = user.iloc[0]

                if verify_password(
                    pin,
                    employee["pin_hash"]
                ):

                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = int(
                        employee["id"]
                    )
                    st.session_state["user_name"] = employee[
                        "full_name"
                    ]
                    st.session_state["user_role"] = employee[
                        "role"
                    ]
                    st.session_state["employee_code"] = employee[
                        "employee_code"
                    ]

                    st.rerun()

                else:

                    st.error(
                        "Invalid PIN."
                    )


# =========================================================
# ADMIN — EMPLOYEE MANAGEMENT
# =========================================================

def employee_management():

    page_header(
        "Employee Management",
        "Create and manage internal MASAR accounts"
    )

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

    st.markdown("### Create Employee Account")

    with st.form("new_employee"):

        c1, c2 = st.columns(2)

        with c1:

            code = st.text_input(
                "Employee Code *",
                placeholder="EMP001"
            )

            name = st.text_input(
                "Full Name *"
            )

            position = st.text_input(
                "Position"
            )

            email = st.text_input(
                "Email"
            )

        with c2:

            phone = st.text_input(
                "Phone"
            )

            role = st.selectbox(
                "Role",
                [
                    "Employee",
                    "Manager",
                    "Admin"
                ]
            )

            pin = st.text_input(
                "Temporary PIN *",
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
                    "Employee code, name and PIN are required."
                )

            else:

                try:

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
                            code.upper(),
                            name,
                            position,
                            email,
                            phone,
                            hash_password(pin),
                            role,
                            status,
                            datetime.now().isoformat()
                        )
                    )

                    st.success(
                        f"Account created for {name}."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "This employee code already exists."
                    )


# =========================================================
# INTERNAL CHAT
# =========================================================

def internal_chat():

    page_header(
        "MASAR Internal Chat",
        "Private employee-to-employee communication"
    )

    current_user = st.session_state["user_id"]

    employees = query(
        """
        SELECT
            id,
            employee_code,
            full_name,
            position
        FROM employees
        WHERE id != ?
        AND status='Active'
        ORDER BY full_name
        """,
        (current_user,)
    )

    if employees.empty:

        st.info(
            "No other active employees available."
        )

        return

    employee_options = {
        f"{row['full_name']} — {row['position']}":
        int(row["id"])
        for _, row in employees.iterrows()
    }

    selected = st.selectbox(
        "Chat with",
        list(employee_options.keys())
    )

    receiver_id = employee_options[selected]

    # -----------------------------------------------------
    # MESSAGES
    # -----------------------------------------------------

    messages = query(
        """
        SELECT
            m.*,
            e.full_name AS sender_name
        FROM messages m
        LEFT JOIN employees e
        ON m.sender_id=e.id
        WHERE
            (
                sender_id=? AND receiver_id=?
            )
            OR
            (
                sender_id=? AND receiver_id=?
            )
        ORDER BY created_at ASC
        """,
        (
            current_user,
            receiver_id,
            receiver_id,
            current_user
        )
    )

    chat_box = st.container(height=450)

    with chat_box:

        if messages.empty:

            st.info(
                "No messages yet. Start the conversation."
            )

        else:

            for _, msg in messages.iterrows():

                mine = (
                    int(msg["sender_id"])
                    == current_user
                )

                css = (
                    "chat-me"
                    if mine
                    else "chat-other"
                )

                st.markdown(
                    f"""
                    <div class="chat-message {css}">
                        <b>{msg['sender_name']}</b><br>
                        {msg['message']}
                        <div style="
                            font-size:10px;
                            color:#6F849B;
                            margin-top:5px;
                        ">
                            {msg['created_at']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

    with st.form("send_message"):

        message = st.text_input(
            "Message",
            placeholder="Write your message..."
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
                    receiver_id,
                    message.strip(),
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

            st.rerun()


# =========================================================
# JOB DESCRIPTION LIBRARY
# =========================================================

def job_description_library():

    page_header(
        "Job Description Library",
        "Central repository for approved employee job descriptions"
    )

    employees = query(
        """
        SELECT
            id,
            employee_code,
            full_name,
            position
        FROM employees
        ORDER BY full_name
        """
    )

    tab1, tab2 = st.tabs(
        [
            "📁 Document Library",
            "⬆️ Upload Job Description"
        ]
    )

    with tab1:

        files = query(
            """
            SELECT
                j.id,
                j.title,
                j.file_name,
                e.full_name AS employee,
                j.uploaded_at,
                j.file_size,
                j.notes
            FROM job_description_files j
            LEFT JOIN employees e
            ON j.employee_id=e.id
            ORDER BY j.id DESC
            """
        )

        if files.empty:

            st.info(
                "No job description files uploaded yet."
            )

        else:

            st.dataframe(
                files,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### Open Document")

            selected_file = st.selectbox(
                "Select document",
                files["id"].tolist()
            )

            row = files[
                files["id"] == selected_file
            ].iloc[0]

            path = Path(
                row["file_path"]
            )

            if path.exists():

                with open(
                    path,
                    "rb"
                ) as f:

                    st.download_button(
                        "Download Word File",
                        data=f.read(),
                        file_name=row["file_name"],
                        mime=(
                            "application/vnd.openxmlformats-"
                            "officedocument.wordprocessingml.document"
                        )
                    )

    with tab2:

        if st.session_state["user_role"] != "Admin":

            st.warning(
                "Only administrators can upload job descriptions."
            )

        else:

            with st.form(
                "upload_jd",
                clear_on_submit=True
            ):

                title = st.text_input(
                    "Document Title"
                )

                employee = st.selectbox(
                    "Assigned Employee",
                    ["General / Not Assigned"] +
                    employees["full_name"].tolist()
                )

                uploaded = st.file_uploader(
                    "Upload Word Job Description",
                    type=["docx"]
                )

                notes = st.text_area(
                    "Notes"
                )

                submit = st.form_submit_button(
                    "UPLOAD DOCUMENT"
                )

                if submit:

                    if uploaded is None:

                        st.error(
                            "Please upload a Word document."
                        )

                    else:

                        safe_name = (
                            uploaded.name
                            .replace("/", "_")
                            .replace("\\", "_")
                        )

                        unique_name = (
                            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            f"_{safe_name}"
                        )

                        path = JD_DIR / unique_name

                        with open(
                            path,
                            "wb"
                        ) as f:

                            f.write(
                                uploaded.getbuffer()
                            )

                        employee_id = None

                        if employee != "General / Not Assigned":

                            employee_id = int(
                                employees[
                                    employees["full_name"]
                                    == employee
                                ]["id"].iloc[0]
                            )

                        execute(
                            """
                            INSERT INTO job_description_files
                            (
                                employee_id,
                                title,
                                file_name,
                                file_path,
                                file_size,
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
                                str(path),
                                uploaded.size,
                                st.session_state[
                                    "user_id"
                                ],
                                datetime.now().isoformat(),
                                notes
                            )
                        )

                        st.success(
                            "Job description uploaded successfully."
                        )

                        st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    page_header(
        "Executive Dashboard",
        "MASAR business development command center"
    )

    companies = query(
        "SELECT * FROM companies"
    )

    opportunities = query(
        "SELECT * FROM opportunities"
    )

    followups = query(
        "SELECT * FROM followups"
    )

    employees = query(
        "SELECT * FROM employees"
    )

    pipeline = (
        opportunities["value"].sum()
        if not opportunities.empty
        else 0
    )

    weighted = (
        (
            opportunities["value"]
            *
            opportunities["probability"]
            / 100
        ).sum()
        if not opportunities.empty
        else 0
    )

    today = date.today().isoformat()

    overdue = 0

    if not followups.empty:

        overdue = len(
            followups[
                (followups["status"] == "Open")
                &
                (followups["due_date"] < today)
            ]
        )

    c1,c2,c3,c4,c5 = st.columns(5)

    with c1:
        kpi(
            "Companies",
            len(companies),
            "CRM accounts"
        )

    with c2:
        kpi(
            "Employees",
            len(employees),
            "Active internal users"
        )

    with c3:
        kpi(
            "Pipeline",
            f"{pipeline:,.0f}",
            "Total opportunity value"
        )

    with c4:
        kpi(
            "Weighted Pipeline",
            f"{weighted:,.0f}",
            "Probability adjusted"
        )

    with c5:
        kpi(
            "Overdue",
            overdue,
            "Action required"
        )

    st.write("")

    if not opportunities.empty:

        left,right = st.columns(2)

        with left:

            data = (
                opportunities
                .groupby("stage")["value"]
                .sum()
                .reset_index()
            )

            fig = px.bar(
                data,
                x="stage",
                y="value",
                text_auto=True
            )

            fig.update_layout(
                template="plotly_dark"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        with right:

            data = (
                opportunities
                .groupby("service")["value"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                data,
                names="service",
                values="value"
            )

            fig.update_layout(
                template="plotly_dark"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    st.markdown("### Recent Follow-ups")

    if not followups.empty:

        st.dataframe(
            followups
            .sort_values("due_date")
            .head(10),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No follow-ups yet."
        )


# =========================================================
# CRM
# =========================================================

def crm():

    page_header(
        "CRM & Companies",
        "Strategic account management"
    )

    companies = query(
        "SELECT * FROM companies ORDER BY id DESC"
    )

    tab1,tab2 = st.tabs(
        [
            "Companies",
            "Add Company"
        ]
    )

    with tab1:

        search = st.text_input(
            "Search"
        )

        if search:

            companies = companies[
                companies["name"]
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        st.dataframe(
            companies,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form("company"):

            name = st.text_input(
                "Company Name"
            )

            website = st.text_input(
                "Website"
            )

            c1,c2 = st.columns(2)

            with c1:

                industry = st.text_input(
                    "Industry"
                )

                country = st.text_input(
                    "Country"
                )

            with c2:

                size = st.selectbox(
                    "Size",
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

            if submit:

                if name.strip():

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


# =========================================================
# INTELLIGENCE CENTER
# =========================================================

def intelligence():

    page_header(
        "Intelligence Center",
        "Research companies and identify MASAR opportunities"
    )

    url = st.text_input(
        "Company Website",
        placeholder="https://www.example.com"
    )

    if st.button(
        "RUN INTELLIGENCE SCAN",
        type="primary"
    ):

        if not url:

            st.warning(
                "Enter a website."
            )

        else:

            try:

                if not url.startswith("http"):
                    url = "https://" + url

                headers = {
                    "User-Agent":
                    "Mozilla/5.0 MASAR Intelligence OS"
                }

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=15
                )

                response.raise_for_status()

                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                for element in soup(
                    ["script","style","noscript"]
                ):
                    element.decompose()

                title = (
                    soup.title.get_text(
                        strip=True
                    )
                    if soup.title
                    else ""
                )

                meta = soup.find(
                    "meta",
                    attrs={"name":"description"}
                )

                description = (
                    meta.get("content","")
                    if meta
                    else ""
                )

                text = soup.get_text(
                    " ",
                    strip=True
                )

                st.session_state[
                    "intel"
                ] = {
                    "title": title,
                    "description": description,
                    "text": text[:30000]
                }

                st.success(
                    "Intelligence scan completed."
                )

            except Exception:

                st.error(
                    "Unable to access this website."
                )

    if "intel" in st.session_state:

        intel = st.session_state["intel"]

        st.markdown(
            f"## {intel['title']}"
        )

        if intel["description"]:

            st.info(
                intel["description"]
            )

        tab1,tab2,tab3 = st.tabs(
            [
                "Snapshot",
                "Extracted Information",
                "MASAR Analysis"
            ]
        )

        with tab1:

            st.write(
                "Website intelligence successfully collected."
            )

        with tab2:

            st.text_area(
                "Website Content",
                intel["text"],
                height=500
            )

        with tab3:

            st.markdown("""
### MASAR Opportunity Areas

#### Government Affairs
- Government relations
- Regulatory engagement
- Stakeholder management
- Public-sector access

#### Public Relations
- Corporate reputation
- Media relations
- Strategic communications
- Crisis communications

#### Business Development
- Strategic partnerships
- Market entry
- Commercial expansion
- Institutional relationships
            """)


# =========================================================
# OPPORTUNITIES
# =========================================================

def opportunities():

    page_header(
        "Opportunities",
        "Manage the MASAR commercial pipeline"
    )

    df = query("""
        SELECT
            o.id,
            c.name AS company,
            o.title,
            o.service,
            o.stage,
            o.value,
            o.probability,
            o.next_action,
            o.next_action_date
        FROM opportunities o
        LEFT JOIN companies c
        ON o.company_id=c.id
        ORDER BY o.id DESC
    """)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Add Opportunity")

    companies = query(
        "SELECT id,name FROM companies ORDER BY name"
    )

    if companies.empty:

        st.warning(
            "Add companies first."
        )

        return

    company_map = dict(
        zip(
            companies["name"],
            companies["id"]
        )
    )

    with st.form("opportunity"):

        company = st.selectbox(
            "Company",
            list(company_map.keys())
        )

        title = st.text_input(
            "Opportunity"
        )

        service = st.selectbox(
            "Service",
            [
                "Government Affairs",
                "Public Relations",
                "Business Development",
                "Strategic Advisory",
                "Market Entry",
                "Stakeholder Management"
            ]
        )

        stage = st.selectbox(
            "Stage",
            [
                "Lead",
                "Qualified",
                "Meeting",
                "Proposal",
                "Negotiation",
                "Won",
                "Lost"
            ]
        )

        value = st.number_input(
            "Estimated Value",
            min_value=0.0,
            step=1000.0
        )

        probability = st.slider(
            "Probability",
            0,
            100,
            25
        )

        next_action = st.text_input(
            "Next Action"
        )

        next_date = st.date_input(
            "Next Action Date"
        )

        submit = st.form_submit_button(
            "CREATE"
        )

        if submit:

            execute(
                """
                INSERT INTO opportunities
                (
                    company_id,
                    title,
                    service,
                    stage,
                    value,
                    probability,
                    next_action,
                    next_action_date,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_map[company],
                    title,
                    service,
                    stage,
                    value,
                    probability,
                    next_action,
                    next_date.isoformat(),
                    datetime.now().isoformat()
                )
            )

            st.success(
                "Opportunity created."
            )

            st.rerun()


# =========================================================
# GOVERNANCE
# =========================================================

def governance():

    page_header(
        "Governance",
        "Policies, procedures and organizational documentation"
    )

    df = query(
        """
        SELECT
            id,
            category,
            title,
            review_date,
            status
        FROM governance
        ORDER BY id DESC
        """
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if st.session_state["user_role"] == "Admin":

        st.markdown("### Add Document")

        with st.form("governance"):

            category = st.selectbox(
                "Type",
                [
                    "Policy",
                    "Procedure",
                    "Governance",
                    "Other"
                ]
            )

            title = st.text_input(
                "Title"
            )

            review = st.date_input(
                "Review Date"
            )

            content = st.text_area(
                "Content",
                height=300
            )

            submit = st.form_submit_button(
                "SAVE"
            )

            if submit:

                execute(
                    """
                    INSERT INTO governance
                    (
                        category,
                        title,
                        content,
                        review_date,
                        status
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        category,
                        title,
                        content,
                        review.isoformat(),
                        "Active"
                    )
                )

                st.success(
                    "Saved."
                )

                st.rerun()


# =========================================================
# LOGOUT
# =========================================================

def logout():

    st.session_state.clear()

    st.rerun()


# =========================================================
# AUTHENTICATION
# =========================================================

if "authenticated" not in st.session_state:

    st.session_state["authenticated"] = False


if not st.session_state["authenticated"]:

    login_screen()

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding:10px 0 25px;">
            <div class="masar-logo">
                ◈ MASAR
            </div>
            <div class="masar-tag">
                INTELLIGENCE OS
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="profile-card">
            <b>
                {st.session_state['user_name']}
            </b>
            <br>
            <span style="color:#38BDF8;">
                {st.session_state['user_role']}
            </span>
            <br>
            <small>
                {st.session_state['employee_code']}
            </small>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    pages = [
        "🏠 Dashboard",
        "🏢 CRM & Companies",
        "💼 Opportunities",
        "💬 Internal Chat",
        "📁 Job Descriptions",
        "🧠 Intelligence Center",
        "⚖️ Governance"
    ]

    if st.session_state["user_role"] == "Admin":

        pages.insert(
            5,
            "👑 Employee Management"
        )

    page = st.radio(
        "Navigation",
        pages
    )

    st.markdown("---")

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()


# =========================================================
# ROUTING
# =========================================================

if page == "🏠 Dashboard":

    dashboard()

elif page == "🏢 CRM & Companies":

    crm()

elif page == "💼 Opportunities":

    opportunities()

elif page == "💬 Internal Chat":

    internal_chat()

elif page == "📁 Job Descriptions":

    job_description_library()

elif page == "🧠 Intelligence Center":

    intelligence()

elif page == "⚖️ Governance":

    governance()

elif page == "👑 Employee Management":

    employee_management()