import streamlit as st
import time
import datetime
from utils import save_exercise_session

def show():
    st.header("Physical Operations")

    # State
    if 'ex_activity' not in st.session_state:
        st.session_state['ex_activity'] = None
    if 'ex_start_time' not in st.session_state:
        st.session_state['ex_start_time'] = None
    if 'ex_duration' not in st.session_state:
        st.session_state['ex_duration'] = 0

    # 1. Selection Screen
    if st.session_state['ex_activity'] is None:
        st.subheader("Select Protocol")
        
        activities = [
            "Corsa sul posto", "Routine addominali", "E-bike", 
            "Cyclette", "Tapis roulant", "Camminata fuori", 
            "Vario", "Marcia sul posto", "Stretching"
        ]
        
        # Grid Layout
        cols = st.columns(3)
        for i, activity in enumerate(activities):
            with cols[i % 3]:
                if st.button(f"🏃 {activity}", key=activity, use_container_width=True):
                    st.session_state['ex_activity'] = activity
                    st.rerun()

    # 2. Activity / Timer Screen
    else:
        activity = st.session_state['ex_activity']
        st.caption(f"Protocol Active: {activity}")
        
        # If timer is running, we show ONLY the timer to focus the user
        if st.session_state['ex_start_time'] is not None:
            container = st.container(border=True)
            with container:
                st.markdown(f"### {activity}")
                elapsed_sec = int(time.time() - st.session_state['ex_start_time'])
                mm, ss = divmod(elapsed_sec, 60)
                hh, mm = divmod(mm, 60)
                timer_str = f"{hh:02d}:{mm:02d}:{ss:02d}"
                
                st.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>{timer_str}</h1>", unsafe_allow_html=True)
                st.info("⏱ Operation in progress...")
                
                if st.button("⏹ STOP & REVIEW", type="secondary", use_container_width=True):
                    end_time = time.time()
                    elapsed = end_time - st.session_state['ex_start_time']
                    st.session_state['ex_duration'] = int(elapsed / 60) # Minutes
                    st.session_state['ex_start_time'] = None # Reset Timer
                    st.rerun()
                
                # Auto-refresh loop
                time.sleep(1)
                st.rerun()
        
        # If exercise is stopped but not yet saved (Review mode)
        elif st.session_state['ex_duration'] > 0:
            container = st.container(border=True)
            with container:
                st.markdown(f"### {activity}")
                st.success(f"Session Stopped. Total: {st.session_state['ex_duration']} minutes.")
                
                with st.form("quick_save_form"):
                    st.markdown("### Finalize Log")
                    duration = st.number_input(
                        "Confirm Duration (Minutes)", 
                        min_value=1, 
                        value=max(1, st.session_state['ex_duration'])
                    )
                    calories = st.number_input("Calories Burned", min_value=0, step=10, value=int(duration * 7))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("✅ SAVE & SYNC", use_container_width=True)
                    with col2:
                        if st.form_submit_button("🗑 DISCARD", use_container_width=True):
                            st.session_state['ex_activity'] = None
                            st.session_state['ex_duration'] = 0
                            st.rerun()

                    if submitted:
                        if save_exercise_session(activity, duration, calories):
                            st.success(f"Data synchronized.")
                            st.session_state['ex_activity'] = None
                            st.session_state['ex_duration'] = 0
                            time.sleep(1)
                            st.rerun()

        # IDLE Mode: Choice between Timer and Manual Entry
        else:
            tab_timer, tab_manual = st.tabs(["⏱ LIVE TIMER", "📝 MANUAL LOG"])
            
            with tab_timer:
                st.markdown(f"### Live {activity}")
                st.markdown("<h1 style='text-align: center; color: #8b949e;'>00:00:00</h1>", unsafe_allow_html=True)
                if st.button("▶ START SESSION", type="primary", use_container_width=True):
                    st.session_state['ex_start_time'] = time.time()
                    st.rerun()
            
            with tab_manual:
                st.markdown(f"### Manual Entry: {activity}")
                with st.form("manual_log_form"):
                    log_date = st.date_input("Date of Exercise", value=datetime.date.today())
                    log_minutes = st.number_input("Duration (Minutes)", min_value=1, value=30)
                    log_calories = st.number_input("Calories Burned", min_value=0, step=10, value=int(log_minutes * 7))
                    
                    if st.form_submit_button("💾 SAVE MANUAL ENTRY", use_container_width=True):
                        # Convert Date to Datetime (Streamlit date_input returns datetime.date)
                        dt_log = datetime.datetime.combine(log_date, datetime.time(12, 0))
                        if save_exercise_session(activity, log_minutes, log_calories, custom_date=dt_log):
                            st.success(f"Manual log saved for {log_date}")
                            st.session_state['ex_activity'] = None
                            time.sleep(1)
                            st.rerun()

        st.markdown("---")
        if st.button("⬅ Back to Protocols"):
            st.session_state['ex_activity'] = None
            st.session_state['ex_start_time'] = None
            st.session_state['ex_duration'] = 0
            st.rerun()
