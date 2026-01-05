import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

    # Filter Layout
    f_col1, f_col2 = st.columns(2)
    with f_col1:
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
    
    # Base Data Filtering (Time)
    filtered_df = df.copy()
    if start_date:
        filtered_df = filtered_df[filtered_df['datetime'] >= start_date]

    # Extract available activities for filter
    available_activities = ["All"]
    if not filtered_df.empty:
        # Avoid NaN in activity
        ex_rows = filtered_df[filtered_df['type'] == 'exercise']
        if not ex_rows.empty:
            ex_types = ex_rows['activity'].dropna().unique().tolist()
            ex_types.sort()
            available_activities.extend(ex_types)

    with f_col2:
        activity_filter = st.selectbox("Exercise Type", available_activities, index=0)

    # Apply Activity Filter
    if activity_filter != "All":
        filtered_df = filtered_df[
            (filtered_df['type'] != 'exercise') | 
            (filtered_df['activity'] == activity_filter)
        ]

    # --- Processing Data ---
    meditation_df = filtered_df[filtered_df['type'] == 'meditation'].copy()
    exercise_df = filtered_df[filtered_df['type'] == 'exercise'].copy()
    weight_df = filtered_df[filtered_df['type'] == 'weight'].copy()

    # --- KPIs ---
    kpi_cols = st.columns(4)
    
    # 1. Weight KPI
    current_weight = 0
    if not weight_df.empty:
        current_weight = weight_df.sort_values('datetime', ascending=False).iloc[0]['weight']
    
    with kpi_cols[0]:
        st.metric(
            label="Weight (Kg)", 
            value=f"{current_weight} kg",
            delta=f"{round(current_weight - 75, 1)} kg" if current_weight else None,
            delta_color="inverse"
        )

    # Date calc for averages
    days = 1
    if start_date:
        days = (today - start_date).days
    elif not filtered_df.empty:
        td = filtered_df['datetime'].max() - filtered_df['datetime'].min()
        days = td.days
    days = max(1, days)
    is_all_time = (filter_option == "All Time")

    # 2. Calories KPI
    metric_cal = 0
    label_cal = "Total Kcal" if is_all_time else "Avg Kcal/Day"
    if not exercise_df.empty:
        total_calories = exercise_df['calories'].sum()
        metric_cal = total_calories if is_all_time else int(total_calories / days)

    with kpi_cols[1]:
        st.metric(label=label_cal, value=f"{metric_cal}")

    # 3. Exercise Minutes KPI
    metric_ex_min = 0
    label_ex_min = "Ex. Minutes" if is_all_time else "Avg Ex. Min/Day"
    if not exercise_df.empty:
        total_ex_mins = exercise_df['duration_minutes'].sum()
        metric_ex_min = total_ex_mins if is_all_time else int(total_ex_mins / days)

    with kpi_cols[2]:
        st.metric(label=label_ex_min, value=f"{metric_ex_min} min")

    # 4. Meditation KPI
    metric_med = 0
    label_med = "Mindfulness" if is_all_time else "Avg Mind/Day"
    if not meditation_df.empty:
        total_meditation = meditation_df['duration_minutes'].sum()
        metric_med = total_meditation if is_all_time else int(total_meditation / days)

    with kpi_cols[3]:
        st.metric(label=label_med, value=f"{metric_med} min")

    # --- Charts ---
    st.markdown("### Activity Trends")
    
    # Dual Axis Setup
    has_seconds = not exercise_df.empty
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Meditation (Primary Y)
    if not meditation_df.empty:
        med_daily = meditation_df.groupby(meditation_df['datetime'].dt.date)['duration_minutes'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=med_daily['datetime'],
            y=med_daily['duration_minutes'],
            name="Meditation (min)",
            marker_color='#2ea043'
        ), secondary_y=False)

    # 2. Exercise Minutes (Primary Y)
    if not exercise_df.empty:
        ex_daily = exercise_df.groupby(exercise_df['datetime'].dt.date)['duration_minutes'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=ex_daily['datetime'],
            y=ex_daily['duration_minutes'],
            name="Exercise (min)",
            marker_color='#db6d28'
        ), secondary_y=False)
        
        # 3. Exercise Calories (Secondary Y)
        ex_cal_daily = exercise_df.groupby(exercise_df['datetime'].dt.date)['calories'].sum().reset_index()
        fig.add_trace(go.Scatter(
            x=ex_cal_daily['datetime'],
            y=ex_cal_daily['calories'],
            name="Calories (kcal)",
            line=dict(color='#ff4b4b', width=3),
            mode='lines+markers'
        ), secondary_y=True)

    fig.update_layout(
        barmode='stack',
        template="plotly_dark",
        legend=dict(x=0, y=1.1, orientation="h"),
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0)
    )

    fig.update_yaxes(title_text="Minutes", secondary_y=False)
    if has_seconds:
        fig.update_yaxes(title_text="Calories", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    # Lower Row Charts
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### Exercise Distribution")
        if not exercise_df.empty:
            pie_df = exercise_df.groupby('activity')['duration_minutes'].sum().reset_index()
            fig_pie = px.pie(
                pie_df, 
                values='duration_minutes', 
                names='activity',
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No exercise data available for pie chart.")

    with c2:
        st.markdown("### Weight Trend")
        if not weight_df.empty:
            weight_df_sorted = weight_df.sort_values('datetime')
            fig_weight = px.line(
                weight_df_sorted, 
                x='datetime', 
                y='weight',
                markers=True,
                template="plotly_dark"
            )
            fig_weight.update_traces(line_color='#58a6ff')
            fig_weight.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_weight, use_container_width=True)
        else:
            st.info("No weight data recorded.")
