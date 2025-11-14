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

dotenv.load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

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
    """Enhanced login and registration page"""
    
    # Center the auth container
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("""
            <div class="auth-container">
                <div class="auth-header">
                    <h1 class="auth-title">🏢 Facilities AI</h1>
                    <p class="auth-subtitle">Your Intelligent Office Assistant</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs for Login and Register
        tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
        
        # LOGIN TAB
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                # st.markdown("### Welcome Back! 👋")
                # st.markdown("Sign in to access your dashboard")
                
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    help="Your unique username"
                )
                password = st.text_input(
                    "Password",
                    placeholder="Enter your password",
                    type="password",
                    help="Minimum 8 characters"
                )
                
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    remember = st.checkbox("Remember me")
                with col_b:
                    st.markdown("")  # Spacing
                
                submit = st.form_submit_button("🚀 LOGIN", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("📝 Please fill in all fields")
                    elif len(password) < 8:
                        st.error("🔒 Password must be at least 8 characters")
                    else:
                        with st.spinner("🔄 Authenticating..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/api/login",
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
                                    
                                    st.success(f"✨ Welcome back, {data['user']['full_name']}!")
                                    st.balloons()
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid credentials. Please try again.")
                            except requests.exceptions.ConnectionError:
                                st.error("🔴 **Server Connection Error**")
                                st.info("Please ensure the backend server is running:")
                                st.code("uvicorn main:app --reload", language="bash")
                            except Exception as e:
                                st.error(f"⚠️ Unexpected error: {str(e)}")
        
        # REGISTER TAB
        with tab2:
            with st.form("register_form", clear_on_submit=False):
                st.markdown("### Join Us Today! 🎉")
                st.markdown("Create your account in seconds")
                
                full_name = st.text_input(
                    "Full Name *",
                    placeholder="John Doe",
                    help="Your complete name"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    username_reg = st.text_input(
                        "Username *",
                        placeholder="johndoe",
                        help="Choose a unique username"
                    )
                with col_b:
                    email = st.text_input(
                        "Email *",
                        placeholder="john@company.com",
                        help="Your work email"
                    )
                
                col_c, col_d = st.columns(2)
                with col_c:
                    password_reg = st.text_input(
                        "Password *",
                        type="password",
                        placeholder="Min 8 characters",
                        help="Strong password recommended"
                    )
                with col_d:
                    confirm_password = st.text_input(
                        "Confirm Password *",
                        type="password",
                        placeholder="Re-enter password"
                    )
                
                agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
                
                register_btn = st.form_submit_button("✨ CREATE ACCOUNT", use_container_width=True)
                
                if register_btn:
                    if not all([full_name, username_reg, email, password_reg, confirm_password]):
                        st.error("📝 All fields are required")
                    elif not agree_terms:
                        st.error("📋 Please agree to the terms and conditions")
                    elif len(password_reg) < 8:
                        st.error("🔒 Password must be at least 8 characters")
                    elif password_reg != confirm_password:
                        st.error("🔄 Passwords do not match")
                    elif "@" not in email or "." not in email:
                        st.error("📧 Please enter a valid email address")
                    else:
                        with st.spinner("🔄 Creating your account..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/api/register",
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
                                    st.rerun()
                                else:
                                    error_detail = response.json().get("detail", "Registration failed")
                                    st.error(f"❌ {error_detail}")
                            except requests.exceptions.ConnectionError:
                                st.error("🔴 Backend server is not running")
                                st.code("uvicorn main:app --reload", language="bash")
                            except Exception as e:
                                st.error(f"⚠️ Error: {str(e)}")
        
        # Footer
        st.markdown("---")
        st.markdown("""
            <p style='text-align: center; color: #999; font-size: 0.9rem;'>
                🔒 Secure • 🚀 Fast • 💡 Intelligent<br>
                © 2025 Facilities Management AI. All rights reserved.
            </p>
        """, unsafe_allow_html=True)


def dashboard():
    """Enhanced main dashboard with modern UI"""
    user = st.session_state.user_data
    
    # Top Header Bar
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
            type=["pdf"],
            disabled=not st.session_state.system_initialized,
            help="Upload company policy documents for analysis"
        )
        
        if uploaded_file and st.session_state.system_initialized:
            file_identifier = (uploaded_file.name, uploaded_file.size)
            if st.session_state.processed_file_id != file_identifier:
                with st.spinner(f"📄 Processing {uploaded_file.name}..."):
                    if st.session_state.rag_system.process_pdf(uploaded_file):
                        st.session_state.processed_file_id = file_identifier
                        st.session_state.docs_processed = st.session_state.get('docs_processed', 0) + 1
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
        
        with col_b:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.clear()
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