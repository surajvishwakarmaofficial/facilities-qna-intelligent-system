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
    """Enhanced main dashboard with modern UI"""
    user = st.session_state.user_data
    
    # Top Header Bar
    col_header, col_logout = st.columns([6, 1])
    
    with col_header:
        st.markdown(f"""
            <div class="dashboard-header">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="user-welcome">👋 Welcome, {user['full_name']}!</div>
                        <div class="user-details">
                            <span>👤 {user['username']}</span>
                            <span>📧 {user['email']}</span>
                            <span>🕒 {datetime.now().strftime('%B %d, %Y • %I:%M %p')}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col_logout:
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()

    # Quick Stats Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">💬</div>
                <div class="stat-value">{len(st.session_state.messages)}</div>
                <div class="stat-label">Messages</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        system_status = "🟢 Active" if st.session_state.system_initialized else "🟡 Inactive"
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">🤖</div>
                <div class="stat-label">System Status</div>
                <div style="margin-top: 0.5rem; font-weight: 600;">{system_status}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        session_duration = "Just now"
        if hasattr(st.session_state, 'login_time'):
            delta = datetime.now() - st.session_state.login_time
            minutes = int(delta.total_seconds() / 60)
            session_duration = f"{minutes}m" if minutes > 0 else "Just now"
        
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">⏱️</div>
                <div class="stat-label">Session</div>
                <div style="margin-top: 0.5rem; font-weight: 600;">{session_duration}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        docs_processed = st.session_state.get('docs_processed', 0)
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">📄</div>
                <div class="stat-value">{docs_processed}</div>
                <div class="stat-label">Docs Processed</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Enhanced Sidebar
    with st.sidebar:
        st.markdown("### ⚡ Quick Actions")
        
        # Initialize System Button
        if not st.session_state.system_initialized:
            if st.button("🚀 Initialize Knowledge Base", type="primary", use_container_width=True):
                with st.spinner("🔄 Initializing RAG system..."):
                    rag_system = FacilitiesRAGSystem()
                    if rag_system.initialize_clients():
                        if rag_system.load_knowledge_base():
                            st.session_state.rag_system = rag_system
                            st.session_state.system_initialized = True
                            st.success("🎉 System ready!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to load knowledge base")
                    else:
                        st.error("❌ Failed to initialize RAG system")
        else:
            st.success("✅ System Initialized")
        
        st.markdown("---")
        
        # File Upload Section
        st.markdown("### 📤 Upload Documents")
        uploaded_file = st.file_uploader(
            "Upload PDF Policy Documents",
            type=["pdf", "csv", "xlsx", "xls", "txt"],
            disabled=not st.session_state.system_initialized,
            help="Upload company policy documents for analysis",

        )
       
        if uploaded_file and st.session_state.system_initialized:
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
        
        # System Information
        st.markdown("### 📊 System Info")
        
        if st.session_state.system_initialized:
            st.markdown("""
                <div class="feature-card">
                    <div style="color: #28a745; font-weight: 600;">
                        🟢 RAG System Active
                    </div>
                    <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                        AI-powered responses enabled
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="feature-card">
                    <div style="color: #ffc107; font-weight: 600;">
                        🟡 RAG System Inactive
                    </div>
                    <div style="font-size: 0.85rem; color: #666; margin-top: 0.5rem;">
                        General chat mode only
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Available Topics
        st.markdown("### 📚 Knowledge Base")
        topics = [
            ("🅿️", "Parking Policies"),
            ("🏛️", "Conference Rooms"),
            ("💪", "Gym & Wellness"),
            ("🍽️", "Cafeteria Services"),
            ("💻", "IT Support"),
            ("🚨", "Emergency Protocols"),
            ("📮", "Mail Services"),
            ("🔐", "Building Security")
        ]
        
        for icon, topic in topics:
            st.markdown(f"""
                <div style="background: #f8f9fa; padding: 0.5rem; 
                            border-radius: 8px; margin-bottom: 0.5rem;
                            border-left: 3px solid #667eea;">
                    {icon} {topic}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Action Buttons
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                if st.session_state.rag_system:
                    st.session_state.rag_system.chat_history = []
                st.rerun()
        
        # Export Chat
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
    
    # Main Chat Interface
    st.markdown("""
        <div class="chat-container">
            <div class="chat-title">
                <span>💬</span> Facilities Management Assistant
            </div>
            <p style="color: #666; margin-bottom: 2rem;">
                Ask me anything about office amenities, policies, and procedures!
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sample Questions (if not initialized)
    if not st.session_state.system_initialized and len(st.session_state.messages) == 0:
        st.info("💡 **Tip:** Initialize the knowledge base for policy-specific answers, or chat for general conversation!")
        
        st.markdown("### 🎯 Try These Questions:")
        col1, col2 = st.columns(2)
        
        sample_questions = [
            "What are the parking policies?",
            "How do I book a conference room?",
            "What are the gym timings?",
            "How do I get IT support?",
            "What's the cafeteria menu?",
            "Emergency evacuation procedures?"
        ]
        
        for i, question in enumerate(sample_questions):
            with col1 if i % 2 == 0 else col2:
                if st.button(f"💭 {question}", key=f"sample_{i}", use_container_width=True):
                    st.session_state.sample_question = question
                    st.rerun()
    
    # Handle sample question click
    if hasattr(st.session_state, 'sample_question'):
        prompt = st.session_state.sample_question
        delattr(st.session_state, 'sample_question')
        process_message(prompt)
        st.rerun()
    
    # Display Chat History
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
    
    # Chat Input
    if prompt := st.chat_input("💬 Type your message here...", key="chat_input"):
        process_message(prompt)
        st.rerun()


def process_message(prompt):
    """Process and respond to user message"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate response
    answer = ""
    source_docs = []
    
    if not st.session_state.system_initialized:
        # General conversation mode
        answer = get_llm_greeting_response(st.session_state.messages, prompt)
    else:
        # RAG-enabled mode
        result = st.session_state.rag_system.generate_response(prompt)
        answer = result["answer"]
        source_docs = result.get("sources", [])
    
    # Prepare sources for storage
    sources = []
    if source_docs and st.session_state.system_initialized:
        for doc in source_docs:
            title = doc.metadata.get("title", "Unknown")
            content = doc.page_content
            sources.append({"title": title, "content": content})
    
    # Add assistant message
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
    
    # Initialize session state
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