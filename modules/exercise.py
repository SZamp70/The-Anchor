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
    if 'ex_temp_duration' not in st.session_state:
        st.session_state['ex_temp_duration'] = 0
    if 'ex_temp_calories' not in st.session_state:
        st.session_state['ex_temp_calories'] = 0
    if 'man_duration' not in st.session_state:
        st.session_state['man_duration'] = 30
    if 'man_calories' not in st.session_state:
        st.session_state['man_calories'] = 210 # 30 * 7

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
                
                st.markdown("### Finalize Log")
                
                # Sync temp duration if not set
                if st.session_state['ex_temp_duration'] == 0:
                    st.session_state['ex_temp_duration'] = max(1, st.session_state['ex_duration'])
                    st.session_state['ex_temp_calories'] = int(st.session_state['ex_temp_duration'] * 7)

                # Callback for duration change
                def on_review_duration_change():
                    st.session_state['ex_temp_calories'] = int(st.session_state['ex_temp_duration'] * 7)

                new_duration = st.number_input(
                    "Confirm Duration (Minutes)", 
                    min_value=1, 
                    key="ex_temp_duration",
                    on_change=on_review_duration_change
                )
                
                new_calories = st.number_input(
                    "Calories Burned", 
                    min_value=0, 
                    step=10, 
                    key="ex_temp_calories"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ SAVE & SYNC", type="primary", use_container_width=True):
                        if save_exercise_session(activity, st.session_state['ex_temp_duration'], st.session_state['ex_temp_calories']):
                            st.success(f"Data synchronized.")
                            st.session_state['ex_activity'] = None
                            st.session_state['ex_duration'] = 0
                            st.session_state['ex_temp_duration'] = 0
                            st.session_state['ex_temp_calories'] = 0
                            time.sleep(1)
                            st.rerun()
                with col2:
                    if st.button("🗑 DISCARD", use_container_width=True):
                        st.session_state['ex_activity'] = None
                        st.session_state['ex_duration'] = 0
                        st.session_state['ex_temp_duration'] = 0
                        st.session_state['ex_temp_calories'] = 0
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
                
                log_date = st.date_input("Date of Exercise", value=datetime.date.today())
                
                # Callback for manual duration change
                def on_manual_duration_change():
                    st.session_state['man_calories'] = int(st.session_state['man_duration'] * 7)

                st.number_input(
                    "Duration (Minutes)", 
                    min_value=1, 
                    key="man_duration",
                    on_change=on_manual_duration_change
                )
                
                st.number_input(
                    "Calories Burned", 
                    min_value=0, 
                    step=10, 
                    key="man_calories"
                )
                
                if st.button("💾 SAVE MANUAL ENTRY", type="primary", use_container_width=True):
                    # Convert Date to Datetime (Streamlit date_input returns datetime.date)
                    dt_log = datetime.datetime.combine(log_date, datetime.time(12, 0))
                    if save_exercise_session(
                        activity, 
                        st.session_state['man_duration'], 
                        st.session_state['man_calories'], 
                        custom_date=dt_log
                    ):
                        st.success(f"Manual log saved for {log_date}")
                        st.session_state['ex_activity'] = None
                        # Reset values for next manual entry
                        st.session_state['man_duration'] = 30
                        st.session_state['man_calories'] = 210
                        time.sleep(1)
                        st.rerun()

        st.markdown("---")
        if st.button("⬅ Back to Protocols"):
            st.session_state['ex_activity'] = None
            st.session_state['ex_start_time'] = None
            st.session_state['ex_duration'] = 0
            st.rerun()
