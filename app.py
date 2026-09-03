import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="MASAR Intelligence OS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #ffffff;
    }
    .sub-text {
        color: #8b949e;
        font-size: 13px;
    }
    .sidebar-brand {
        padding: 10px 0px 20px 0px;
        border-bottom: 1px solid #30363d;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Mock Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = True
if "user_name" not in st.session_state:
    st.session_state.user_name = "Abdelrahman Waleed"
if "user_role" not in st.session_state:
    st.session_state.user_role = "SSA • Employee"
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar Component ---
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <b>MASAR for Consultancy & Business Dev.</b><br>
            <span class="sub-text">Intelligent Business Platform</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.write(f"**{st.session_state.user_name}**")
    st.caption(st.session_state.user_role)
    
    st.markdown("---")
    st.markdown("### Navigation")
    
    nav_option = st.radio(
        "Go to",
        [
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
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption("Notifications: 0")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- Main Content Router ---
if nav_option == "Dashboard":
    st.markdown('<p class="main-header">Dashboard</p>', unsafe_allow_html=True)
    st.write("Welcome back, Abdelrahman. Here is an overview of your operations today.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Tasks", "4", "1 due today")
    col2.metric("CRM Leads", "18", "+3 this week")
    col3.metric("Performance Score", "94%", "+2%")

elif nav_option == "Internal Chat":
    st.markdown('<p class="main-header">Internal Chat</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-text">Secure employee-to-employee communication.</p>', unsafe_allow_html=True)
    
    chat_partner = st.selectbox("Chat With", ["Abdelrahman Waleed (SSA)", "Management Team", "Sales Department"])
    
    # Chat container
    chat_container = st.container(height=300)
    with chat_container:
        if not st.session_state.messages:
            st.info("No messages yet. Start the conversation below.")
        else:
            for msg in st.session_state.messages:
                st.markdown(f"**{msg['sender']}**: {msg['text']}")
                
    # Message input form
    with st.form("chat_form", clear_on_submit=True):
        new_msg = st.text_input("Message", placeholder="Type your message here...", label_visibility="collapsed")
        submitted = st.form_submit_button("Send", use_container_width=True)
        if submitted and new_msg:
            st.session_state.messages.append({"sender": st.session_state.user_name, "text": new_msg})
            st.rerun()

elif nav_option == "CRM":
    st.markdown('<p class="main-header">CRM Management</p>', unsafe_allow_html=True)
    st.write("Manage client relationships and pipeline status.")
    
    # Mock CRM Table
    crm_data = pd.DataFrame({
        "Client Name": ["Alpha Corp", "Beta Solutions", "Gamma Delta"],
        "Status": ["In Negotiation", "Proposal Sent", "Closed Won"],
        "Value (EGP)": ["150,000", "85,000", "320,000"]
    })
    st.dataframe(crm_data, use_container_width=True)

else:
    st.markdown(f'<p class="main-header">{nav_option}</p>', unsafe_allow_html=True)
    st.write(f"The module for **{nav_option}** is loaded and ready.")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; margin-top: 20px; padding: 10px; font-size: 11px;'>"
    "MASAR Intelligence OS &bull; Internal Business Platform"
    "</div>",
    unsafe_allow_html=True
)
