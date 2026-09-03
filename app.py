import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from io import BytesIO
from pathlib import Path

# =========================================================
# MASAR INTELLIGENCE OS
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
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

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


init_db()

# =========================================================
# DATABASE HELPERS
# =========================================================

def query(sql, params=()):
    conn = get_db()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(56,189,248,0.06), transparent 25%),
        radial-gradient(circle at 90% 10%, rgba(30,58,138,0.08), transparent 25%),
        #0B1220;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07111F 0%, #0B1E36 100%);
    border-right: 1px solid rgba(56,189,248,0.15);
}

section[data-testid="stSidebar"] * {
    color: #E5EEF8;
}

h1, h2, h3 {
    color: #F5F9FF !important;
}

p, label {
    color: #B7C5D6 !important;
}

.masar-header {
    padding: 20px 0 25px 0;
}

.masar-title {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #FFFFFF;
}

.masar-subtitle {
    color: #7DD3FC;
    font-size: 14px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.kpi {
    background: linear-gradient(
        145deg,
        rgba(20,36,58,0.96),
        rgba(10,25,43,0.96)
    );
    border: 1px solid rgba(56,189,248,0.13);
    border-radius: 18px;
    padding: 20px;
    min-height: 125px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.20);
}

.kpi-label {
    font-size: 12px;
    color: #8FA6BF;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.kpi-value {
    font-size: 32px;
    font-weight: 800;
    color: #FFFFFF;
    margin-top: 8px;
}

.kpi-small {
    font-size: 12px;
    color: #38BDF8;
    margin-top: 5px;
}

.card {
    background: rgba(15,31,51,0.82);
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
}

.section-title {
    font-size: 19px;
    font-weight: 750;
    color: white;
    margin-bottom: 12px;
}

.score {
    font-size: 52px;
    font-weight: 900;
    color: #38BDF8;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 20px;
    background: rgba(56,189,248,0.12);
    color: #7DD3FC;
    font-size: 12px;
}

div[data-testid="stMetric"] {
    background: rgba(15,31,51,0.82);
    padding: 15px;
    border-radius: 16px;
    border: 1px solid rgba(56,189,248,0.10);
}

.stButton > button {
    border-radius: 10px;
    border: 1px solid rgba(56,189,248,0.25);
    background: linear-gradient(135deg, #0B1E36, #12345A);
    color: white;
    font-weight: 650;
}

.stButton > button:hover {
    border-color: #38BDF8;
    color: #7DD3FC;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# UI HELPERS
# =========================================================

def header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="masar-header">
            <div class="masar-subtitle">{COMPANY_NAME}</div>
            <div class="masar-title">{title}</div>
            <div style="color:#8295AA;margin-top:5px;">
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
            <div class="kpi-small">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding:15px 5px 25px 5px;">
            <div style="font-size:30px;font-weight:900;color:white;">
                ◈ MASAR
            </div>
            <div style="font-size:11px;color:#38BDF8;letter-spacing:2px;">
                INTELLIGENCE OS
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigation",
        [
            "Executive Dashboard",
            "CRM & Companies",
            "Opportunities",
            "Contacts",
            "Meetings",
            "Follow-ups",
            "Intelligence Center",
            "Analytics",
            "Report Factory",
            "Governance"
        ]
    )

    st.markdown("---")

    st.caption("MASAR Business Development System")
    st.caption("Version 1.0")


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    header(
        "Executive Dashboard",
        "Business development command center"
    )

    companies = query("SELECT * FROM companies")
    opportunities = query("SELECT * FROM opportunities")
    followups = query("SELECT * FROM followups")

    total_companies = len(companies)

    active_opps = len(
        opportunities[
            ~opportunities["stage"].isin(["Won", "Lost"])
        ]
    ) if not opportunities.empty else 0

    pipeline = (
        opportunities["value"].sum()
        if not opportunities.empty else 0
    )

    weighted = (
        (opportunities["value"] *
         opportunities["probability"] / 100).sum()
        if not opportunities.empty else 0
    )

    today = date.today().isoformat()

    overdue = len(
        followups[
            (followups["status"] == "Open") &
            (followups["due_date"] < today)
        ]
    ) if not followups.empty else 0

    won = len(
        opportunities[
            opportunities["stage"] == "Won"
        ]
    ) if not opportunities.empty else 0

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        kpi("Companies", total_companies, "CRM accounts")

    with c2:
        kpi("Active Opportunities", active_opps, "Open pipeline")

    with c3:
        kpi("Pipeline Value", f"{pipeline:,.0f}", "Total opportunity value")

    with c4:
        kpi("Weighted Pipeline", f"{weighted:,.0f}", "Probability adjusted")

    with c5:
        kpi("Overdue", overdue, "Follow-ups requiring action")

    st.write("")

    left, right = st.columns(2)

    with left:

        st.markdown(
            '<div class="section-title">Pipeline by Stage</div>',
            unsafe_allow_html=True
        )

        if not opportunities.empty:

            stage_data = (
                opportunities
                .groupby("stage")["value"]
                .sum()
                .reset_index()
            )

            fig = px.bar(
                stage_data,
                x="stage",
                y="value",
                text_auto=True
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10,r=10,t=20,b=10)
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.info("No opportunities yet.")

    with right:

        st.markdown(
            '<div class="section-title">Opportunity Funnel</div>',
            unsafe_allow_html=True
        )

        if not opportunities.empty:

            funnel = (
                opportunities
                .groupby("stage")
                .size()
                .reset_index(name="count")
            )

            fig = px.funnel(
                funnel,
                y="stage",
                x="count"
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        else:
            st.info("No funnel data.")

    st.markdown(
        '<div class="section-title">Priority Actions</div>',
        unsafe_allow_html=True
    )

    if not followups.empty:

        priority = followups[
            followups["status"] == "Open"
        ].copy()

        if not priority.empty:

            priority["due_date"] = pd.to_datetime(
                priority["due_date"],
                errors="coerce"
            )

            priority = priority.sort_values("due_date")

            st.dataframe(
                priority[
                    [
                        "title",
                        "due_date",
                        "priority",
                        "owner"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

        else:
            st.success("No open follow-ups.")

    else:
        st.info("No follow-ups yet.")


# =========================================================
# CRM
# =========================================================

def crm():

    header(
        "CRM & Companies",
        "Manage target accounts, prospects and strategic relationships"
    )

    tab1, tab2 = st.tabs(
        ["Company Database", "Add Company"]
    )

    with tab1:

        df = query("""
            SELECT
                c.id,
                c.name,
                c.industry,
                c.country,
                c.status,
                c.website,
                c.size
            FROM companies c
            ORDER BY c.id DESC
        """)

        search = st.text_input(
            "Search companies",
            placeholder="Company name, industry or country..."
        )

        if search:

            mask = (
                df["name"].str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                df["industry"].str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                df["country"].str.contains(
                    search,
                    case=False,
                    na=False
                )
            )

            df = df[mask]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download CRM Excel",
            data=excel_download(df),
            file_name="MASAR_CRM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tab2:

        with st.form("company_form"):

            name = st.text_input("Company Name *")

            website = st.text_input(
                "Website",
                placeholder="https://example.com"
            )

            c1, c2 = st.columns(2)

            with c1:
                industry = st.text_input("Industry")
                country = st.text_input("Country")

            with c2:
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
                "Add Company"
            )

            if submit:

                if not name.strip():

                    st.error("Company name is required.")

                else:

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
                        f"{name} added successfully."
                    )

                    st.rerun()


# =========================================================
# OPPORTUNITIES
# =========================================================

def opportunities():

    header(
        "Opportunities & Pipeline",
        "Track commercial opportunities from prospecting to closure"
    )

    companies = query(
        "SELECT id, name FROM companies ORDER BY name"
    )

    tab1, tab2 = st.tabs(
        ["Pipeline", "New Opportunity"]
    )

    with tab1:

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
            ON o.company_id = c.id
            ORDER BY o.id DESC
        """)

        if not df.empty:

            df["weighted_value"] = (
                df["value"] *
                df["probability"] / 100
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Export Pipeline",
                data=excel_download(df),
                file_name="MASAR_Pipeline.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:

            st.info(
                "No opportunities available."
            )

    with tab2:

        if companies.empty:

            st.warning(
                "Add a company first."
            )

        else:

            company_map = dict(
                zip(
                    companies["name"],
                    companies["id"]
                )
            )

            with st.form("opportunity_form"):

                company_name = st.selectbox(
                    "Company",
                    list(company_map.keys())
                )

                title = st.text_input(
                    "Opportunity Title"
                )

                service = st.selectbox(
                    "MASAR Service",
                    [
                        "Government Affairs",
                        "Public Relations",
                        "Business Development",
                        "Strategic Advisory",
                        "Market Entry",
                        "Stakeholder Management",
                        "Government Relations",
                        "Other"
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

                c1, c2, c3 = st.columns(3)

                with c1:
                    value = st.number_input(
                        "Estimated Value",
                        min_value=0.0,
                        step=1000.0
                    )

                with c2:
                    probability = st.slider(
                        "Probability %",
                        0,
                        100,
                        25
                    )

                with c3:
                    action_date = st.date_input(
                        "Next Action Date"
                    )

                next_action = st.text_input(
                    "Next Action"
                )

                notes = st.text_area(
                    "Notes"
                )

                submit = st.form_submit_button(
                    "Create Opportunity"
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
                            notes,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            company_map[company_name],
                            title,
                            service,
                            stage,
                            value,
                            probability,
                            next_action,
                            action_date.isoformat(),
                            notes,
                            datetime.now().isoformat()
                        )
                    )

                    st.success(
                        "Opportunity created."
                    )

                    st.rerun()


# =========================================================
# CONTACTS
# =========================================================

def contacts():

    header(
        "Contacts & Relationships",
        "Build relationship intelligence around strategic accounts"
    )

    companies = query(
        "SELECT id, name FROM companies ORDER BY name"
    )

    tab1, tab2 = st.tabs(
        ["Contacts", "Add Contact"]
    )

    with tab1:

        df = query("""
            SELECT
                ct.id,
                c.name AS company,
                ct.name,
                ct.position,
                ct.email,
                ct.phone,
                ct.relationship
            FROM contacts ct
            LEFT JOIN companies c
            ON ct.company_id = c.id
            ORDER BY ct.id DESC
        """)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        if companies.empty:

            st.warning(
                "Add a company first."
            )

        else:

            company_map = dict(
                zip(
                    companies["name"],
                    companies["id"]
                )
            )

            with st.form("contact_form"):

                company = st.selectbox(
                    "Company",
                    list(company_map.keys())
                )

                name = st.text_input(
                    "Contact Name"
                )

                position = st.text_input(
                    "Position / Title"
                )

                c1, c2 = st.columns(2)

                with c1:
                    email = st.text_input(
                        "Email"
                    )

                with c2:
                    phone = st.text_input(
                        "Phone"
                    )

                relationship = st.selectbox(
                    "Relationship",
                    [
                        "Cold",
                        "Introduced",
                        "Developing",
                        "Strong",
                        "Strategic",
                        "Client"
                    ]
                )

                notes = st.text_area(
                    "Relationship Notes"
                )

                submit = st.form_submit_button(
                    "Add Contact"
                )

                if submit:

                    execute(
                        """
                        INSERT INTO contacts
                        (
                            company_id,
                            name,
                            position,
                            email,
                            phone,
                            relationship,
                            notes,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            company_map[company],
                            name,
                            position,
                            email,
                            phone,
                            relationship,
                            notes,
                            datetime.now().isoformat()
                        )
                    )

                    st.success(
                        "Contact added."
                    )

                    st.rerun()


# =========================================================
# MEETINGS
# =========================================================

def meetings():

    header(
        "Meetings",
        "Capture meeting outcomes, intelligence and next actions"
    )

    companies = query(
        "SELECT id, name FROM companies ORDER BY name"
    )

    tab1, tab2 = st.tabs(
        ["Meeting Log", "Add Meeting"]
    )

    with tab1:

        df = query("""
            SELECT
                m.id,
                c.name AS company,
                m.title,
                m.meeting_date,
                m.attendees,
                m.outcome,
                m.next_steps
            FROM meetings m
            LEFT JOIN companies c
            ON m.company_id = c.id
            ORDER BY m.meeting_date DESC
        """)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        if companies.empty:

            st.warning(
                "Add a company first."
            )

        else:

            company_map = dict(
                zip(
                    companies["name"],
                    companies["id"]
                )
            )

            with st.form("meeting_form"):

                company = st.selectbox(
                    "Company",
                    list(company_map.keys())
                )

                title = st.text_input(
                    "Meeting Title"
                )

                meeting_date = st.date_input(
                    "Meeting Date"
                )

                attendees = st.text_input(
                    "Attendees"
                )

                outcome = st.text_area(
                    "Meeting Outcome"
                )

                next_steps = st.text_area(
                    "Next Steps"
                )

                notes = st.text_area(
                    "Additional Intelligence"
                )

                submit = st.form_submit_button(
                    "Save Meeting"
                )

                if submit:

                    execute(
                        """
                        INSERT INTO meetings
                        (
                            company_id,
                            title,
                            meeting_date,
                            attendees,
                            outcome,
                            next_steps,
                            notes
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            company_map[company],
                            title,
                            meeting_date.isoformat(),
                            attendees,
                            outcome,
                            next_steps,
                            notes
                        )
                    )

                    st.success(
                        "Meeting saved."
                    )

                    st.rerun()


# =========================================================
# FOLLOW UPS
# =========================================================

def followups():

    header(
        "Follow-ups & Actions",
        "Never lose a strategic follow-up"
    )

    companies = query(
        "SELECT id, name FROM companies ORDER BY name"
    )

    df = query("""
        SELECT
            f.id,
            c.name AS company,
            f.title,
            f.due_date,
            f.priority,
            f.status,
            f.owner
        FROM followups f
        LEFT JOIN companies c
        ON f.company_id = c.id
        ORDER BY f.due_date
    """)

    today = date.today().isoformat()

    if not df.empty:

        overdue_count = len(
            df[
                (df["status"] == "Open") &
                (df["due_date"] < today)
            ]
        )

        if overdue_count > 0:

            st.error(
                f"⚠️ {overdue_count} follow-up(s) are overdue."
            )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    st.markdown(
        "### Add Follow-up"
    )

    if companies.empty:

        st.warning(
            "Add a company first."
        )

    else:

        company_map = dict(
            zip(
                companies["name"],
                companies["id"]
            )
        )

        with st.form("followup_form"):

            company = st.selectbox(
                "Company",
                list(company_map.keys())
            )

            title = st.text_input(
                "Action"
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                due = st.date_input(
                    "Due Date"
                )

            with c2:
                priority = st.selectbox(
                    "Priority",
                    [
                        "Low",
                        "Medium",
                        "High",
                        "Critical"
                    ]
                )

            with c3:
                owner = st.text_input(
                    "Owner"
                )

            notes = st.text_area(
                "Notes"
            )

            submit = st.form_submit_button(
                "Create Follow-up"
            )

            if submit:

                execute(
                    """
                    INSERT INTO followups
                    (
                        company_id,
                        title,
                        due_date,
                        priority,
                        status,
                        owner,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        company_map[company],
                        title,
                        due.isoformat(),
                        priority,
                        "Open",
                        owner,
                        notes
                    )
                )

                st.success(
                    "Follow-up created."
                )

                st.rerun()


# =========================================================
# WEBSITE INTELLIGENCE
# =========================================================

def fetch_website(url):

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
        ["script", "style", "noscript"]
    ):
        element.decompose()

    title = (
        soup.title.get_text(strip=True)
        if soup.title
        else ""
    )

    description = ""

    meta = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta:
        description = meta.get(
            "content",
            ""
        )

    text = soup.get_text(
        " ",
        strip=True
    )

    return {
        "title": title,
        "description": description,
        "text": text[:30000],
        "url": url
    }


def calculate_score(
    strategic_fit,
    market_potential,
    relationship_strength,
    urgency,
    accessibility
):

    return round(
        (
            strategic_fit +
            market_potential +
            relationship_strength +
            urgency +
            accessibility
        ) / 5
    )


# =========================================================
# INTELLIGENCE CENTER
# =========================================================

def intelligence():

    header(
        "Intelligence Center",
        "Turn company information into actionable MASAR opportunities"
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Company Intelligence",
            "Opportunity Scoring",
            "Meeting Brief"
        ]
    )

    with tab1:

        st.markdown(
            """
            <div class="card">
                <div class="section-title">
                    🌐 Website Intelligence
                </div>
                Enter a company's website and extract
                its publicly visible information.
            </div>
            """,
            unsafe_allow_html=True
        )

        url = st.text_input(
            "Company Website",
            placeholder="https://www.example.com"
        )

        if st.button(
            "Run Intelligence Scan",
            type="primary"
        ):

            if not url:

                st.warning(
                    "Enter a website first."
                )

            else:

                try:

                    with st.spinner(
                        "Scanning public website..."
                    ):

                        result = fetch_website(
                            url
                        )

                    st.session_state[
                        "intel_result"
                    ] = result

                    st.success(
                        "Website intelligence collected."
                    )

                except Exception as e:

                    st.error(
                        "Unable to read this website. "
                        "The site may block automated requests."
                    )

        if "intel_result" in st.session_state:

            result = st.session_state[
                "intel_result"
            ]

            st.markdown(
                f"""
                <div class="card">
                    <div class="section-title">
                        {result["title"]}
                    </div>
                    <div class="badge">
                        {result["url"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            t1, t2, t3, t4 = st.tabs(
                [
                    "Snapshot",
                    "Website Description",
                    "Raw Intelligence",
                    "MASAR Analysis"
                ]
            )

            with t1:

                st.write(
                    result["title"]
                )

                if result["description"]:

                    st.info(
                        result["description"]
                    )

            with t2:

                st.write(
                    result["description"]
                    or "No meta description found."
                )

            with t3:

                st.text_area(
                    "Extracted website content",
                    result["text"],
                    height=400
                )

            with t4:

                st.markdown(
                    """
                    ### MASAR Strategic Analysis

                    Use the extracted intelligence to evaluate:

                    **Government Affairs**
                    - Regulatory exposure
                    - Government stakeholders
                    - Public-sector opportunities
                    - Market-entry requirements

                    **Public Relations**
                    - Reputation positioning
                    - Media opportunities
                    - Stakeholder communication

                    **Business Development**
                    - Strategic partnerships
                    - New market opportunities
                    - Institutional relationships
                    - Commercial expansion
                    """
                )

    with tab2:

        st.markdown(
            "### MASAR Opportunity Score"
        )

        st.caption(
            "This is a strategic heuristic, not an objective valuation."
        )

        c1, c2 = st.columns(2)

        with c1:

            strategic_fit = st.slider(
                "Strategic Fit",
                0,
                100,
                70
            )

            market_potential = st.slider(
                "Market Potential",
                0,
                100,
                70
            )

            relationship_strength = st.slider(
                "Relationship Strength",
                0,
                100,
                50
            )

        with c2:

            urgency = st.slider(
                "Urgency",
                0,
                100,
                50
            )

            accessibility = st.slider(
                "Accessibility",
                0,
                100,
                60
            )

            score = calculate_score(
                strategic_fit,
                market_potential,
                relationship_strength,
                urgency,
                accessibility
            )

        st.markdown(
            f"""
            <div class="card" style="text-align:center;">
                <div style="color:#8FA6BF;">
                    MASAR OPPORTUNITY SCORE
                </div>
                <div class="score">
                    {score}/100
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if score >= 80:

            st.success(
                "🔥 High-priority strategic opportunity."
            )

        elif score >= 60:

            st.info(
                "Promising opportunity requiring further qualification."
            )

        else:

            st.warning(
                "Low current priority. Monitor or develop relationship."
            )

    with tab3:

        st.markdown(
            "### Meeting Brief Generator"
        )

        company = st.text_input(
            "Company"
        )

        objective = st.text_area(
            "Meeting Objective"
        )

        context = st.text_area(
            "Known Context"
        )

        if st.button(
            "Generate Meeting Brief"
        ):

            brief = f"""
MASAR MEETING BRIEF
===================

Company:
{company}

Meeting Objective:
{objective}

Known Context:
{context}

KEY QUESTIONS
-------------
1. What are the company's current strategic priorities?
2. What government or regulatory challenges are they facing?
3. What markets are they targeting?
4. Which stakeholders influence their success?
5. Where can MASAR create measurable value?

MASAR POSITIONING
-----------------
Government Affairs
Public Relations
Business Development
Strategic Advisory
Stakeholder Management

NEXT STEP
---------
Define a clear commercial or strategic next action.
"""

            st.text_area(
                "Meeting Brief",
                brief,
                height=450
            )


# =========================================================
# ANALYTICS
# =========================================================

def analytics():

    header(
        "Business Analytics",
        "Management intelligence across the MASAR pipeline"
    )

    companies = query(
        "SELECT * FROM companies"
    )

    opportunities = query(
        "SELECT * FROM opportunities"
    )

    contacts_df = query(
        "SELECT * FROM contacts"
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi(
            "Accounts",
            len(companies)
        )

    with c2:
        kpi(
            "Contacts",
            len(contacts_df)
        )

    with c3:
        kpi(
            "Opportunities",
            len(opportunities)
        )

    if not opportunities.empty:

        st.markdown(
            "### Revenue Potential"
        )

        a, b = st.columns(2)

        with a:

            stage = (
                opportunities
                .groupby("stage")["value"]
                .sum()
                .reset_index()
            )

            fig = px.bar(
                stage,
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

        with b:

            service = (
                opportunities
                .groupby("service")["value"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                service,
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

    else:

        st.info(
            "Add opportunities to unlock analytics."
        )


# =========================================================
# REPORT GENERATOR
# =========================================================

def generate_docx(
    company_name,
    content
):

    from docx import Document

    doc = Document()

    doc.add_heading(
        "MASAR",
        0
    )

    doc.add_paragraph(
        COMPANY_NAME
    )

    doc.add_heading(
        company_name,
        1
    )

    for section, text in content.items():

        doc.add_heading(
            section,
            2
        )

        doc.add_paragraph(
            text
        )

    buffer = BytesIO()

    doc.save(buffer)

    buffer.seek(0)

    return buffer


def generate_pdf(
    company_name,
    content
):

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer
    )

    from reportlab.lib.styles import getSampleStyleSheet

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "MASAR",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            COMPANY_NAME,
            styles["Normal"]
        )
    )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            company_name,
            styles["Heading1"]
        )
    )

    for section, text in content.items():

        story.append(
            Paragraph(
                section,
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                text.replace("\n", "<br/>"),
                styles["BodyText"]
            )
        )

        story.append(
            Spacer(1, 10)
        )

    doc.build(story)

    buffer.seek(0)

    return buffer


def report_factory():

    header(
        "Report Factory",
        "Create professional MASAR intelligence and business development reports"
    )

    company = st.text_input(
        "Company / Client Name"
    )

    profile = st.text_area(
        "Company Profile"
    )

    services = st.text_area(
        "Services / Business Activities"
    )

    opportunities = st.text_area(
        "Potential MASAR Opportunities"
    )

    risks = st.text_area(
        "Risks / Challenges"
    )

    recommendation = st.text_area(
        "MASAR Recommendation"
    )

    content = {
        "Executive Summary": profile,
        "Services & Activities": services,
        "Potential MASAR Opportunities": opportunities,
        "Risks & Challenges": risks,
        "MASAR Strategic Recommendation": recommendation
    }

    if st.button(
        "Generate Report",
        type="primary"
    ):

        if not company:

            st.warning(
                "Enter a company name."
            )

        else:

            st.session_state[
                "report_content"
            ] = content

            st.success(
                "Report generated."
            )

    if "report_content" in st.session_state:

        content = st.session_state[
            "report_content"
        ]

        st.markdown(
            "### Report Preview"
        )

        for section, text in content.items():

            st.markdown(
                f"#### {section}"
            )

            st.write(
                text or "—"
            )

        docx = generate_docx(
            company,
            content
        )

        pdf = generate_pdf(
            company,
            content
        )

        st.download_button(
            "📄 Download Word Report",
            data=docx,
            file_name=f"{company}_MASAR_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        st.download_button(
            "📕 Download PDF Report",
            data=pdf,
            file_name=f"{company}_MASAR_Report.pdf",
            mime="application/pdf"
        )


# =========================================================
# GOVERNANCE
# =========================================================

def governance():

    header(
        "Governance",
        "Policies, procedures and organizational documents"
    )

    tab1, tab2 = st.tabs(
        ["Governance Library", "Add Document"]
    )

    with tab1:

        df = query("""
            SELECT
                id,
                category,
                title,
                review_date,
                status
            FROM governance
            ORDER BY id DESC
        """)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        with st.form(
            "governance_form"
        ):

            category = st.selectbox(
                "Document Type",
                [
                    "Job Description",
                    "Procedure",
                    "Policy",
                    "Governance",
                    "Other"
                ]
            )

            title = st.text_input(
                "Title"
            )

            review_date = st.date_input(
                "Next Review Date"
            )

            status = st.selectbox(
                "Status",
                [
                    "Active",
                    "Draft",
                    "Under Review",
                    "Archived"
                ]
            )

            content = st.text_area(
                "Document Content",
                height=300
            )

            submit = st.form_submit_button(
                "Save Document"
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
                        review_date.isoformat(),
                        status
                    )
                )

                st.success(
                    "Governance document saved."
                )

                st.rerun()


# =========================================================
# EXCEL
# =========================================================

def excel_download(df):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="MASAR Data"
        )

    output.seek(0)

    return output.getvalue()


# =========================================================
# ROUTER
# =========================================================

if page == "Executive Dashboard":
    dashboard()

elif page == "CRM & Companies":
    crm()

elif page == "Opportunities":
    opportunities()

elif page == "Contacts":
    contacts()

elif page == "Meetings":
    meetings()

elif page == "Follow-ups":
    followups()

elif page == "Intelligence Center":
    intelligence()

elif page == "Analytics":
    analytics()

elif page == "Report Factory":
    report_factory()

elif page == "Governance":
    governance()