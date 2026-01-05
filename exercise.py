import streamlit as st
import time
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
                # Using a container as a card click
                # Streamlit buttons don't support much styling without custom components, 
                # so we use simple buttons with generic styling for now.
                if st.button(f"🏃 {activity}", key=activity, use_container_width=True):
                    st.session_state['ex_activity'] = activity
                    st.rerun()

    # 2. Activity / Timer Screen
    else:
        activity = st.session_state['ex_activity']
        st.caption(f"Protocol Active: {activity}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Timer Control")
            
            # Start Button
            if st.session_state['ex_start_time'] is None:
                if st.button("▶ START", type="primary", use_container_width=True):
                    st.session_state['ex_start_time'] = time.time()
                    st.rerun()
            else:
                # Stop Button
                if st.button("⏹ STOP", type="secondary", use_container_width=True):
                    end_time = time.time()
                    elapsed = end_time - st.session_state['ex_start_time']
                    st.session_state['ex_duration'] = int(elapsed / 60) # Minutes
                    st.session_state['ex_start_time'] = None # Reset Timer
                    st.rerun()
                
                # Show running status with live timer
                elapsed_sec = int(time.time() - st.session_state['ex_start_time'])
                mm, ss = divmod(elapsed_sec, 60)
                hh, mm = divmod(mm, 60)
                timer_str = f"{hh:02d}:{mm:02d}:{ss:02d}"
                
                st.info(f"⏱ Timer Running: **{timer_str}**")
                
                # Auto-refresh loop
                time.sleep(1)
                st.rerun()

        with col2:
            st.markdown("### Log Details")
            
            with st.form("workout_form"):
                duration = st.number_input(
                    "Duration (Minutes)", 
                    min_value=1, 
                    value=max(1, st.session_state['ex_duration'])
                )
                calories = st.number_input("Calories Burned", min_value=0, step=10)
                
                submitted = st.form_submit_button("Save Workout Log")
                if submitted:
                    if save_exercise_session(activity, duration, calories):
                        st.success(f"Saved {activity} - {duration} mins.")
                        # Reset
                        st.session_state['ex_activity'] = None
                        st.session_state['ex_duration'] = 0
                        time.sleep(1)
                        st.rerun()

        st.markdown("---")
        if st.button("⬅ Cancel / Back"):
            st.session_state['ex_activity'] = None
            st.session_state['ex_start_time'] = None
            st.rerun()
