# import streamlit as st
# import requests
# import time

# st.set_page_config(
#     page_title="YASH Facilities AI Portal",
#     page_icon="https://www.yash.com/wp-content/uploads/2023/06/YASH-Technologies-Logo.png",
#     layout="centered"
# )

# API_URL = "http://127.0.0.1:8000"

# # === FULL CSS WITH .main AND .header FIXED ===
# st.markdown("""
# <style>
#     .chat-container {
#         background: white;
#         border-radius: 20px;
#         padding: 25px;
#         box-shadow: 0 10px 30px rgba(0,0,0,0.1);
#         margin: 20px 0;
#     }
#     .ticket-box {
#         background: #f8f9fa;
#         border-radius: 15px;
#         padding: 20px;
#         border: 2px dashed #667eea;
#     }
#     .stButton>button {
#         background: linear-gradient(45deg, #667eea, #764ba2);
#         color: white;
#         border: none;
#         padding: 14px;
#         border-radius: 50px;
#         font-weight: bold;
#         width: 100%;
#     }
#     .footer {
#         text-align: center;
#         color: white;
#         margin-top: 60px;
#         font-size: 0.9rem;
#     }
# </style>
# """, unsafe_allow_html=True)

# # === SESSION STATE ===
# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
#     st.session_state.username = ""
#     st.session_state.user_data = None
#     st.session_state.messages = []

# # === LOGIN PAGE ===
# if not st.session_state.logged_in:
#     st.markdown('<div class="main">', unsafe_allow_html=True)
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
#         st.markdown('<h1 style="text-align:center; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;">YASH Facilities AI</h1>', unsafe_allow_html=True)
        
#         tab1, tab2 = st.tabs(["Login", "Register"])
        
#         with tab1:
#             with st.form("login"):
#                 username = st.text_input("Username", placeholder="username")
#                 password = st.text_input("Password (8 chars)", type="password", placeholder="password")
#                 if st.form_submit_button("LOGIN"):
#                     if len(password) < 8:
#                         st.error("Password must be min 8 characters!")
#                     else:
#                         try:
#                             r = requests.post(f"{API_URL}/api/login", json={"username": username, "password": password})
#                             if r.status_code == 200:
#                                 data = r.json()
#                                 st.session_state.logged_in = True
#                                 st.session_state.username = username
#                                 st.session_state.user_data = data["user"]
#                                 st.session_state.messages = []
#                                 st.success(f"Welcome {data['user']['full_name']}!")
#                                 # st.balloons()
#                                 time.sleep(2)
#                                 st.rerun()
#                             else:
#                                 st.error("Wrong username or password")
#                         except Exception as e:
#                             st.error("Backend not running → Run: uvicorn main:app --reload")

#         with tab2:
#             with st.form("register"):
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     st.text_input("Full Name", key="full_name", placeholder="Suraj Vishwakarma")
#                     st.text_input("Username", key="reg_user", placeholder="suraj")
#                 with col2:
#                     st.text_input("Email", key="email", placeholder="suraj@yash.com")
#                     password = st.text_input("Password (8 chars)", type="password", key="reg_pass", placeholder="yash2025")
#                 confirm = st.text_input("Confirm Password", type="password")
                
#                 if st.form_submit_button("CREATE ACCOUNT"):
#                     if password != confirm:
#                         st.error("Passwords don't match!")
#                     elif len(password) < 8:
#                         st.error("Password must be min 8 characters!")
#                     elif not all(st.session_state.get(k) for k in ["full_name", "reg_user", "email"]):
#                         st.error("All fields required!")
#                     else:
#                         data = {
#                             "username": st.session_state.reg_user,
#                             "email": st.session_state.email,
#                             "full_name": st.session_state.full_name,
#                             "password": password
#                         }
#                         try:
#                             r = requests.post(f"{API_URL}/api/register", json=data)
#                             if r.status_code == 200:
#                                 st.success("Account created! Login now")
#                                 # st.balloons()
#                             else:
#                                 st.error(r.json().get("detail", "Error"))
#                         except:
#                             st.error("Backend not running")
        
#         st.markdown('</div>', unsafe_allow_html=True)  # Close login-card
#     st.markdown('</div>', unsafe_allow_html=True)  # Close main

# # === MAIN DASHBOARD AFTER LOGIN ===
# else:
#     user = st.session_state.user_data
#     st.markdown('<div class="main">', unsafe_allow_html=True)
    
#     # Header Card
#     st.markdown(f'''
#     <div class="header">
#         <h1 style="background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
#             Hello, <strong>{user["full_name"]}</strong>!
#         </h1>
#         <p style="color:#555; font-size:1.1rem;">Employee ID: <strong>{user["username"]}</strong> • {user["email"]}</p>
#     </div>
#     ''', unsafe_allow_html=True)
    
#     # Logout
#     col1, col2 = st.columns([4, 1])
#     with col2:
#         if st.button("Logout", type="secondary"):
#             st.session_state.clear()
#             st.rerun()
    
#     # AI Chat
#     st.markdown('<div class="chat-container">', unsafe_allow_html=True)
#     st.markdown("### YASH AI Assistant - Ask Anything")
    
#     for msg in st.session_state.messages:
#         with st.chat_message(msg["role"]):
#             st.write(msg["content"])
    
#     if prompt := st.chat_input("e.g., How to get birthday gift? | AC not working | New laptop"):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.write(prompt)
        
#         with st.chat_message("assistant"):
#             with st.spinner("Searching YASH policies..."):
#                 try:
#                     r = requests.post(f"{API_URL}/api/query", json={
#                         "user_id": st.session_state.username,
#                         "query": prompt
#                     })
#                     if r.status_code == 200:
#                         resp = r.json()["response"]
#                         st.write(resp)
#                         st.session_state.messages.append({"role": "assistant", "content": resp})
#                     else:
#                         st.error("AI service temporarily unavailable")
#                 except:
#                     st.error("Backend offline")
    
#     st.markdown('</div>', unsafe_allow_html=True)
    
#     # Ticket Form
#     with st.expander("Raise New Service Ticket", expanded=False):
#         st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
#         with st.form("ticket"):
#             col1, col2 = st.columns(2)
#             with col1:
#                 category = st.selectbox("Category", ["Laptop", "AC/Heating", "Printer", "Network", "Birthday Gift", "Cleaning", "Others"])
#             with col2:
#                 priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
#             description = st.text_area("Describe your issue")
#             if st.form_submit_button("SUBMIT TICKET"):
#                 try:
#                     r = requests.post(f"{API_URL}/api/tickets", json={
#                         "user_id": st.session_state.username,
#                         "category": category,
#                         "description": description,
#                         "priority": priority
#                     })
#                     if r.status_code == 200:
#                         ticket_id = r.json()["ticket_id"]
#                         st.success(f"Ticket {ticket_id} created successfully!")
#                         # st.balloons()
#                     else:
#                         st.error("Failed to create ticket")
#                 except:
#                     st.error("Backend not running")
#         st.markdown('</div>', unsafe_allow_html=True)
    
#     st.markdown('<div class="footer">© 2025 YASH Technologies | AI-Powered Facilities • Zilliz RAG • Auto-Escalation Active</div>', unsafe_allow_html=True)
#     st.markdown('</div>', unsafe_allow_html=True)


# import streamlit as st
# import requests
# from datetime import datetime
# import time
# import pytz
# import dotenv
# import os

# dotenv.load_dotenv()

# # === CONFIG ===
# st.set_page_config(
#     page_title="YASH Facilities AI Portal",
#     page_icon="https://www.yash.com/wp-content/uploads/2023/06/YASH-Technologies-Logo.png",
#     layout="wide"
# )

# API_URL = os.environ.get("API_URL")

# ist = pytz.timezone('Asia/Kolkata')

# # === CSS ===
# st.markdown("""
# <style>
#     .main {background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 20px;}
#     .status-open {background: #e3f2fd; color: #1976d2; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
#     .status-progress {background: #fff3e0; color: #ef6c00; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
#     .status-escalated {background: #ffebee; color: #d32f2f; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
#     .status-resolved {background: #e8f5e8; color: #2e7d32; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
#     .timer {color: #d32f2f; font-weight: bold; font-size: 1rem;}
#     .ticket-card {
#         background: white;
#         padding: 20px;
#         border-radius: 16px;
#         box-shadow: 0 6px 20px rgba(0,0,0,0.1);
#         margin: 15px 0;
#         border-left: 6px solid #667eea;
#     }
#     .stButton>button {
#         border-radius: 12px !important;
#         font-weight: bold !important;
#     }
#     .footer {
#         text-align: center;
#         padding: 30px;
#         color: #666;
#         font-size: 0.9rem;
#         margin-top: 50px;
#     }
# </style>
# """, unsafe_allow_html=True)

# # === SESSION STATE ===
# if "logged_in" not in st.session_state:
#     st.session_state.logged_in = False
#     st.session_state.username = ""
#     st.session_state.user_data = None
#     st.session_state.messages = []

# # === LOGIN / REGISTER ===
# if not st.session_state.logged_in:
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.markdown("<h1 style='text-align:center; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>YASH Facilities AI</h1>", unsafe_allow_html=True)
#         st.markdown("<p style='text-align:center; color:#666;'>AI-Powered Policy & Facilities Assistant</p>", unsafe_allow_html=True)

#         tab1, tab2 = st.tabs(["Login", "Register"])

#         with tab1:
#             with st.form("login_form"):
#                 username = st.text_input("Username", placeholder="admin")
#                 password = st.text_input("Password (8 chars)", type="password", value="admin2025")
#                 submit = st.form_submit_button("LOGIN NOW")

#                 if submit:
#                     if len(password) < 8:
#                         st.error("Password must be exactly 8 characters!")
#                     else:
#                         try:
#                             r = requests.post(f"{API_URL}/api/login", json={"username": username, "password": password})
#                             if r.status_code == 200:
#                                 data = r.json()
#                                 st.session_state.logged_in = True
#                                 st.session_state.username = username
#                                 st.session_state.user_data = data["user"]
#                                 st.session_state.messages = []
#                                 st.success(f"Welcome {data['user']['full_name']}!")
#                                 # st.balloons()
#                                 time.sleep(2)
#                                 st.rerun()
#                             else:
#                                 st.error("Wrong username or password")
#                         except Exception as e:
#                             st.error("Backend not running → Run: uvicorn main:app --reload")

#         with tab2:
#             with st.form("register_form"):
#                 c1, c2 = st.columns(2)
#                 with c1:
#                     full_name = st.text_input("Full Name", key="full_name")
#                     username = st.text_input("Username", key="reg_user")
#                 with c2:
#                     email = st.text_input("Email", key="email")
#                     password = st.text_input("Password (8 chars)", type="password", key="reg_pass")
#                 confirm = st.text_input("Confirm Password", type="password")

#                 if st.form_submit_button("CREATE ACCOUNT"):
#                     if password != confirm or len(password) < 8:
#                         st.error("Password must be 8 chars and match!")
#                     elif not all([full_name, username, email]):
#                         st.error("All fields required")
#                     else:
#                         try:
#                             r = requests.post(f"{API_URL}/api/register", json={
#                                 "username": username,
#                                 "email": email,
#                                 "full_name": full_name,
#                                 "password": password
#                             })
#                             if r.status_code == 200:
#                                 st.success("Account created! Now login.")
#                                 st.balloons()
#                             else:
#                                 st.error(r.json().get("detail"))
#                         except:
#                             st.error("Backend offline")

# else:
#     user = st.session_state.user_data
#     st.markdown(f"""
#     <div class="main">
#         <h1 style="background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
#             Hello, {user['full_name']}!
#         </h1>
#         <p style="color:#555; font-size:1.1rem;">Employee ID: <strong>{user['username']}</strong> • {user['email']}</p>
#     </div>
#     """, unsafe_allow_html=True)

#     col1, col2 = st.columns([5, 1])
#     with col2:
#         if st.button("Logout"):
#             st.session_state.clear()
#             st.rerun()

#     tab1, tab2 = st.tabs(["AI Assistant", "My Tickets"])

#     # === AI CHAT ===
#     with tab1:
#         st.markdown("### Ask Anything: Policies, Gifts, AC, Laptop...")
#         for msg in st.session_state.messages:
#             with st.chat_message(msg["role"]):
#                 st.markdown(msg["content"])

#         if prompt := st.chat_input("e.g., When do I get my birthday gift?"):
#             st.session_state.messages.append({"role": "user", "content": prompt})
#             with st.chat_message("user"):
#                 st.markdown(prompt)
#             with st.chat_message("assistant"):
#                 with st.spinner("Searching knowledge base..."):
#                     try:
#                         r = requests.post(f"{API_URL}/api/query", json={
#                             "user_id": st.session_state.username,
#                             "query": prompt
#                         }, timeout=30)
#                         if r.status_code == 200:
#                             resp = r.json()["response"]
#                             st.markdown(resp)
#                             st.session_state.messages.append({"role": "assistant", "content": resp})
#                         else:
#                             st.error("AI temporarily down")
#                     except:
#                         st.error("Backend offline")

#     # === MY TICKETS ===
#     with tab2:
#         st.markdown("### Your Service Tickets")

#         try:
#             r = requests.get(f"{API_URL}/api/my-tickets/{st.session_state.username}", timeout=10)
#             if r.status_code == 200:
#                 tickets = r.json()["tickets"]
#                 if not tickets:
#                     st.info("No tickets raised yet. Create one below!")
#                 else:
#                     for t in tickets:
#                         age = t['age_hours']
#                         hrs_left = max(0, 24 - age)
#                         status_class = {
#                             "Open": "status-open",
#                             "In Progress": "status-progress",
#                             "Escalated": "status-escalated",
#                             "Resolved": "status-resolved"
#                         }.get(t['status'], "status-open")

#                         utc_time = datetime.fromisoformat(t['created_at'].replace('Z', '+00:00'))
#                         ist_time = utc_time.astimezone(ist)
#                         with st.container():
#                             st.markdown(f"""
#                             <div class="ticket-card">
#                                 <h3>#{t['ticket_id']} • {t['category']}</h3>
#                                 <p><strong>Status:</strong> <span class='{status_class}'>{t['status']}</span>
#                                 { 'ESCALATED' if t['escalated'] else ''}</p>
#                                 <p><strong>Priority:</strong> {t['priority']} • <strong>Age:</strong> {age:.1f}h</p>
#                                 { f'<p class="timer">Will auto-escalate in {hrs_left:.1f} hours</p>' if t['status'] == 'Open' and hrs_left > 0 else '' }
#                                 <p><strong>Description:</strong> {t['description']}</p>
#                                 <small>Created: {ist_time.strftime('%b %d, %Y at %I:%M %p IST')} (India Time)</small>
#                             </div>
#                             """, unsafe_allow_html=True)

#                             # ADMIN CONTROLS
#                             if st.session_state.username == "admin":
#                                 cols = st.columns(4)
#                                 actions = [
#                                     ("Open", "Open"),
#                                     ("In Progress", "In Progress"),
#                                     ("Escalate", "Escalated"),
#                                     ("Resolve", "Resolved")
#                                 ]
#                                 for col, (label, status) in zip(cols, actions):
#                                     with col:
#                                         if st.button(label, key=f"{status.lower()}_{t['ticket_id']}"):
#                                             try:
#                                                 requests.patch(
#                                                     f"{API_URL}/api/tickets/{t['ticket_id']}/status",
#                                                     json={"status": status}
#                                                 )
#                                                 st.success(f"Ticket updated to {status}")
#                                                 time.sleep(0.5)
#                                                 st.rerun()
#                                             except:
#                                                 st.error("Update failed")
#             else:
#                 st.error("Failed to load tickets")
#         except:
#             st.error("Cannot connect to backend")

#         # === RAISE NEW TICKET ===
#         with st.expander("Raise New Ticket", expanded=True):
#             with st.form("new_ticket"):
#                 c1, c2 = st.columns(2)
#                 with c1:
#                     category = st.selectbox("Category", [
#                         "Laptop", "AC/Heating", "Printer", "Network",
#                         "Birthday Gift", "Cleaning", "Furniture", "Others"
#                     ])
#                 with c2:
#                     priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
#                 description = st.text_area("Describe your issue in detail", height=120)

#                 if st.form_submit_button("SUBMIT TICKET", use_container_width=True):
#                     if len(description) < 20:
#                         st.error("Please provide more details")
#                     else:
#                         try:
#                             r = requests.post(f"{API_URL}/api/tickets", json={
#                                 "user_id": st.session_state.username,
#                                 "category": category,
#                                 "description": description,
#                                 "priority": priority
#                             })
#                             if r.status_code == 200:
#                                 st.success(f"Ticket {r.json()['ticket_id']} created successfully!")
#                                 st.balloons()
#                                 time.sleep(1)
#                                 st.rerun()
#                             else:
#                                 st.error("Failed to create ticket")
#                         except:
#                             st.error("Backend not reachable")

#     st.markdown("""
#     <div class="footer">
#         © 2025 YASH Technologies | AI-Powered Facilities • Zilliz RAG • 24×7 Auto-Escalation • Real-time Tracking
#     </div>
#     """, unsafe_allow_html=True)



import streamlit as st
import requests
from datetime import datetime
import time
import pytz
import dotenv
import os
from dateutil import parser  # <-- ADDED THIS

dotenv.load_dotenv()

# === CONFIG ===
st.set_page_config(
    page_title="YASH Facilities AI Portal",
    page_icon="https://www.yash.com/wp-content/uploads/2023/06/YASH-Technologies-Logo.png",
    layout="wide"
)

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")  # fallback

# === IST TIMEZONE ===
ist = pytz.timezone('Asia/Kolkata')

# === CSS ===
st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 20px;}
    .status-open {background: #e3f2fd; color: #1976d2; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
    .status-progress {background: #fff3e0; color: #ef6c00; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
    .status-escalated {background: #ffebee; color: #d32f2f; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
    .status-resolved {background: #e8f5e8; color: #2e7d32; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;}
    .timer {color: #d32f2f; font-weight: bold; font-size: 1rem;}
    .ticket-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        margin: 15px 0;
        border-left: 6px solid #667eea;
    }
    .stButton>button {
        border-radius: 12px !important;
        font-weight: bold !important;
    }
    .footer {
        text-align: center;
        padding: 30px;
        color: #666;
        font-size: 0.9rem;
        margin-top: 50px;
    }
</style>
""", unsafe_allow_html=True)

# === SESSION STATE ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_data = None
    st.session_state.messages = []

# === LOGIN / REGISTER ===
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>YASH Facilities AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666;'>AI-Powered Policy & Facilities Assistant</p>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="admin")
                password = st.text_input("Password (8 chars)", type="password", value="admin2025")
                submit = st.form_submit_button("LOGIN NOW")

                if submit:
                    if len(password) < 8:
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
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Wrong username or password")
                        except Exception as e:
                            st.error("Backend not running → Run: uvicorn main:app --reload")

        with tab2:
            with st.form("register_form"):
                c1, c2 = st.columns(2)
                with c1:
                    full_name = st.text_input("Full Name", key="full_name")
                    username = st.text_input("Username", key="reg_user")
                with c2:
                    email = st.text_input("Email", key="email")
                    password = st.text_input("Password (8 chars)", type="password", key="reg_pass")
                confirm = st.text_input("Confirm Password", type="password")

                if st.form_submit_button("CREATE ACCOUNT"):
                    if password != confirm or len(password) < 8:
                        st.error("Password must be 8 chars and match!")
                    elif not all([full_name, username, email]):
                        st.error("All fields required")
                    else:
                        try:
                            r = requests.post(f"{API_URL}/api/register", json={
                                "username": username,
                                "email": email,
                                "full_name": full_name,
                                "password": password
                            })
                            if r.status_code == 200:
                                st.success("Account created! Now login.")
                                st.balloons()
                            else:
                                st.error(r.json().get("detail"))
                        except:
                            st.error("Backend offline")

else:
    user = st.session_state.user_data
    st.markdown(f"""
    <div class="main">
        <h1 style="background: linear-gradient(90deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Hello, {user['full_name']}!
        </h1>
        <p style="color:#555; font-size:1.1rem;">Employee ID: <strong>{user['username']}</strong> • {user['email']}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    tab1, tab2 = st.tabs(["AI Assistant", "My Tickets"])

    # === AI CHAT ===
    with tab1:
        st.markdown("### Ask Anything: Policies, Gifts, AC, Laptop...")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("e.g., When do I get my birthday gift?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Searching knowledge base..."):
                    try:
                        r = requests.post(f"{API_URL}/api/query", json={
                            "user_id": st.session_state.username,
                            "query": prompt
                        }, timeout=30)
                        if r.status_code == 200:
                            resp = r.json()["response"]
                            st.markdown(resp)
                            st.session_state.messages.append({"role": "assistant", "content": resp})
                        else:
                            st.error("AI temporarily down")
                    except:
                        st.error("Backend offline")

    # === MY TICKETS ===
    with tab2:
        st.markdown("### Your Service Tickets")

        try:
            r = requests.get(f"{API_URL}/api/my-tickets/{st.session_state.username}", timeout=10)
            if r.status_code == 200:
                tickets = r.json()["tickets"]
                if not tickets:
                    st.info("No tickets raised yet. Create one below!")
                else:
                    for t in tickets:
                        age = t['age_hours']
                        hrs_left = max(0, 24 - age)
                        status_class = {
                            "Open": "status-open",
                            "In Progress": "status-progress",
                            "Escalated": "status-escalated",
                            "Resolved": "status-resolved"
                        }.get(t['status'], "status-open")

                        # === 100% ROBUST UTC → IST CONVERSION ===
                        created_str = t['created_at']
                        try:
                            # Try standard ISO format
                            if created_str.endswith('Z'):
                                created_str = created_str.replace('Z', '+00:00')
                            if '.' in created_str:
                                created_str = created_str.split('.')[0]  # remove microseconds
                            if '+' not in created_str and 'Z' not in t['created_at']:
                                created_str += '+00:00'
                            utc_time = datetime.fromisoformat(created_str)
                        except:
                            # Fallback: use dateutil parser (handles ANY format)
                            utc_time = parser.parse(created_str)

                        ist_time = utc_time.astimezone(ist)

                        with st.container():
                            st.markdown(f"""
                            <div class="ticket-card">
                                <h3>#{t['ticket_id']} • {t['category']}</h3>
                                <p><strong>Status:</strong> <span class='{status_class}'>{t['status']}</span>
                                { 'ESCALATED' if t['escalated'] else ''}</p>
                                <p><strong>Priority:</strong> {t['priority']} • <strong>Age:</strong> {age:.1f}h</p>
                                { f'<p class="timer">Will auto-escalate in {hrs_left:.1f} hours</p>' if t['status'] == 'Open' and hrs_left > 0 else '' }
                                <p><strong>Description:</strong> {t['description']}</p>
                                <small>Created: {ist_time.strftime('%b %d, %Y at %I:%M %p IST')} (India Time)</small>
                            </div>
                            """, unsafe_allow_html=True)

                            # ADMIN CONTROLS
                            if st.session_state.username == "admin":
                                cols = st.columns(4)
                                actions = [
                                    ("Open", "Open"),
                                    ("In Progress", "In Progress"),
                                    ("Escalate", "Escalated"),
                                    ("Resolve", "Resolved")
                                ]
                                for col, (label, status) in zip(cols, actions):
                                    with col:
                                        if st.button(label, key=f"{status.lower()}_{t['ticket_id']}"):
                                            try:
                                                requests.patch(
                                                    f"{API_URL}/api/tickets/{t['ticket_id']}/status",
                                                    json={"status": status}
                                                )
                                                st.success(f"Ticket updated to {status}")
                                                time.sleep(0.5)
                                                st.rerun()
                                            except:
                                                st.error("Update failed")
            else:
                st.error("Failed to load tickets")
        except Exception as e:
            st.error(f"Cannot connect to backend: {str(e)}")

        # === RAISE NEW TICKET ===
        with st.expander("Raise New Ticket", expanded=True):
            with st.form("new_ticket"):
                c1, c2 = st.columns(2)
                with c1:
                    category = st.selectbox("Category", [
                        "Laptop", "AC/Heating", "Printer", "Network",
                        "Birthday Gift", "Cleaning", "Furniture", "Others"
                    ])
                with c2:
                    priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                description = st.text_area("Describe your issue in detail", height=120)

                if st.form_submit_button("SUBMIT TICKET", use_container_width=True):
                    if len(description) < 20:
                        st.error("Please provide more details")
                    else:
                        try:
                            r = requests.post(f"{API_URL}/api/tickets", json={
                                "user_id": st.session_state.username,
                                "category": category,
                                "description": description,
                                "priority": priority
                            })
                            if r.status_code == 200:
                                st.success(f"Ticket {r.json()['ticket_id']} created successfully!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to create ticket")
                        except:
                            st.error("Backend not reachable")

    st.markdown("""
    <div class="footer">
        © 2025 YASH Technologies | AI-Powered Facilities • Zilliz RAG • 24×7 Auto-Escalation • Real-time Tracking
    </div>
    """, unsafe_allow_html=True)