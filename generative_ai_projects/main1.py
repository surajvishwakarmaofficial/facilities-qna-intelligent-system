import streamlit as st
import requests
import time
import os
import dotenv

# Import refactored logic
from src.utils.state_utils import initialize_session_state
from src.rag_core import FacilitiesRAGSystem
from src.llm.clients import get_llm_greeting_response

dotenv.load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# CSS Styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 20px;
    }
    .auth-card {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    .stButton>button {
        border-radius: 12px !important;
        font-weight: bold !important;
        width: 100%;
    }
    .header-gradient {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .user-info {
        background: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


def login_page():
    """Display login and registration forms"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="header-gradient">🏢 Facilities Management AI</h1>', unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666; font-size:1.1rem;'>AI-Powered Policy & Facilities Assistant</p>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        # LOGIN TAB
        with tab1:
            with st.form("login_form"):
                st.markdown("### Welcome Back!")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", placeholder="Enter your password", type="password")
                submit = st.form_submit_button("LOGIN NOW", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("Please fill in all fields")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        with st.spinner("Authenticating..."):
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
                                    st.success(f"✅ Welcome back, {data['user']['full_name']}!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid username or password")
                            except requests.exceptions.ConnectionError:
                                st.error("🔴 Backend server is not running. Please start the FastAPI server.")
                                st.code("uvicorn main:app --reload", language="bash")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
        
        # REGISTER TAB
        with tab2:
            with st.form("register_form"):
                st.markdown("### Create New Account")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    full_name = st.text_input("Full Name", placeholder="John Doe", key="reg_fullname")
                    username_reg = st.text_input("Username", placeholder="johndoe", key="reg_username")
                
                with col_b:
                    email = st.text_input("Email", placeholder="john@example.com", key="reg_email")
                    password_reg = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
                
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                register_btn = st.form_submit_button("CREATE ACCOUNT", use_container_width=True)
                
                if register_btn:
                    if not all([full_name, username_reg, email, password_reg, confirm_password]):
                        st.error("❌ All fields are required")
                    elif len(password_reg) < 8:
                        st.error("❌ Password must be at least 8 characters")
                    elif password_reg != confirm_password:
                        st.error("❌ Passwords do not match")
                    else:
                        with st.spinner("Creating account..."):
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
                                    st.success("✅ Account created successfully! Please login.")
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    error_detail = response.json().get("detail", "Registration failed")
                                    st.error(f"❌ {error_detail}")
                            except requests.exceptions.ConnectionError:
                                st.error("🔴 Backend server is not running")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")


def dashboard():
    """Main dashboard after login"""
    user = st.session_state.user_data
    
    # Header with user info
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div class="user-info">
            <h2 style='margin:0; color:#667eea;'>👋 Hello, {user['full_name']}!</h2>
            <p style='margin:5px 0 0 0; color:#666;'>
                <strong>Username:</strong> {user['username']} | 
                <strong>Email:</strong> {user['email']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.header("📋 System Status")
        
        if st.button("🔄 Initialize Knowledge Base", type="primary", use_container_width=True):
            with st.spinner("Initializing RAG system..."):
                rag_system = FacilitiesRAGSystem()
                if rag_system.initialize_clients():
                    if rag_system.load_knowledge_base():
                        st.session_state.rag_system = rag_system
                        st.session_state.system_initialized = True
                        st.success("🎉 System ready!")
                    else:
                        st.error("❌ Failed to load knowledge base")
                else:
                    st.error("❌ Failed to initialize RAG system")
        
        st.markdown("---")
        st.subheader("⬆️ Upload Policy Documents")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            disabled=not st.session_state.system_initialized,
            key="pdf_uploader"
        )
        
        if uploaded_file and st.session_state.system_initialized:
            file_identifier = (uploaded_file.name, uploaded_file.size)
            if st.session_state.processed_file_id != file_identifier:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    if st.session_state.rag_system.process_pdf(uploaded_file):
                        st.session_state.processed_file_id = file_identifier
                        st.rerun()
        
        # Status indicators
        if st.session_state.system_initialized:
            st.success("🟢 System Status: Ready")
        else:
            st.warning("🟡 System Status: Not Initialized")
        
        st.info(f"💬 Messages: {len(st.session_state.messages)}")
        
        st.markdown("---")
        st.subheader("📚 Available Topics")
        st.markdown("""
        - 🅿️ Parking policies
        - 🏛️ Conference room booking
        - 💪 Gym and wellness
        - 🍽️ Cafeteria services
        - 💻 IT support & desk booking
        - 🚨 Emergency protocols
        - 📮 Mail room services
        - 🔐 Building access & security
        """)
        
        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.rag_system:
                st.session_state.rag_system.chat_history = []
            st.rerun()
    
    # Main chat interface
    st.title("🏢 Facilities Management Assistant")
    st.markdown("*Ask me anything about office amenities, policies, and procedures!*")
    
    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📄 Sources"):
                    for idx, source in enumerate(message["sources"], 1):
                        st.markdown(f"**{idx}. {source['title']}**")
                        st.caption(source['content'][:200] + "...")
    
    # Show sample questions if not initialized
    if not st.session_state.system_initialized:
        st.info("💡 You can chat for general conversation, but for specific policy questions, please click 'Initialize Knowledge Base' in the sidebar.")
        st.subheader("Sample Policy Questions (RAG Disabled)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("- What are the parking policies?")
            st.markdown("- How do I book a conference room?")
        with col2:
            st.markdown("- What are the gym timings?")
            st.markdown("- How do I get IT support?")
    
    # Chat input
    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        answer = ""
        source_docs = []
        
        if not st.session_state.system_initialized:
            with st.spinner("Thinking..."):
                answer = get_llm_greeting_response(st.session_state.messages, prompt)
        else:
            with st.spinner("Searching knowledge base..."):
                result = st.session_state.rag_system.generate_response(prompt)
                answer = result["answer"]
                source_docs = result.get("sources", [])
        
        # Display response
        with st.chat_message("assistant"):
            st.markdown(answer)
            
            sources = []
            if source_docs and st.session_state.system_initialized:
                with st.expander("📄 Sources"):
                    for idx, doc in enumerate(source_docs, 1):
                        title = doc.metadata.get("title", "Unknown")
                        content = doc.page_content
                        st.markdown(f"**{idx}. {title}**")
                        st.caption(content[:200] + "...")
                        sources.append({"title": title, "content": content})
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
        
        st.rerun()


def main():
    # Set page config
    st.set_page_config(
        page_title="Facilities Management Assistant",
        page_icon="🏢",
        layout="wide"
    )
    
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_data = None
    
    initialize_session_state()
    
    # Route to appropriate page
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard()


if __name__ == "__main__":
    main()