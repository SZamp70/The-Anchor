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
        ex_types = filtered_df[filtered_df['type'] == 'exercise']['activity'].dropna().unique().tolist()
        ex_types.sort()
        available_activities.extend(ex_types)

    with f_col2:
        activity_filter = st.selectbox("Exercise Type", available_activities, index=0)

    # Apply Activity Filter (Only affects Exercise Data?)
    # User said: "totali e grafici riguarderanno solo le tipologie di esercizio selezionato"
    # This implies we filter the MAIN dataframe for exercise types, but keep others?
    # Actually, if I select "Running", showing Meditation might be weird if I want to see "Running Stats".
    # BUT, typically dashboards show context.
    # Let's filter exercise_df strictly, and maybe leave meditation alone or filter it out?
    # "dopo la selezione, totali e grafici riguarderanno solo le tipologie di esercizio selezionato"
    # This suggests strict filtering. If I select "Running", I probably don't care about Meditation or Weight context.
    # HOWEVER, Weight is physically separate.
    # Let's apply filter to the dataframe used for KPIs and Charts.
    
    if activity_filter != "All":
        # Keep non-exercise rows (like weight/meditation) OR filter everything?
        # If I want to see "Running", I probably shouldn't see "Cycling".
        # But do I want to see "Meditation"? 
        # Let's assume the filter applies to the 'activity' column. 
        # Rows without 'activity' (meditation, weight) would be excluded if we do df = df[df['activity'] == filter].
        # So we must be careful.
        # Strategy: Filter 'exercise' rows to match type. Keep others?
        # User said "totali... riguarderanno solo". If I select Running, Total Meditation should probably be hidden or 0?
        # A clearer interpretation: The dashboard focuses on the selection.
        # Let's Filter the global DF to: (type != exercise) OR (activity == filter)
        # Wait, if I select Running, I want to see running stats.
        
        # Let's filter the DF to include only the selected activity for exercises.
        # We will keep Meditation and Weight visible for context unless requested otherwise, 
        # but the request says "totals and charts will concern ONLY the selected exercise types".
        # This might imply hiding meditation.
        # Let's be safe: Filter the EXERCISE portion.
        filtered_df = filtered_df[
            (filtered_df['type'] != 'exercise') | 
            (filtered_df['activity'] == activity_filter)
        ]

    # --- Processing Data ---
    # Separate types
    meditation_df = filtered_df[filtered_df['type'] == 'meditation'].copy()
    exercise_df = filtered_df[filtered_df['type'] == 'exercise'].copy()
    weight_df = filtered_df[filtered_df['type'] == 'weight'].copy()

    # --- KPIs ---
    kpi_cols = st.columns(4)
    
    # 1. Weight KPI
    current_weight = 0
    if not weight_df.empty:
        current_weight = weight_df.sort_values('datetime', ascending=False).iloc[0]['weight']
    
    target_weight_min = 74.0
    target_weight_max = 76.0
    
    with kpi_cols[0]:
        st.metric(
            label="Weight (Kg)", 
            value=f"{current_weight} kg",
            delta=f"{round(current_weight - 75, 1)} kg" if current_weight else None,
            delta_color="inverse"
        )

    # Date calc
    days = 1
    if start_date:
        days = (today - start_date).days
    elif not filtered_df.empty:
        days = (filtered_df['datetime'].max() - filtered_df['datetime'].min()).days
    days = max(1, days)
    is_all_time = (filter_option == "All Time")

    # 2. Calories KPI
    metric_cal = 0
    label_cal = "Total Kcal" if is_all_time else "Avg Kcal/Day"
    total_calories = 0
    
    if not exercise_df.empty:
        total_calories = exercise_df['calories'].sum()
        metric_cal = total_calories if is_all_time else int(total_calories / days)

    with kpi_cols[1]:
        st.metric(label=label_cal, value=f"{metric_cal}")

    # 3. Exercise Minutes KPI (UPGRADE 1)
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
    
    # 1. Activity Volume (Dual Axis: Minutes vs Calories)
    st.markdown("### Activity Trends")
    
    # Prepare data
    chart_data = []
    
    # Daily aggregation for line/bar charts
    # We want a single dataframe with Date, MedMins, ExMins, ExCals
    # Re-build from filtered_df
    
    daily_stats = filtered_df.groupby([filtered_df['datetime'].dt.date, 'type', 'activity'])[['duration_minutes', 'calories']].sum().reset_index()
    daily_stats['datetime'] = pd.to_datetime(daily_stats['datetime'])
    
    # Create figure with secondary y-axis
    fig = go.Figure()

    # Add Exercise Minutes (Bar or Area?) -> Let's use Area for volume
    # Aggregated by date for total volume
    
    daily_agg = filtered_df.groupby(filtered_df['datetime'].dt.date).agg({
        'duration_minutes': 'sum',
        'calories': 'sum'
    }).reset_index()
    daily_agg['datetime'] = pd.to_datetime(daily_agg['datetime'])

    # Breakdown by type for stacking? 
    # User wants "Exercise + Meditation". Stacking types is good. Rules out dual axis?
    # No, we can Stack Columns for Minutes, and Line for Calories.
    
    # 1. Meditation Minutes (Area/Bar)
    if not meditation_df.empty:
        med_daily = meditation_df.groupby(meditation_df['datetime'].dt.date)['duration_minutes'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=med_daily['datetime'],
            y=med_daily['duration_minutes'],
            name="Meditation (min)",
            marker_color='#2ea043'
        ))

    # 2. Exercise Minutes (Area/Bar)
    if not exercise_df.empty:
        ex_daily = exercise_df.groupby(exercise_df['datetime'].dt.date)['duration_minutes'].sum().reset_index()
        fig.add_trace(go.Bar(
            x=ex_daily['datetime'],
            y=ex_daily['duration_minutes'],
            name="Exercise (min)",
            marker_color='#db6d28'
        ))
        
        # 3. Exercise Calories (Line, Secondary Y)
        # Re-calc for calories (aggregated daily)
        ex_cal_daily = exercise_df.groupby(exercise_df['datetime'].dt.date)['calories'].sum().reset_index()
        fig.add_trace(go.Scatter(
            x=ex_cal_daily['datetime'],
            y=ex_cal_daily['calories'],
            name="Calories (kcal)",
            yaxis="y2",
            line=dict(color='#ff4b4b', width=3),
            mode='lines+markers'
        ))

    # Layout for Dual Axis
    fig.update_layout(
        barmode='stack', # Stack minutes
        yaxis=dict(
            title="Duration (Minutes)",
            titlefont=dict(color="#ffffff"),
            tickfont=dict(color="#ffffff")
        ),
        yaxis2=dict(
            title="Calories (Kcal)",
            titlefont=dict(color="#ff4b4b"),
            tickfont=dict(color="#ff4b4b"),
            overlaying="y",
            side="right"
        ),
        legend=dict(x=0, y=1.1, orientation="h"),
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)


    # 2. Distribution Pie Chart (UPGRADE 4) & Weight
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### Exercise Distribution")
        # Pie chart of Exercise TYPES based on Duration (Time invested)
        if not exercise_df.empty:
            pie_df = exercise_df.groupby('activity')['duration_minutes'].sum().reset_index()
            fig_pie = px.pie(
                pie_df, 
                values='duration_minutes', 
                names='activity',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No exercises recorded in this period.")

    with c2:
        st.markdown("### Weight Trend")
        if not weight_df.empty:
            weight_df_sorted = weight_df.sort_values('datetime')
            fig_line = px.line(
                weight_df_sorted, 
                x='datetime', 
                y='weight',
                markers=True
            )
            # Add target range lines
            fig_line.add_hline(y=target_weight_min, line_dash="dash", line_color="green")
            fig_line.add_hline(y=target_weight_max, line_dash="dash", line_color="green")
            
            fig_line.update_traces(line_color='#58a6ff')
            fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No weight data recorded.")
