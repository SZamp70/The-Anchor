import streamlit as st
import os
from modules import dashboard, meditation, exercise

# --- Configuration ---
st.set_page_config(
    page_title="The Anchor",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

import base64

# --- CSS Injection ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def local_css(file_name):
    # Load stylesheet
    with open(file_name) as f:
        css = f.read()
    
    # Inject Background Image if exists
    bg_file = "2025_08_18 - Sudio low Res.jpg"
    bg_b64 = get_base64_of_bin_file(bg_file)
    if bg_b64:
        # Override the background-image in the already loaded CSS logic? 
        # Easier to append a new specific block
        css += f"""
        .stApp {{
            background-image: url("data:image/jpg;base64,{bg_b64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
             /* Ensure overlay is handled by box-shadow in main styles or here */
        }}
        """
        
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

local_css("styles.css")

# --- Authentication Constants ---
MASTER_PASSWORD = "papera70"

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- Main App Logic ---
def main():
    if not st.session_state['authenticated']:
        show_login()
    else:
        show_app()

def show_login():
    # Hero Image Area (Placeholder logic, better with actual image if available)
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <img src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80" style="width: 100%; border-radius: 12px; height: 300px; object-fit: cover;">
        <h1 style="color: white; margin-top: 20px;">THE ANCHOR</h1>
        <p style="color: #8b949e;">Your Operational Base specifically designed for Wellness.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Access Code", type="password")
        if st.button("Enter Operations"):
            if password == MASTER_PASSWORD:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Access Denied")

def show_app():
    # Sidebar Navigation
    with st.sidebar:
        st.title("⚓ The Anchor")
        st.markdown("---")
        menu_selection = st.radio("Navigation", ["Dashboard", "Meditation", "Exercise"], index=0)
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state['authenticated'] = False
            st.rerun()

    # Module Loading
    if menu_selection == "Dashboard":
        dashboard.show()
    elif menu_selection == "Meditation":
        meditation.show()
    elif menu_selection == "Exercise":
        exercise.show()

if __name__ == "__main__":
    main()
