import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import datetime
import json
import os

# --- Firestore Setup ---
# Check if app is already initialized to avoid errors on reload
# Check if app is already initialized to avoid errors on reload
# Check if app is already initialized to avoid errors on reload
# --- Firestore Setup ---
if not firebase_admin._apps:
    try:
        # 1. Try Streamlit Secrets (Cloud / Production)
        if "firebase" in st.secrets:
            # Create a dictionary from secrets
            key_dict = dict(st.secrets["firebase"])
            
            # FIXED: Handle private_key escaping issues common in TOML/Streamlit Secrets
            if "private_key" in key_dict:
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        
        # 2. Try Local File (Development backup)
        elif os.path.exists("firebase-key.json"):
            cred = credentials.Certificate("firebase-key.json")
            firebase_admin.initialize_app(cred)
        else:
            st.warning("⚠️ Firebase credentials not found. Using Offline Mode.")
            
    except Exception as e:
        # Prevent crash by catching all initialization errors
        st.error(f"Firebase Initialization Error: {e}")

try:
    # Attempt to get client, but handle failure gracefully
    if firebase_admin._apps:
        db = firestore.client()
    else:
        db = None
except Exception as e:
    st.error(f"Firestore Client Error: {e}")
    db = None

COLLECTION_NAME = "daily_logs"

# --- Offline Fallback ---
if 'offline_logs' not in st.session_state:
    st.session_state['offline_logs'] = []


def save_log(data: dict):
    """
    Saves a dictionary of data to Firestore with a timestamp.
    Falls back to simple session_state storage if DB is unavailable.
    """
    # Timestamp generation
    data['date_str'] = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Try Cloud Firestore
    if db is not None and not st.session_state.get('force_offline', False):
        try:
            # Add a server timestamp
            data['timestamp'] = firestore.SERVER_TIMESTAMP
            db.collection(COLLECTION_NAME).add(data)
            return True
        except Exception as e:
            # 403 or other errors -> Fallback
            # Only warn once per session to avoid spamming
            if 'firebase_error_shown' not in st.session_state:
                st.warning(f"⚠️ Firebase disconnected ({e}). Data saved LOCALLY only (will be lost on refresh).")
                st.session_state['firebase_error_shown'] = True
    
    # Fallback: Local Session State
    # Simulate server timestamp with local time for consistency
    data['timestamp'] = datetime.datetime.now()
    data['datetime'] = data['timestamp'] # Helper for pandas
    st.session_state['offline_logs'].append(data)
    return True

def get_logs(start_date=None, end_date=None, limit=None):
    """
    Retrieves logs from Firestore + Local Offline logs.
    """
    logs = []
    
    # 1. Fetch from Firestore if available
    # Check manual offline override
    if db is not None and not st.session_state.get('force_offline', False):
        try:
            query = db.collection(COLLECTION_NAME).order_by('timestamp', direction=firestore.Query.DESCENDING)
            if limit:
                query = query.limit(limit)
                
            # Use get() for blocking retrieval (safer against stream hangs)
            # This fetches all logic snapshots at once
            docs = query.get(timeout=5)
            for doc in docs:
                log_data = doc.to_dict()
                if 'timestamp' in log_data and log_data['timestamp']:
                    log_data['datetime'] = log_data['timestamp']
                logs.append(log_data)
        except Exception as e:
            # Show error to user to diagnose
            st.error(f"DB Error (Switching to Offline): {e}")
            # Auto-switch to offline to prevent further hangs
            st.session_state['force_offline'] = True
            pass
            
    # 2. Fetch from Local Session
    local_logs = st.session_state.get('offline_logs', [])
    logs.extend(local_logs)
    
    return logs

def save_meditation_session(duration_minutes):
    return save_log({
        "type": "meditation",
        "duration_minutes": duration_minutes,
        "completed_at": datetime.datetime.now()
    })

def save_exercise_session(activity_type, duration_minutes, calories):
    return save_log({
        "type": "exercise",
        "activity": activity_type,
        "duration_minutes": duration_minutes,
        "calories": calories,
        "completed_at": datetime.datetime.now()
    })
