import streamlit as st
import uuid
import pandas as pd
import sqlite3
import time
import base64
from graph import app_graph, DB_NAME

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

config = {"configurable": {"thread_id": st.session_state.thread_id}}

def encode_image(uploaded_file):
    """Converts uploaded file to Base64 string for the AI"""
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

st.set_page_config(page_title="AI Moderator", layout="wide")
st.title("AI Content Moderation System")
tab1, tab2 = st.tabs(["Live Pipeline", "Analytics Dashboard"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Input Channel")
        
        # Image Uploader
        uploaded_file = st.file_uploader("Upload Image (Optional)", type=['jpg', 'png', 'jpeg'])
        
        # Text Input
        user_input = st.text_area("Or type text content...", height=100)
        
        if st.button("Analyze Content", type="primary"):
            
            initial_state = {}
            has_input = False

            # Priority 1: Check Image
            if uploaded_file:
                st.info("Processing Image...")
                b64_image = encode_image(uploaded_file)
                # Clear text content to ensure router goes to image node
                initial_state = {"content": "[IMAGE]", "image_base64": b64_image, "decision": "PENDING"}
                has_input = True
                
            # Priority 2: Check Text
            elif user_input:
                st.info("Processing Text...")
                initial_state = {"content": user_input, "image_base64": None, "decision": "PENDING"}
                has_input = True
            
            else:
                st.warning("Please upload an image or type text.")

            if has_input:
                with st.spinner("AI Agents working..."):
                    for event in app_graph.stream(initial_state, config):
                        pass
                st.rerun()

    with col2:
        st.subheader("Decision Engine")
        current = app_graph.get_state(config)
        
        if current.values:
            data = current.values
            status = data.get("decision", "PENDING")
            reason = data.get("reason", "Processing...")
            severity = data.get("severity", 0)

            if data.get("image_base64"):
                st.image(f"data:image/jpeg;base64,{data['image_base64']}", caption="Analyzed Image", width=300)
            
            # Metric Badges
            m1, m2, m3 = st.columns(3)
            m1.metric("Status", status)
            m2.metric("Severity", f"{severity}/5")
            m3.metric("Layer", "Judge" if severity < 5 else "Guard")

            # Status Alert
            if status == "BLOCK":
                st.error(f"BLOCKED: {reason}")
            elif status == "APPROVE":
                st.success(f"APPROVED: {reason}")
            elif status == "ESCALATE":
                st.warning(f"ESCALATED: {reason}")
                
                # Human Buttons
                c1, c2 = st.columns(2)
                if c1.button("Override: Approve"):
                    app_graph.update_state(config, {"decision": "APPROVE", "reason": "Admin Override"})
                    st.rerun()
                if c2.button("Confirm: Block"):
                    app_graph.update_state(config, {"decision": "BLOCK", "reason": "Admin Confirmed"})
                    st.rerun()

with tab2:
    st.header("Real-Time Monitoring")
    
    # Auto-refresh button
    if st.button("Refresh Data"):
        st.rerun()

    try:
        # Load Data
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM logs", conn)
        conn.close()
        
        if not df.empty:
            # Convert timestamp string to datetime object for sorting/graphing
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # TOP ROW: KPI CARDS
            k1, k2, k3, k4 = st.columns(4)
            total_reqs = len(df)
            blocked_count = len(df[df['decision'] == 'BLOCK'])
            block_rate = (blocked_count / total_reqs) * 100
            
            k1.metric("Total Traffic", f"{total_reqs}", delta="Requests")
            k2.metric("Block Rate", f"{block_rate:.1f}%", delta_color="inverse")
            k3.metric("Escalations", len(df[df['decision'] == 'ESCALATE']), delta_color="off")
            
            # Calculate "Last Hour" traffic for the live feel
            last_hour = df[df['timestamp'] > (pd.Timestamp.now() - pd.Timedelta(hours=1))]
            k4.metric("Last Hour", len(last_hour), "Active")

            # GRAPH ROW
            st.divider()
            c1, c2 = st.columns([1, 2]) # 1/3 width vs 2/3 width
            
            with c1:
                st.subheader("Decision Ratio")
                # GRAPH 1: DONUT CHART (Using Altair)
                import altair as alt
                
                # Prepare data for donut
                donut_data = df['decision'].value_counts().reset_index()
                donut_data.columns = ['decision', 'count']
                
                base = alt.Chart(donut_data).encode(
                    theta=alt.Theta("count", stack=True)
                )
                
                pie = base.mark_arc(outerRadius=110, innerRadius=70).encode(
                    color=alt.Color("decision", scale=alt.Scale(
                        domain=['APPROVE', 'BLOCK', 'ESCALATE'],
                        range=['#28a745', '#dc3545', '#ffc107']  # Green, Red, Yellow
                    )),
                    order=alt.Order("count", sort="descending"),
                    tooltip=["decision", "count"]
                )
                
                text = base.mark_text(radius=140).encode(
                    text="count",
                    order=alt.Order("count", sort="descending"),
                    color=alt.value("white")
                )
                
                st.altair_chart(pie + text, width='stretch')

            with c2:
                st.subheader("Traffic Trend (Last 24 Hours)")
                # GRAPH 2: TIME SERIES AREA CHART
                
                # Group by hour (or minute) to see spikes
                # We create a new column just for plotting: rounded to nearest 10 min
                df['time_chunk'] = df['timestamp'].dt.floor('10min')
                trend_data = df.groupby(['time_chunk', 'decision']).size().reset_index(name='count')
                
                area_chart = alt.Chart(trend_data).mark_area(opacity=0.6).encode(
                    x=alt.X('time_chunk', title='Time'),
                    y=alt.Y('count', title='Requests'),
                    color=alt.Color('decision', scale=alt.Scale(
                        domain=['APPROVE', 'BLOCK', 'ESCALATE'],
                        range=['#28a745', '#dc3545', '#ffc107']
                    ))
                ).interactive()
                
                st.altair_chart(area_chart, width='stretch')

            # Audit Logs
            st.divider()
            st.subheader("Recent Audit Logs")
            st.dataframe(
                df.sort_values(by='timestamp', ascending=False)[['timestamp', 'content', 'decision', 'reason']],
                width='stretch',
                hide_index=True
            )
            
        else:
            st.info("Waiting for data... Go to the 'Live Pipeline' tab and submit some text!")
            
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
