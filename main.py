import streamlit as st
import os

# --- Page Config MUST be the first Streamlit command ---
st.set_page_config(
    page_title="The Anchor",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

import base64
from modules import dashboard, meditation, exercise
import streamlit.components.v1 as components

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
    try:
        with open(file_name) as f:
            css = f.read()
            
        # Inject Background Image if exists
        bg_file = "2025_08_18 - Sudio low Res.jpg"
        bg_b64 = get_base64_of_bin_file(bg_file)
        if bg_b64:
            css += f"""
            .stApp {{
                background-image: url("data:image/jpg;base64,{bg_b64}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            """
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("styles.css")

# --- Persistent JS Component (Wake Lock & Auth Persistence) ---
def inject_session_manager():
    # This component stays active across reruns if called in both show_login and show_app
    # It handles Screen Wake Lock and persists the 'authenticated' state in localStorage
    js_code = f"""
    <script>
    // 1. Screen Wake Lock
    let wakeLock = null;
    const requestWakeLock = async () => {{
        try {{
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('Wake Lock is active');
        }} catch (err) {{
            console.error(`${{err.name}}, ${{err.message}}`);
        }}
    }};

    if ('wakeLock' in navigator) {{
        requestWakeLock();
        // Re-request when visible again
        document.addEventListener('visibilitychange', async () => {{
            if (wakeLock !== null && document.visibilityState === 'visible') {{
                requestWakeLock();
            }}
        }});
    }}

    // 2. Auth Persistence
    const MASTER_PASSWORD = "papera70"; // Sync with Python
    
    // Check if we need to auto-login
    const savedAuth = localStorage.getItem('anchor_authenticated');
    const urlParams = new URLSearchParams(window.location.search);
    const isAutoLogin = urlParams.get('autologin');

    if (savedAuth === 'true' && !isAutoLogin && !window.location.hash.includes('authenticated=true')) {{
        // Use query param to signal auto-login to Streamlit
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('autologin', 'true');
        window.location.href = newUrl.href;
    }}

    function setAuth(status) {{
        localStorage.setItem('anchor_authenticated', status);
    }}

    // Listen for messages from Streamlit if needed, or just poll
    // For now, we'll just check the state and expose helper
    window.setAnchorAuth = setAuth;
    </script>
    """
    components.html(js_code, height=0)


# --- Authentication Constants ---
MASTER_PASSWORD = "papera70"

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- Main App Logic ---
def main():
    inject_session_manager()
    
    # Auto-login check
    if not st.session_state['authenticated']:
        if st.query_params.get("autologin") == "true":
            st.session_state['authenticated'] = True
            st.rerun()
    
    if not st.session_state['authenticated']:
        show_login()
    else:
        show_app()

def show_login():
    # Hero Image Area
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
                # Inject JS to save to localStorage
                components.html(f"<script>localStorage.setItem('anchor_authenticated', 'true');</script>", height=0)
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
        
        # Network Control
        if st.toggle("Work Offline", value=False):
            st.session_state['force_offline'] = True
        else:
            st.session_state['force_offline'] = False

        st.markdown("---")
        if st.button("Logout"):
            st.session_state['authenticated'] = False
            # Inject JS to clear localStorage
            components.html(f"<script>localStorage.setItem('anchor_authenticated', 'false');</script>", height=0)
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