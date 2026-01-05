import streamlit as st
import time
import base64
import datetime
import streamlit.components.v1 as components
from utils import save_meditation_session

# --- CONFIGURATION ---
PHASES = [
    {"name": "intro", "label": "Introduction", "duration": 15, "audio": "01_intro.m4a"},
    {"name": "breathing", "label": "Deep Breathing (3 Min)", "duration": 180, "audio": None}, # Gong only
    {"name": "feet", "label": "Body Scan: Feet", "duration": 60, "audio": "05_body_piedi.m4a"},
    {"name": "torso", "label": "Body Scan: Torso", "duration": 60, "audio": "06_body_tronco.m4a"},
    {"name": "shoulders", "label": "Body Scan: Shoulders", "duration": 60, "audio": "07_body_spalle.m4a"},
    {"name": "closing", "label": "Closing", "duration": 20, "audio": "08_chiusura.m4a"}
]

def load_audio_b64(file_path: str):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

def inject_persistent_audio(b64_string, mime_type="audio/mp4", loop=False, element_id="audio_player"):
    """
    Uses an iframe component to host the audio player. 
    If the HTML content (b64 string) remains the same across Streamlit reruns, 
    the iframe is NOT reloaded, so audio continues playing without interruption.
    """
    if not b64_string:
        return

    loop_attr = "loop" if loop else ""
    # We use a script to ensure volume/play, but standard HTML5 autoplay works in iframes usually.
    # Height 0 to hide it.
    html_content = f"""
        <html>
        <body>
        <audio autoplay {loop_attr} controls style="display:none;">
            <source src="data:{mime_type};base64,{b64_string}" type="{mime_type}">
        </audio>
        <script>
            // Optional: Ensure play if blocked?
            var audio = document.querySelector('audio');
            audio.volume = 1.0;
            audio.play().catch(e => console.log("Autoplay blocked:", e));
        </script>
        </body>
        </html>
    """
    # Key is crucial? If key changes, it remounts. 
    # If we don't provide key, Streamlit uses position + args.
    # If args (html_content) are same, it keeps it.
    components.html(html_content, height=0)

def get_audio_path(filename):
    return f"assets/audio/{filename}"

def show():
    st.header("Deep Focus Operations")

    # --- STATE MANAGEMENT ---
    if 'med_state' not in st.session_state:
        st.session_state['med_state'] = 'idle'
    if 'current_phase_index' not in st.session_state:
        st.session_state['current_phase_index'] = 0
    if 'phase_start_time' not in st.session_state:
        st.session_state['phase_start_time'] = 0
    
    # --- IDLE SCREEN (SELECTION) ---
    if st.session_state['med_state'] == 'idle':
        
        tab_live, tab_manual = st.tabs(["🧘 LIVE SESSION", "📝 MANUAL LOG"])
        
        with tab_live:
            st.info("Ensure sound is ON.")
            if st.button("▶ START MISSION", type="primary", use_container_width=True):
                st.session_state['med_state'] = 'running'
                st.session_state['current_phase_index'] = 0
                st.session_state['phase_start_time'] = time.time()
                st.rerun()
                
        with tab_manual:
            st.markdown("### Manual Meditation Entry")
            with st.form("manual_med_form"):
                log_date = st.date_input("Date of Session", value=datetime.date.today())
                log_minutes = st.number_input("Duration (Minutes)", min_value=1, value=15)
                
                if st.form_submit_button("💾 SAVE ENTRY", use_container_width=True):
                    # Convert Date to Datetime
                    dt_log = datetime.datetime.combine(log_date, datetime.time(12, 0))
                    if save_meditation_session(log_minutes, custom_date=dt_log):
                        st.success(f"Meditation log saved for {log_date}")
                        time.sleep(1)
                        st.rerun()
        return

    # --- RUNNING SCREEN ---
    
    # 1. Background Gong (Persistent Component)
    gong_b64 = load_audio_b64(get_audio_path("Gong Semplice.mp3"))
    inject_persistent_audio(gong_b64, mime_type="audio/mp3", loop=True, element_id="bg_gong")

    # 2. Timer & Phase Logic
    idx = st.session_state['current_phase_index']
    
    # Check Checkpoint
    if idx >= len(PHASES):
        save_meditation_session(10)
        st.balloons() # Verify balloons
        st.success("Mission Complete.")
        time.sleep(4) # Wait for balloons
        st.session_state['med_state'] = 'idle'
        st.rerun()
    
    current_phase = PHASES[idx]

    # 3. Voice Audio (Persistent for Phase duration)
    if current_phase["audio"]:
        audio_b64 = load_audio_b64(get_audio_path(current_phase["audio"]))
        inject_persistent_audio(audio_b64, mime_type="audio/mp4", loop=False, element_id=f"voice_{current_phase['name']}")
    else:
        components.html("<html></html>", height=0)

    # 4. Countdown Logic
    elapsed = time.time() - st.session_state['phase_start_time']
    remaining = current_phase["duration"] - elapsed
    
    # 5. UI Render - Stacked Row Layout
    st.write("### Mission Progress")
    for i, phase in enumerate(PHASES):
        c1, c2 = st.columns([3, 1])
        with c1:
            if i < idx:
                st.caption(f"✅ {phase['label']}")
                st.progress(100)
            elif i == idx:
                st.subheader(f"🔄 {phase['label']}")
                progress = min(max(elapsed / current_phase["duration"], 0.0), 1.0)
                st.progress(progress)
            else:
                st.caption(f"⏳ {phase['label']}")
                st.progress(0)
        
        with c2:
            st.write("")
            st.write("")
            if i < idx:
                st.markdown("**Completed**")
            elif i == idx:
                if st.button("⏭ SKIP", key=f"btn_skip_{i}", use_container_width=True):
                    st.session_state['current_phase_index'] += 1
                    st.session_state['phase_start_time'] = time.time()
                    st.rerun()
            else:
                st.write("-")

    # 6. Auto-Advance Logic
    if remaining <= 0:
        st.session_state['current_phase_index'] += 1
        st.session_state['phase_start_time'] = time.time()
        st.rerun()
    else:
        # Refresh loop
        time.sleep(1) 
        st.rerun()
