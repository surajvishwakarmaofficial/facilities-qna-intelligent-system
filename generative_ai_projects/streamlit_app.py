import streamlit as st
import requests
import time

st.set_page_config(
    page_title="YASH Facilities AI Portal",
    page_icon="https://www.yash.com/wp-content/uploads/2023/06/YASH-Technologies-Logo.png",
    layout="centered"
)

API_URL = "http://127.0.0.1:8000"

# === FULL CSS WITH .main AND .header FIXED ===
st.markdown("""
<style>
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    .ticket-box {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        border: 2px dashed #667eea;
    }
    .stButton>button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 14px;
        border-radius: 50px;
        font-weight: bold;
        width: 100%;
    }
    .footer {
        text-align: center;
        color: white;
        margin-top: 60px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# === SESSION STATE ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_data = None
    st.session_state.messages = []

# === LOGIN PAGE ===
if not st.session_state.logged_in:
    st.markdown('<div class="main">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        st.markdown('<h1 style="text-align:center; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">YASH Facilities AI</h1>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login"):
                username = st.text_input("Username", placeholder="username")
                password = st.text_input("Password (8 chars)", type="password", placeholder="password")
                if st.form_submit_button("LOGIN"):
                    if len(password) != 8:
                        st.error("Password must be exactly 8 characters!")
                    else:
                        try:
                            r = requests.post(f"{API_URL}/api/login", json={"username": username, "password": password})
                            if r.status_code == 200:
                                data = r.json()
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_data = data["user"]
                                st.session_state.messages = []
                                st.success(f"Welcome {data['user']['full_name']}!")
                                # st.balloons()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Wrong username or password")
                        except Exception as e:
                            st.error("Backend not running → Run: uvicorn main:app --reload")

        with tab2:
            with st.form("register"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Full Name", key="full_name", placeholder="Suraj Vishwakarma")
                    st.text_input("Username", key="reg_user", placeholder="suraj")
                with col2:
                    st.text_input("Email", key="email", placeholder="suraj@yash.com")
                    password = st.text_input("Password (8 chars)", type="password", key="reg_pass", placeholder="yash2025")
                confirm = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("CREATE ACCOUNT"):
                    if password != confirm:
                        st.error("Passwords don't match!")
                    elif len(password) != 8:
                        st.error("Password must be exactly 8 characters!")
                    elif not all(st.session_state.get(k) for k in ["full_name", "reg_user", "email"]):
                        st.error("All fields required!")
                    else:
                        data = {
                            "username": st.session_state.reg_user,
                            "email": st.session_state.email,
                            "full_name": st.session_state.full_name,
                            "password": password
                        }
                        try:
                            r = requests.post(f"{API_URL}/api/register", json=data)
                            if r.status_code == 200:
                                st.success("Account created! Login now")
                                # st.balloons()
                            else:
                                st.error(r.json().get("detail", "Error"))
                        except:
                            st.error("Backend not running")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close login-card
    st.markdown('</div>', unsafe_allow_html=True)  # Close main

# === MAIN DASHBOARD AFTER LOGIN ===
else:
    user = st.session_state.user_data
    st.markdown('<div class="main">', unsafe_allow_html=True)
    
    # Header Card
    st.markdown(f'''
    <div class="header">
        <h1 style="background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Hello, <strong>{user["full_name"]}</strong>!
        </h1>
        <p style="color:#555; font-size:1.1rem;">Employee ID: <strong>{user["username"]}</strong> • {user["email"]}</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Logout
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Logout", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    # AI Chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown("### YASH AI Assistant - Ask Anything")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if prompt := st.chat_input("e.g., How to get birthday gift? | AC not working | New laptop"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Searching YASH policies..."):
                try:
                    r = requests.post(f"{API_URL}/api/query", json={
                        "user_id": st.session_state.username,
                        "query": prompt
                    })
                    if r.status_code == 200:
                        resp = r.json()["response"]
                        st.write(resp)
                        st.session_state.messages.append({"role": "assistant", "content": resp})
                    else:
                        st.error("AI service temporarily unavailable")
                except:
                    st.error("Backend offline")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Ticket Form
    with st.expander("Raise New Service Ticket", expanded=False):
        st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
        with st.form("ticket"):
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", ["Laptop", "AC/Heating", "Printer", "Network", "Birthday Gift", "Cleaning", "Others"])
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            description = st.text_area("Describe your issue")
            if st.form_submit_button("SUBMIT TICKET"):
                try:
                    r = requests.post(f"{API_URL}/api/tickets", json={
                        "user_id": st.session_state.username,
                        "category": category,
                        "description": description,
                        "priority": priority
                    })
                    if r.status_code == 200:
                        ticket_id = r.json()["ticket_id"]
                        st.success(f"Ticket {ticket_id} created successfully!")
                        # st.balloons()
                    else:
                        st.error("Failed to create ticket")
                except:
                    st.error("Backend not running")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="footer">© 2025 YASH Technologies | AI-Powered Facilities • Zilliz RAG • Auto-Escalation Active</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)