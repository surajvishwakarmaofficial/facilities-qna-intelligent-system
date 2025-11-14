# src/utils/state_utils.py

import streamlit as st

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False
    if 'processed_file_id' not in st.session_state:
        st.session_state.processed_file_id = None
        