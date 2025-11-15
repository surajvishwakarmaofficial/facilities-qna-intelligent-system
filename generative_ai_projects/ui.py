import streamlit as st
import requests
import time
import os
import dotenv
from datetime import datetime
import json

# Import refactored logic
from src.utils.state_utils import initialize_session_state
from src.rag_core import FacilitiesRAGSystem
from src.llm.clients import get_llm_greeting_response
from config.constant_config import Config

dotenv.load_dotenv()


# Enhanced CSS Styling with Modern Design
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }
    
    /* Auth Page Styles */
    .auth-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 3rem;
        border-radius: 24px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        animation: fadeIn 0.6s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .auth-title {
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .auth-subtitle {
        color: #666;
        font-size: 1.2rem;
        font-weight: 500;
    }
    
    /* Dashboard Styles */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        margin-bottom: 2rem;
        color: white;
    }
    
    .user-welcome {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .user-details {
        display: flex;
        gap: 2rem;
        font-size: 0.95rem;
        opacity: 0.9;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Chat Interface Styles */
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        min-height: 500px;
    }
    
    .chat-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Sidebar Enhancements */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .feature-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .feature-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }
    
    /* Button Styles */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Form Input Styles */
    .stTextInput>div>div>input {
        border-radius: 10px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Tab Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 1rem 2rem;
        font-weight: 600;
    }
    
    /* Quick Action Buttons */
    .quick-action {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }
    
    .quick-action:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .status-ready {
        background: #d4edda;
        color: #155724;
    }
    
    .status-pending {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-error {
        background: #f8d7da;
        color: #721c24;
    }
    
    /* Source Documents */
    .source-doc {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 3px solid #667eea;
        margin-bottom: 0.5rem;
    }
    
    .source-title {
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    /* Animation for messages */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .stChatMessage {
        animation: slideIn 0.4s ease-out;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Expander Styles */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* File Uploader */
    .stFileUploader {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        border: 2px dashed #667eea;
    }
    
    /* Metrics */
    .metric-container {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)


def show_notification(message, type="info"):
    """Display styled notifications"""
    icons = {"success": "✅", "error": "❌", "info": "ℹ️", "warning": "⚠️"}
    colors = {
        "success": "#d4edda",
        "error": "#f8d7da",
        "info": "#d1ecf1",
        "warning": "#fff3cd"
    }
    st.markdown(f"""
        <div style="background: {colors.get(type, colors['info'])}; 
                    padding: 1rem; 
                    border-radius: 10px; 
                    margin: 1rem 0;
                    border-left: 4px solid {colors.get(type, colors['info']).replace('d', '8')};">
            {icons.get(type, icons['info'])} {message}
        </div>
    """, unsafe_allow_html=True)


def login_page():
    """Neon minimalist login card design"""
    
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    st.markdown("""
        <style>
        /* Dark background */
        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
        }
        
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Neon card container */
        .neon-card {
            background: rgba(26, 28, 36, 0.95);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            box-shadow: 0 8px 32px rgba(0, 255, 255, 0.1),
                        0 0 60px rgba(0, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 255, 0.2);
            max-width: 400px;
            margin: 0 auto;
            backdrop-filter: blur(10px);
        }
        
        /* Logo/Icon */
        .neon-icon {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #00fff5 0%, #0099ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 20px rgba(0, 255, 255, 0.5));
        }
        
        /* Title */
        .neon-title {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.3rem;
            text-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
        }
        
        /* Subtitle */
        .neon-subtitle {
            text-align: center;
            color: #8a8a9e;
            font-size: 0.85rem;
            margin-bottom: 1.2rem;
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            background: rgba(42, 44, 56, 0.8) !important;
            border: 1px solid rgba(0, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            padding: 0.5rem 0.75rem !important;
            font-size: 0.85rem !important;
            transition: all 0.3s ease !important;
            height: 38px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border: 1px solid rgba(0, 255, 255, 0.6) !important;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2) !important;
            outline: none !important;
        }
        
        .stTextInput > label {
            color: #00fff5 !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            margin-bottom: 0.3rem !important;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #00fff5 0%, #0099ff 100%) !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            letter-spacing: 1px !important;
            width: 100% !important;
            margin-top: 0.5rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 20px rgba(0, 255, 255, 0.3) !important;
            height: 38px !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 30px rgba(0, 255, 255, 0.5) !important;
        }
        
        /* Checkbox styling */
        .stCheckbox {
            color: #8a8a9e !important;
            font-size: 0.8rem !important;
        }
        
        /* Divider */
        .neon-divider {
            text-align: center;
            margin: 1rem 0;
            color: #8a8a9e;
            position: relative;
            font-size: 0.8rem;
        }
        
        .neon-divider::before,
        .neon-divider::after {
            content: "";
            position: absolute;
            top: 50%;
            width: 42%;
            height: 1px;
            background: rgba(138, 138, 158, 0.3);
        }
        
        .neon-divider::before {
            left: 0;
        }
        
        .neon-divider::after {
            right: 0;
        }
        
        /* Social buttons */
        .social-btn {
            background: rgba(42, 44, 56, 0.8) !important;
            border: 1px solid rgba(138, 138, 158, 0.2) !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            padding: 0.5rem !important;
            margin: 0.3rem 0 !important;
            font-size: 0.8rem !important;
        }
        
        /* Link styling */
        .neon-link {
            color: #00fff5;
            text-decoration: none;
            font-size: 0.8rem;
            transition: all 0.3s ease;
        }
        
        .neon-link:hover {
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
        }
        
        /* Footer text */
        .footer-text {
            text-align: center;
            margin-top: 1rem;
            color: #8a8a9e;
            font-size: 0.8rem;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background: transparent;
            border-bottom: 1px solid rgba(0, 255, 255, 0.1);
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #8a8a9e;
            background: transparent;
            border: none;
            font-weight: 600;
        }
        
        .stTabs [aria-selected="true"] {
            color: #00fff5 !important;
            border-bottom: 2px solid #00fff5 !important;
        }
        
        /* Error/Success messages */
        .stAlert {
            background: rgba(42, 44, 56, 0.8) !important;
            border-radius: 8px !important;
            border-left: 3px solid #00fff5 !important;
            padding: 0.5rem !important;
            font-size: 0.8rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # st.markdown('<div class="neon-card">', unsafe_allow_html=True)
        st.markdown('''
            <div class="neon-card" style="padding: 1rem; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
                <h2 style="margin: 0; color: #667eea; font-weight: 700;">AI Assistant</h2>
                <p style="color: #666; margin-top: 0.5rem;">Facilities Management AI Assistant</p>
            </div>
        ''', unsafe_allow_html=True)        
        # Check if showing registration form
        if st.session_state.show_register:
            # Registration Form
            st.markdown('<div class="neon-icon">🤖</div>', unsafe_allow_html=True)
            st.markdown('<h1 class="neon-title">Create Account</h1>', unsafe_allow_html=True)
            st.markdown('<p class="neon-subtitle">Join Facilities AI today</p>', unsafe_allow_html=True)
            
            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input(
                    "Full Name",
                    placeholder="Enter your full name",
                    help="Your complete name"
                )
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    username_reg = st.text_input(
                        "Username",
                        placeholder="Choose username",
                        help="Unique username"
                    )
                with col_r2:
                    email = st.text_input(
                        "Email",
                        placeholder="Enter email",
                        help="Your work email"
                    )
                
                col_r3, col_r4 = st.columns(2)
                with col_r3:
                    password_reg = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Min 8 characters",
                        help="Strong password"
                    )
                with col_r4:
                    confirm_password = st.text_input(
                        "Confirm",
                        type="password",
                        placeholder="Re-enter password"
                    )
                
                agree_terms = st.checkbox("I agree to Terms of Service and Privacy Policy")
                
                register_btn = st.form_submit_button("CREATE ACCOUNT", use_container_width=True)
                
                if register_btn:
                    if not all([full_name, username_reg, email, password_reg, confirm_password]):
                        st.error("📝 All fields are required")
                    elif not agree_terms:
                        st.error("📋 Please agree to the terms")
                    elif len(password_reg) < 8:
                        st.error("🔒 Password must be at least 8 characters")
                    elif password_reg != confirm_password:
                        st.error("🔄 Passwords do not match")
                    elif "@" not in email or "." not in email:
                        st.error("📧 Invalid email address")
                    else:
                        with st.spinner("🔄 Creating account..."):
                            try:
                                response = requests.post(
                                    f"{Config.API_URL}/api/register",
                                    json={
                                        "username": username_reg,
                                        "email": email,
                                        "full_name": full_name,
                                        "password": password_reg
                                    },
                                    timeout=10
                                )
                                
                                if response.status_code == 200:
                                    st.success("✅ Account created successfully!")
                                    st.info("🔐 Please sign in with your credentials")
                                    st.balloons()
                                    time.sleep(2)
                                    st.session_state.show_register = False
                                    st.rerun()
                                else:
                                    error_detail = response.json().get("detail", "Registration failed")
                                    st.error(f"❌ {error_detail}")
                            except requests.exceptions.ConnectionError:
                                st.error("🔴 Backend server is not running")
                                st.code("uvicorn main:app --reload", language="bash")
                            except Exception as e:
                                st.error(f"⚠️ Error: {str(e)}")
            
            # Back to login
            st.markdown('<div class="neon-divider">OR</div>', unsafe_allow_html=True)
            col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
            with col_back2:
                if st.button("← Back to Sign In", use_container_width=True, key="back_to_login"):
                    st.session_state.show_register = False
                    st.rerun()
        
        else:
            # Login Form (existing code)
            # AI Logo/Icon
            st.markdown('<div class="neon-icon">🤖</div>', unsafe_allow_html=True)
            st.markdown('<h1 class="neon-title">Sign In</h1>', unsafe_allow_html=True)
            st.markdown('<p class="neon-subtitle">Access your account</p>', unsafe_allow_html=True)
            
            # Login Form
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "Email",
                    placeholder="",
                    help="Enter your username or email"
                )
                
                password = st.text_input(
                    "Password",
                    placeholder="",
                    type="password",
                    help="Enter your password"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    remember = st.checkbox("Keep me signed in")
                with col_b:
                    st.markdown('<div style="text-align: right; padding-top: 0.5rem;"><a href="#" class="neon-link">Forgot password?</a></div>', unsafe_allow_html=True)
                
                submit = st.form_submit_button("SIGN IN", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("📝 Please fill in all fields")
                    elif len(password) < 8:
                        st.error("🔒 Password must be at least 8 characters")
                    else:
                        with st.spinner("🔄 Authenticating..."):
                            try:
                                response = requests.post(
                                    f"{Config.API_URL}/api/login",
                                    json={"username": username, "password": password},
                                    timeout=10
                                )
                                
                                if response.status_code == 200:
                                    data = response.json()
                                    st.session_state.logged_in = True
                                    st.session_state.username = username
                                    st.session_state.user_data = data["user"]
                                    st.session_state.messages = []
                                    st.session_state.login_time = datetime.now()
                                    
                                    st.toast('Login successful!', icon='✅')
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid credentials. Please try again.")
                            
                            except requests.exceptions.Timeout:
                                st.error("⏱️ The server is taking too long to respond.")
                            except requests.exceptions.ConnectionError:
                                st.error("🔴 **Server Connection Error**")
                                st.info("Please ensure the backend server is running:")
                                st.code("uvicorn main:app --reload", language="bash")
                            except Exception as e:
                                st.error(f"⚠️ Unexpected error: {str(e)}")
                                print(f"Login error: {type(e).__name__} - {str(e)}")
            
            # Divider
            st.markdown('<div class="neon-divider">OR</div>', unsafe_allow_html=True)
            
            # Social login buttons
            st.markdown("""
                <button class="social-btn" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    <span style="font-size: 1.2rem;">🔵</span> Continue with Google
                </button>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <button class="social-btn" style="width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 0.5rem;">
                    <span style="font-size: 1.2rem;">🍎</span> Continue with Apple
                </button>
            """, unsafe_allow_html=True)
            
            
            st.markdown('<div class="footer-text" style="color: #8a8a9e; font-size: 0.9rem;">New here?</div>', unsafe_allow_html=True)
            
            # Footer - Create Account Link
            col_x, col_y, col_z = st.columns([1, 2, 1])
            with col_y:
                if st.button("Create an account", use_container_width=True, key="create_account_btn"):
                    st.session_state.show_register = True
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Copyright
        st.markdown("""
            <p style='text-align: center; color: #5a5a6e; font-size: 0.85rem; margin-top: 2rem;'>
                🔒 Secure • 🚀 Fast • 💡 Intelligent<br>
                © 2025 Facilities Management AI. All rights reserved.
            </p>
        """, unsafe_allow_html=True)

def dashboard():
    """Main dashboard with tickets"""
    user = st.session_state.user_data
    
    col_h, col_l = st.columns([6, 1])
    
    with col_h:
        st.markdown(f'''
        <div class="dashboard-header">
            <div class="user-welcome">👋 Welcome, {user['full_name']}!</div>
            <div class="user-details">
                <span>👤 {user['username']}</span>
                <span>📧 {user['email']}</span>
                <span>🛡️ {user['role']}</span>
                <span>🕒 {datetime.now().strftime('%B %d, %Y • %I:%M %p')}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col_l:
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">💬</div><div class="stat-value">{len(st.session_state.get("messages", []))}</div><div class="stat-label">Messages</div></div>', unsafe_allow_html=True)
    
    with col2:
        status = "🟢 Active" if st.session_state.get('system_initialized', False) else "🟡 Inactive"
        st.markdown(f'<div class="stat-card"><div class="stat-value">🤖</div><div class="stat-label">System</div><div style="margin-top: 0.5rem; font-weight: 600;">{status}</div></div>', unsafe_allow_html=True)
    
    with col3:
        session = "Just now"
        if hasattr(st.session_state, 'login_time'):
            mins = int((datetime.now() - st.session_state.login_time).total_seconds() / 60)
            session = f"{mins}m" if mins > 0 else "Just now"
        st.markdown(f'<div class="stat-card"><div class="stat-value">⏱️</div><div class="stat-label">Session</div><div style="margin-top: 0.5rem; font-weight: 600;">{session}</div></div>', unsafe_allow_html=True)
    
    with col4:
        docs = st.session_state.get('docs_processed', 0)
        st.markdown(f'<div class="stat-card"><div class="stat-value">📄</div><div class="stat-value">{docs}</div><div class="stat-label">Docs</div></div>', unsafe_allow_html=True)
    
    main_tab1, main_tab2 = st.tabs(["💬 AI Assistant", "🎫 Ticket Management"])
    
    # ==========================================
    # TAB 1: AI ASSISTANT - PUT YOUR EXISTING CODE HERE
    # ==========================================
    with main_tab1:
        # 🔽🔽🔽 START: COPY ALL YOUR OLD SIDEBAR CODE HERE 🔽🔽🔽
        with st.sidebar:
            st.markdown("### ⚡ System Control")
            
            if not st.session_state.system_initialized:
                if st.button("🚀 Initialize Knowledge Base", type="primary", use_container_width=True):
                    
                    steps = [
                        ("Connecting to Milvus...", 0),
                        ("Loading embeddings...", 25),
                        ("Processing knowledge base...", 50),
                        ("Building vector index...", 75),
                        ("Finalizing system...", 90),
                    ]
                    
                    spinner_placeholder = st.empty()
                    progress_placeholder = st.empty()
                    
                    success = True
                    
                    rag_system = FacilitiesRAGSystem()
                    
                    with spinner_placeholder:
                        with st.spinner(f"🔄 {steps[0][0]}"):
                            progress_placeholder.progress(steps[0][1])
                            if not rag_system.initialize_clients():
                                success = False
                                spinner_placeholder.empty()
                                st.error("❌ Failed to initialize system")
                    
                    if success:
                        with spinner_placeholder:
                            with st.spinner(f"🔄 {steps[1][0]}"):
                                progress_placeholder.progress(steps[1][1])
                                time.sleep(0.5)
                        
                        with spinner_placeholder:
                            with st.spinner(f"🔄 {steps[2][0]}"):
                                progress_placeholder.progress(steps[2][1])
                                time.sleep(0.5)
                        
                        with spinner_placeholder:
                            with st.spinner(f"🔄 {steps[3][0]}"):
                                progress_placeholder.progress(steps[3][1])
                                if not rag_system.load_knowledge_base():
                                    success = False
                                    spinner_placeholder.empty()
                                    st.error("❌ Failed to load knowledge base")
                        
                        if success:
                            with spinner_placeholder:
                                with st.spinner(f"🔄 {steps[4][0]}"):
                                    progress_placeholder.progress(steps[4][1])
                                    time.sleep(0.5)
                            
                            spinner_placeholder.empty()
                            progress_placeholder.progress(100)
                            st.success("✅ System ready!")
                            
                            st.session_state.rag_system = rag_system
                            st.session_state.system_initialized = True
                            
                            st.balloons()
                            time.sleep(1.5)
                            st.rerun()
                    
                    if not success:
                        progress_placeholder.empty()
            else:
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                                padding: 1rem; border-radius: 12px; text-align: center;
                                border: 2px solid #28a745; margin-bottom: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                        <div style="color: #155724; font-weight: 700; font-size: 1.1rem;">
                            System Ready
                        </div>
                        <div style="color: #155724; font-size: 0.85rem; margin-top: 0.3rem;">
                            AI-powered responses active
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            if st.session_state.system_initialized:
                st.markdown("### 📤 Upload Documents")
                uploaded_file = st.file_uploader(
                    "Upload Documents",
                    type=["pdf", "csv", "xlsx", "xls", "txt"],
                    help="Upload documents in PDF, CSV, Excel, or TXT format"
                )
               
                if uploaded_file:
                    file_identifier = (uploaded_file.name, uploaded_file.size)
                    if st.session_state.processed_file_id != file_identifier:
                        with st.spinner(f"📄 Processing {uploaded_file.name}..."):
                            if st.session_state.rag_system.process_file(uploaded_file):
                                st.session_state.processed_file_id = file_identifier
                                st.session_state.docs_processed += 1
                                st.success(f"✅ {uploaded_file.name} processed!")
                                time.sleep(1)
                                st.rerun()
                
                st.markdown("---")
            
            if st.session_state.system_initialized:
                if st.button("🗑️ Clear Chat", use_container_width=True):
                    st.session_state.messages = []
                    if st.session_state.rag_system:
                        st.session_state.rag_system.chat_history = []
                    st.rerun()
            
                if len(st.session_state.messages) > 0:
                    st.markdown("---")
                    if st.button("💾 Export Chat", use_container_width=True):
                        chat_export = json.dumps(st.session_state.messages, indent=2)
                        st.download_button(
                            label="📥 Download JSON",
                            data=chat_export,
                            file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
        # 🔼🔼🔼 END: SIDEBAR CODE 🔼🔼🔼
        
        # 🔽🔽🔽 START: COPY YOUR CHAT MESSAGE DISPLAY CODE HERE 🔽🔽🔽
        if hasattr(st.session_state, 'sample_question'):
            prompt = st.session_state.sample_question
            delattr(st.session_state, 'sample_question')
            process_message(prompt)
            st.rerun()
        
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if "sources" in message and message["sources"]:
                    with st.expander("📚 View Sources", expanded=False):
                        for source_idx, source in enumerate(message["sources"], 1):
                            st.markdown(f"""
                                <div class="source-doc">
                                    <div class="source-title">{source_idx}. {source['title']}</div>
                                    <div style="color: #666; font-size: 0.9rem;">
                                        {source['content'][:300]}...
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
        
        if st.session_state.system_initialized:
            if prompt := st.chat_input("💬 Type your message here...", key="chat_input"):
                process_message(prompt)
                st.rerun()
        else:
            st.chat_input("💬 Initialize system to start chatting...", key="chat_input_disabled", disabled=True)
        # 🔼🔼🔼 END: CHAT CODE 🔼🔼🔼
    
    # ==========================================
    # TAB 2: TICKET MANAGEMENT - ALREADY DONE!
    # ==========================================
    with main_tab2:
        ticket_dashboard_tab()
        

TICKET_STYLES = """
<style>
.dashboard-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
}
.user-welcome {
    font-size: 2rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}
.user-details {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    font-size: 0.95rem;
    opacity: 0.95;
}
.user-details span {
    background: rgba(255,255,255,0.2);
    padding: 0.4rem 1rem;
    border-radius: 20px;
}
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.stat-card:hover {
    transform: translateY(-5px);
}
.stat-value {
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}
.stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
    font-weight: 600;
}
.ticket-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
    border-left: 5px solid #667eea;
    transition: all 0.3s ease;
}
.ticket-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}
.ticket-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 1rem;
}
.ticket-id {
    font-weight: 700;
    font-size: 1.2rem;
    color: #667eea;
    letter-spacing: 0.5px;
}
.ticket-status-badge {
    display: inline-block;
    padding: 0.5rem 1.2rem;
    border-radius: 25px;
    font-weight: 600;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.status-open { background: #fff3cd; color: #856404; }
.status-assigned { background: #cfe2ff; color: #084298; }
.status-in-progress { background: #d1ecf1; color: #0c5460; }
.status-on-hold { background: #e2e3e5; color: #383d41; }
.status-escalated { background: #f8d7da; color: #721c24; animation: pulse 2s infinite; }
.status-resolved { background: #d4edda; color: #155724; }
.status-closed { background: #e2e3e5; color: #383d41; }
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
.priority-badge {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 15px;
    font-weight: 600;
    font-size: 0.75rem;
    margin-left: 0.5rem;
    text-transform: uppercase;
}
.priority-critical { 
    background: #dc3545; 
    color: white; 
    animation: blink 1.5s infinite;
}
.priority-high { background: #fd7e14; color: white; }
.priority-medium { background: #ffc107; color: #000; }
.priority-low { background: #28a745; color: white; }
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.ticket-meta {
    display: flex;
    gap: 1.5rem;
    font-size: 0.9rem;
    color: #666;
    margin-top: 1rem;
    flex-wrap: wrap;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}
.ticket-meta span {
    display: flex;
    align-items: center;
    gap: 0.3rem;
}
.stats-mini-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.stats-mini-card:hover {
    transform: scale(1.05);
}
.stats-mini-value {
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}
.stats-mini-label {
    font-size: 0.9rem;
    opacity: 0.95;
    font-weight: 600;
}
.ticket-details-box {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    border-left: 4px solid #667eea;
}
.history-entry {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 0.8rem;
    border-left: 3px solid #667eea;
    transition: all 0.2s ease;
}
.history-entry:hover {
    background: #e9ecef;
    transform: translateX(5px);
}
.empty-state {
    text-align: center;
    padding: 3rem;
    color: #999;
}
.empty-state-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}
</style>
"""


def ticket_dashboard_tab():
    """Complete Ticket Management Dashboard"""
    st.markdown(TICKET_STYLES, unsafe_allow_html=True)
    user = st.session_state.user_data
    
    st.markdown("### 📊 Ticket Dashboard Overview")
    
    try:
        stats_response = requests.get(f"{Config.API_URL}/api/tickets/stats/dashboard", timeout=5)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f'<div class="stats-mini-card"><div class="stats-mini-value">{stats.get("total_tickets", 0)}</div><div class="stats-mini-label">📊 Total</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="stats-mini-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><div class="stats-mini-value">{stats.get("open", 0)}</div><div class="stats-mini-label">🔓 Open</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="stats-mini-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"><div class="stats-mini-value">{stats.get("in_progress", 0)}</div><div class="stats-mini-label">⚙️ Progress</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="stats-mini-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);"><div class="stats-mini-value">{stats.get("escalated", 0)}</div><div class="stats-mini-label">🔥 Escalated</div></div>', unsafe_allow_html=True)
            with col5:
                st.markdown(f'<div class="stats-mini-card" style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%);"><div class="stats-mini-value">{stats.get("resolved", 0)}</div><div class="stats-mini-label">✅ Resolved</div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("🔥 Active Critical", stats.get('active_critical', 0))
            with col_s2:
                st.metric("⚠️ Active High", stats.get('active_high', 0))
            with col_s3:
                st.metric("📈 Resolution Rate", f"{stats.get('resolution_rate', 0)}%")
    except:
        st.warning("⚠️ Could not load statistics")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 My Tickets", "➕ Create Ticket", "🔍 All Tickets"])
    
    with tab1:
        show_my_tickets(user)
    
    with tab2:
        show_create_ticket(user)
    
    with tab3:
        show_all_tickets(user)


def show_my_tickets(user):
    """My Tickets Tab"""
    st.markdown("### 🎫 My Tickets")
    
    with st.expander("🔍 Filter & Sort", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            f_status = st.selectbox("Status", ["All", "Open", "Assigned", "In Progress", "On Hold", "Escalated", "Resolved", "Closed"], key="my_status")
        with col2:
            f_priority = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="my_priority")
        with col3:
            f_sort = st.selectbox("Sort", ["Newest First", "Oldest First", "Priority"], key="my_sort")
    
    try:
        params = {}
        if f_status != "All":
            params['status'] = f_status
        if f_priority != "All":
            params['priority'] = f_priority
        
        response = requests.get(f"{Config.API_URL}/api/tickets/user/{user['id']}", params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tickets = data.get('tickets', [])
            
            if f_sort == "Oldest First":
                tickets = sorted(tickets, key=lambda x: x['created_at'])
            elif f_sort == "Priority":
                order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                tickets = sorted(tickets, key=lambda x: order.get(x['priority'], 4))
            else:
                tickets = sorted(tickets, key=lambda x: x['created_at'], reverse=True)
            
            if not tickets:
                st.markdown('<div class="empty-state"><div class="empty-state-icon">📭</div><h3>No tickets found</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown(f"**{len(tickets)} ticket(s)**")
                for t in tickets:
                    display_ticket_card(t, user['id'], False)
        else:
            st.error(f"❌ Failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        st.error("🔴 Server connection failed")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")


def show_create_ticket(user):
    """Create Ticket Tab"""
    st.markdown("### ➕ Create New Ticket")
    st.info("💡 Fill the form to submit a support request")
    
    with st.form("create_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("📂 Category *", ["IT Support", "Facilities", "Security", "HR", "Finance", "Operations", "Maintenance", "Equipment", "Other"])
        with col2:
            priority = st.selectbox("⚡ Priority *", ["Low", "Medium", "High", "Critical"], index=1)
        
        description = st.text_area("📝 Description *", height=150, placeholder="Describe your issue...")
        
        submit = st.form_submit_button("🎫 Create Ticket", use_container_width=True, type="primary")
        
        if submit:
            if not description.strip() or len(description.strip()) < 10:
                st.error("📝 Description too short (min 10 chars)")
            else:
                with st.spinner("Creating..."):
                    try:
                        resp = requests.post(f"{Config.API_URL}/api/tickets/create", json={
                            "user_id": user['id'],
                            "category": category,
                            "description": description.strip(),
                            "priority": priority
                        }, timeout=10)
                        
                        if resp.status_code == 200:
                            ticket = resp.json()
                            st.success(f"✅ Created: **{ticket['ticket_id']}**")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {resp.json().get('detail', 'Error')}")
                    except:
                        st.error("🔴 Server error")


def show_all_tickets(user):
    """All Tickets Tab (Admin)"""
    if user.get('role') not in ['admin', 'manager']:
        st.warning("🔒 Admin access required")
        return
    
    st.markdown("### 🔍 All Tickets (Admin)")
    
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            a_status = st.selectbox("Status", ["All", "Open", "Assigned", "In Progress", "On Hold", "Escalated", "Resolved", "Closed"], key="all_status")
        with col2:
            a_priority = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="all_priority")
        with col3:
            a_escalated = st.selectbox("Escalation", ["All", "Escalated Only", "Non-Escalated"], key="all_esc")
    
    try:
        params = {}
        if a_status != "All":
            params['status'] = a_status
        if a_priority != "All":
            params['priority'] = a_priority
        if a_escalated == "Escalated Only":
            params['escalated'] = True
        elif a_escalated == "Non-Escalated":
            params['escalated'] = False
        
        resp = requests.get(f"{Config.API_URL}/api/tickets/all", params=params, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            tickets = data.get('tickets', [])
            
            if not tickets:
                st.info("📭 No tickets match filters")
            else:
                st.markdown(f"**{len(tickets)} ticket(s)**")
                for t in tickets:
                    display_ticket_card(t, user['id'], True)
        else:
            st.error(f"❌ Failed: {resp.status_code}")
    except:
        st.error("🔴 Server error")


def display_ticket_card(ticket, user_id, is_admin):
    """Display ticket card"""
    status_map = {"Open": "open", "Assigned": "assigned", "In Progress": "in-progress", "On Hold": "on-hold", "Escalated": "escalated", "Resolved": "resolved", "Closed": "closed"}
    priority_map = {"Critical": "critical", "High": "high", "Medium": "medium", "Low": "low"}
    
    status_cls = status_map.get(ticket['status'], 'open')
    priority_cls = priority_map.get(ticket['priority'], 'medium')
    
    desc = ticket['description'][:200] + ("..." if len(ticket['description']) > 200 else "")
    
    st.markdown(f"""
        <div class="ticket-card">
            <div class="ticket-header">
                <div>
                    <span class="ticket-id">{ticket['ticket_id']}</span>
                    <span class="priority-badge priority-{priority_cls}">{ticket['priority']}</span>
                </div>
                <span class="ticket-status-badge status-{status_cls}">{ticket['status']}</span>
            </div>
            <div style="margin: 1rem 0;">
                <strong>📂 {ticket['category']}</strong><br><br>
                <strong>📝 Description:</strong><br>
                <div style="color: #555; margin-top: 0.5rem;">{desc}</div>
            </div>
            <div class="ticket-meta">
                <span>🕒 {ticket['age_hours']:.1f}h old</span>
                <span>📅 {ticket['created_at'][:10]}</span>
                {f"<span style='color: #dc3545; font-weight: 700;'>⚡ Level {ticket['escalation_level']}</span>" if ticket['escalated'] else ""}
                {f"<span>⏱️ Escalates in {ticket['hours_until_escalation']:.1f}h</span>" if ticket.get('hours_until_escalation', 0) > 0 and not ticket['escalated'] else ""}
            </div>
        </div>""", 
        unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👁️ View", key=f"v_{ticket['ticket_id']}", use_container_width=True):
            st.session_state[f"detail_{ticket['ticket_id']}"] = True
            st.rerun()
    
    with col2:
        if st.button("📝 Update", key=f"u_{ticket['ticket_id']}", use_container_width=True):
            st.session_state[f"update_{ticket['ticket_id']}"] = True
            st.rerun()
    
    with col3:
        if ticket['status'] not in ['Resolved', 'Closed', 'Escalated']:
            if st.button("🔥 Escalate", key=f"e_{ticket['ticket_id']}", use_container_width=True):
                escalate_ticket(ticket['ticket_id'], user_id)
    
    with col4:
        if st.button("📜 History", key=f"h_{ticket['ticket_id']}", use_container_width=True):
            st.session_state[f"history_{ticket['ticket_id']}"] = True
            st.rerun()
    
    if st.session_state.get(f"detail_{ticket['ticket_id']}", False):
        view_ticket_details(ticket)
        if st.button("✖️ Close", key=f"cd_{ticket['ticket_id']}", use_container_width=True):
            st.session_state[f"detail_{ticket['ticket_id']}"] = False
            st.rerun()
    
    if st.session_state.get(f"update_{ticket['ticket_id']}", False):
        update_ticket_modal(ticket, user_id, is_admin)
    
    if st.session_state.get(f"history_{ticket['ticket_id']}", False):
        show_ticket_history(ticket['ticket_id'])
        if st.button("✖️ Close", key=f"ch_{ticket['ticket_id']}", use_container_width=True):
            st.session_state[f"history_{ticket['ticket_id']}"] = False
            st.rerun()


def view_ticket_details(ticket):
    """View ticket details"""
    st.markdown(f"### 🎫 {ticket['ticket_id']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Status:** {ticket['status']}  
        **Priority:** {ticket['priority']}  
        **Category:** {ticket['category']}  
        **Escalated:** {'✅ Level ' + str(ticket['escalation_level']) if ticket['escalated'] else '❌ No'}  
        **Assigned:** {ticket.get('assigned_to', 'Unassigned')}
        """)
    
    with col2:
        st.markdown(f"""
        **Created:** {ticket['created_at'][:19]}  
        **Age:** {ticket['age_hours']:.1f} hours  
        **Updated:** {ticket.get('updated_at', 'N/A')[:19] if ticket.get('updated_at') else 'Never'}  
        **Resolved:** {ticket.get('resolved_at', 'Not yet')[:19] if ticket.get('resolved_at') else 'Not yet'}
        """)
    
    st.markdown("**Full Description:**")
    st.info(ticket['description'])


def update_ticket_modal(ticket, user_id, is_admin):
    """Update ticket"""
    st.markdown(f"### 📝 Update {ticket['ticket_id']}")
    
    with st.form(f"upd_{ticket['ticket_id']}"):
        col1, col2 = st.columns(2)
        
        statuses = ["Open", "Assigned", "In Progress", "On Hold", "Escalated", "Resolved", "Closed"]
        with col1:
            new_status = st.selectbox("Status", statuses, index=statuses.index(ticket['status']))
        
        priorities = ["Low", "Medium", "High", "Critical"]
        with col2:
            new_priority = st.selectbox("Priority", priorities, index=priorities.index(ticket['priority']))
        
        assigned = st.text_input("Assign To (User ID)", value=ticket.get('assigned_to', ''))
        notes = st.text_area("Resolution Notes", height=80)
        
        if st.form_submit_button("💾 Save", use_container_width=True, type="primary"):
            try:
                resp = requests.patch(
                    f"{Config.API_URL}/api/tickets/{ticket['ticket_id']}/status",
                    params={"user_id": user_id},
                    json={
                        "status": new_status,
                        "priority": new_priority,
                        "assigned_to": assigned if assigned else None,
                        "resolution_notes": notes if notes else None
                    },
                    timeout=10
                )
                
                if resp.status_code == 200:
                    st.success("✅ Updated!")
                    time.sleep(1)
                    st.session_state[f"update_{ticket['ticket_id']}"] = False
                    st.rerun()
                else:
                    st.error("❌ Failed")
            except:
                st.error("🔴 Error")


def escalate_ticket(ticket_id, user_id):
    """Escalate ticket"""
    try:
        resp = requests.post(
            f"{Config.API_URL}/api/tickets/{ticket_id}/escalate",
            params={"user_id": user_id, "reason": "Manual escalation"},
            timeout=10
        )
        
        if resp.status_code == 200:
            st.success("🔥 Escalated!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Failed")
    except:
        st.error("🔴 Error")


def show_ticket_history(ticket_id):
    """Show history"""
    try:
        resp = requests.get(f"{Config.API_URL}/api/tickets/{ticket_id}/history", timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            history = data.get('history', [])
            
            st.markdown(f"### 📜 History: {ticket_id}")
            
            if not history:
                st.info("No changes yet")
            else:
                for h in history:
                    st.markdown(f'''
                    <div class="history-entry">
                        <strong>{h['changed_by']}</strong>: {h['old_status'] or "New"} → <strong>{h['new_status']}</strong><br>
                        <small style="color: #666;">{h['changed_at'][:19]}</small><br>
                        <em>{h['comment']}</em>
                    </div>
                    ''', unsafe_allow_html=True)
    except:
        st.error("Failed to load history")

def process_message(prompt):
    """Process and respond to user message"""
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    answer = ""
    source_docs = []
    
    if not st.session_state.system_initialized:
        answer = get_llm_greeting_response(st.session_state.messages, prompt)
    else:
        result = st.session_state.rag_system.generate_response(prompt)
        answer = result["answer"]
        source_docs = result.get("sources", [])
    
    sources = []
    if source_docs and st.session_state.system_initialized:
        for doc in source_docs:
            title = doc.metadata.get("title", "Unknown")
            content = doc.page_content
            sources.append({"title": title, "content": content})
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "timestamp": datetime.now().isoformat()
    })


def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Facilities Management AI Assistant",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_data = None
        st.session_state.docs_processed = 0
    
    initialize_session_state()
    
    # Route to appropriate page
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard()


if __name__ == "__main__":
    main()