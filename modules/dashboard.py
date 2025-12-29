import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
from utils import get_logs, save_log

def show():
    st.header("Operations Dashboard")

    # --- Fetch Data & calculate defaults ---
    with st.spinner("Loading Operations Data..."):
        raw_logs = get_logs()
    
    # Process basic DF for defaults (before filtering)
    df = pd.DataFrame(raw_logs)
    last_known_weight = 78.0
    
    if not df.empty:
        # Ensure datetime conversion early
        if 'datetime' not in df.columns and 'timestamp' in df.columns:
             df['datetime'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        elif 'datetime' in df.columns:
             df['datetime'] = pd.to_datetime(df['datetime'], utc=True).dt.tz_convert(None)
        
        # Find latest weight
        w_df = df[df['type'] == 'weight']
        if not w_df.empty:
            last_known_weight = w_df.sort_values('datetime', ascending=False).iloc[0]['weight']

    # --- Quick Actions (Weight Log) ---
    with st.expander("Update Body Metrics"):
        with st.form("weight_form"):
            new_weight = st.number_input("Current Weight (kg)", min_value=40.0, max_value=150.0, step=0.1, value=float(last_known_weight))
            submitted = st.form_submit_button("Update Weight")
            if submitted:
                save_log({
                    "type": "weight",
                    "weight": new_weight,
                    "completed_at": datetime.datetime.now()
                })
                st.success("Weight updated.")
                st.rerun()

    # --- Filters ---
    st.subheader("Performance Overview")
    
    if df.empty:
        st.info("No data available yet. Start by logging a session!")
        return

    filter_option = st.select_slider(
        "Time Range",
        options=["7 Days", "30 Days", "90 Days", "All Time"],
        value="7 Days"
    )

    # Calculate Date Range
    today = datetime.datetime.now()
    if filter_option == "7 Days":
        start_date = today - datetime.timedelta(days=7)
    elif filter_option == "30 Days":
        start_date = today - datetime.timedelta(days=30)
    elif filter_option == "90 Days":
        start_date = today - datetime.timedelta(days=90)
    else:
        start_date = None # All time
    
    # Filter by date
    if start_date:
        df = df[df['datetime'] >= start_date]

    # --- Processing Data ---
    # Separate types
    meditation_df = df[df['type'] == 'meditation'].copy()
    exercise_df = df[df['type'] == 'exercise'].copy()
    weight_df = df[df['type'] == 'weight'].copy()

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    
    # Weight KPI
    current_weight = 0
    if not weight_df.empty:
        current_weight = weight_df.sort_values('datetime', ascending=False).iloc[0]['weight']
    
    target_weight_min = 74.0
    target_weight_max = 76.0
    
    delta_color = "off"
    if current_weight > 0:
        if current_weight < target_weight_min:
            delta_color = "inverse" # Too low?
        elif current_weight > target_weight_max:
            delta_color = "inverse" # Too high
        else:
            delta_color = "normal" # On target

    with col1:
        st.metric(
            label="Current Weight (Target: 74-76kg)", 
            value=f"{current_weight} kg",
            delta=f"{round(current_weight - 75, 1)} kg from mid-target" if current_weight else None,
            delta_color="inverse"
        )

    # Days in range (or 1 if less than a day)
    days = 1
    if start_date:
        days = (today - start_date).days
    elif not df.empty:
        days = (df['datetime'].max() - df['datetime'].min()).days
    days = max(1, days)

    # Determine Display Mode (Total vs Avg)
    is_all_time = (filter_option == "All Time")
    
    # Calories KPI
    metric_cal = 0
    label_cal = "Calories" # Default label
    
    if not exercise_df.empty:
        total_calories = exercise_df['calories'].sum()
        if is_all_time:
            metric_cal = total_calories
            label_cal = "Total Calories"
        else:
            metric_cal = int(total_calories / days)
            label_cal = "Avg Calories / Day"

    with col2:
        st.metric(label=label_cal, value=f"{metric_cal} kcal")

    # Avg/Total Meditation Minutes KPI
    metric_med = 0
    label_med = "Meditation" # Default label
    
    if not meditation_df.empty:
        total_meditation = meditation_df['duration_minutes'].sum()
        if is_all_time:
            metric_med = total_meditation
            label_med = "Total Meditation"
        else:
            metric_med = int(total_meditation / days)
            label_med = "Avg Meditation / Day"

    with col3:
        st.metric(label=label_med, value=f"{metric_med} min")

    # --- Charts ---
    
    # Area Chart: Meditation vs Exercise Minutes
    st.markdown("### Activity Volume")
    
    # Prepare data for Activity Chart
    # Group by date and type, sum duration
    activity_data = []
    
    if not meditation_df.empty:
        med_daily = meditation_df.groupby(meditation_df['datetime'].dt.date)['duration_minutes'].sum().reset_index()
        med_daily['Type'] = 'Meditation'
        activity_data.append(med_daily)
        
    if not exercise_df.empty:
        ex_daily = exercise_df.groupby(exercise_df['datetime'].dt.date)['duration_minutes'].sum().reset_index()
        ex_daily['Type'] = 'Exercise'
        activity_data.append(ex_daily)
    
    if activity_data:
        chart_df = pd.concat(activity_data)
        fig_area = px.area(
            chart_df, 
            x='datetime', 
            y='duration_minutes', 
            color='Type',
            color_discrete_map={'Meditation': '#2ea043', 'Exercise': '#db6d28'}, # Brand colors
            template="plotly_dark"
        )
        fig_area.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_area, use_container_width=True)

    # Line Chart: Weight
    st.markdown("### Weight Trend")
    if not weight_df.empty:
        weight_df_sorted = weight_df.sort_values('datetime')
        fig_line = px.line(
            weight_df_sorted, 
            x='datetime', 
            y='weight',
            template="plotly_dark",
            markers=True
        )
        # Add target range lines
        fig_line.add_hline(y=target_weight_min, line_dash="dash", line_color="green", annotation_text="Target Min")
        fig_line.add_hline(y=target_weight_max, line_dash="dash", line_color="green", annotation_text="Target Max")
        
        fig_line.update_traces(line_color='#58a6ff')
        fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.caption("No weight data recorded in this period.")
