import os
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Browser Leak Sentinel | DevTools Telemetry",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom high-contrast CSS styling tailored for desktop and mobile LinkedIn video previews
st.markdown("""
<style>
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    .stApp { 
        background-color: #0b0f14; 
        color: #ffffff; 
    }
    
    /* Prominent Emerald Green Header */
    .main-title {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 32px; /* Increased font size for impactful visual telemetry */
        font-weight: 800;
        color: #00E676; /* Vibrant Emerald Green */
        letter-spacing: -0.3px;
        margin-bottom: 2px;
    }
    .main-subtitle {
        font-size: 13.5px;
        color: #e6edf3;
        margin-bottom: 12px;
        font-weight: 500;
        letter-spacing: 0.2px;
    }

    /* Enterprise Metric Card Scaffolding */
    .metric-card {
        background-color: #121820;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 6px;
    }
    .metric-title { 
        font-size: 12px; 
        color: #ffffff !important; 
        text-transform: uppercase; 
        font-weight: 800; 
        letter-spacing: 0.8px; 
    }
    .metric-val { 
        font-size: 28px; 
        font-weight: 800; 
        color: #58a6ff; 
        margin: 3px 0; 
        font-family: 'Consolas', monospace;
    }
    
    /* Sub-text forced to crisp pure white for mobile feed clarity */
    .metric-sub { 
        font-size: 13px; 
        color: #ffffff !important; 
        font-weight: 700; 
        opacity: 0.95;
    }
    
    /* Alert dynamic borders and badges */
    .leak-danger { border-left: 5px solid #ff4b4b !important; }
    .leak-text-danger { color: #ff4b4b !important; }
    .leak-sub-danger { color: #ff6b6b !important; font-weight: 800; }

    /* Alert Banner */
    .banner-danger {
        background-color: rgba(255, 75, 75, 0.16);
        border: 1.5px solid #ff4b4b;
        color: #ffffff;
        padding: 9px 16px;
        border-radius: 6px;
        font-size: 13.5px;
        font-weight: 600;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "reports", "live_telemetry.csv")

st.markdown('<div class="main-title">⚡ Browser Leak Sentinel — Runtime Memory Profiler</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Playwright Chrome DevTools Protocol (CDP) • Live JS Heap & Retained DOM Engine</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Profiler Controls")
    refresh_rate = st.slider("Telemetry Refresh Rate (sec)", 0.5, 2.0, 1.0)
    auto_refresh = st.checkbox("Live Auto-Refresh", value=True)
    st.markdown("---")
    st.markdown("### 🎯 Architecture Overview")
    st.markdown("- **Engine:** Playwright Async CDP")
    st.markdown("- **API:** `Performance.getMetrics`")
    st.markdown("- **Target:** Detached DOM Tree Retention")
    st.markdown("- **Detection:** Heap Slope Analysis")

placeholder = st.empty()
iteration_counter = 0

while auto_refresh:
    iteration_counter += 1
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0:
        try:
            df = pd.read_csv(CSV_FILE)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    with placeholder.container():
        if df.empty or len(df) == 0:
            st.info("⏳ Waiting for telemetry stream... Run `python app/profiler_engine.py` in your terminal.")
        else:
            current_heap = float(df["js_heap_used_mb"].iloc[-1])
            initial_heap = float(df["js_heap_used_mb"].iloc[0])
            heap_growth = round(current_heap - initial_heap, 2)
            current_nodes = int(df["dom_nodes"].iloc[-1])
            initial_nodes = int(df["dom_nodes"].iloc[0])
            node_growth = int(current_nodes - initial_nodes)
            total_steps = int(df["step"].iloc[-1])

            is_critical = heap_growth > 5.0 or node_growth > 5000

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">JS Heap (Current)</div>
                    <div class="metric-val">{current_heap:.1f} MB</div>
                    <div class="metric-sub">Allocated: {df['js_heap_total_mb'].iloc[-1]:.1f} MB</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                danger_class = "leak-danger" if is_critical else ""
                val_color = "leak-text-danger" if is_critical else ""
                sub_color = "leak-sub-danger" if is_critical else "metric-sub"
                status_text = "CRITICAL SLOPE" if is_critical else "STABLE BASELINE"
                st.markdown(f"""
                <div class="metric-card {danger_class}">
                    <div class="metric-title">Heap Growth (Delta)</div>
                    <div class="metric-val {val_color}">+{heap_growth:.2f} MB</div>
                    <div class="metric-sub {sub_color}">{status_text}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                danger_class = "leak-danger" if is_critical else ""
                val_color = "leak-text-danger" if is_critical else ""
                sub_color = "leak-sub-danger" if is_critical else "metric-sub"
                st.markdown(f"""
                <div class="metric-card {danger_class}">
                    <div class="metric-title">Active DOM Nodes</div>
                    <div class="metric-val {val_color}">{current_nodes:,}</div>
                    <div class="metric-sub {sub_color}">Detached: +{node_growth:,} nodes</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Automated Actions</div>
                    <div class="metric-val" style="color: #58a6ff;">{total_steps}</div>
                    <div class="metric-sub">Listeners: {int(df['js_event_listeners'].iloc[-1])}</div>
                </div>
                """, unsafe_allow_html=True)

            if is_critical:
                st.markdown(f"""
                <div class="banner-danger">
                    🚨 <b>HIGH-CONFIDENCE LEAK DETECTED:</b> Heap inflated by <b>+{heap_growth:.2f} MB</b> across {total_steps} actions with <b>{node_growth:,}</b> retained detached DOM nodes!
                </div>
                """, unsafe_allow_html=True)

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                fig_heap = go.Figure()
                fig_heap.add_trace(go.Scatter(
                    x=df["step"],
                    y=df["js_heap_used_mb"],
                    mode="lines+markers",
                    name="Heap Used",
                    line=dict(color="#ff4b4b" if is_critical else "#00E676", width=2.5),
                    marker=dict(size=4),
                    fill="tozeroy",
                    fillcolor="rgba(255, 75, 75, 0.15)" if is_critical else "rgba(0, 230, 118, 0.15)"
                ))
                fig_heap.update_layout(
                    title=dict(text="<b>JS Heap Used vs Action Iterations</b>", font=dict(size=14, color="#ffffff")),
                    template="plotly_dark",
                    paper_bgcolor="#121820",
                    plot_bgcolor="#121820",
                    height=325,
                    margin=dict(l=15, r=15, t=32, b=15),
                    xaxis=dict(title="Steps / Actions", gridcolor="#21262d", zeroline=False, title_font=dict(color="#ffffff"), tickfont=dict(color="#ffffff")),
                    yaxis=dict(title="Memory (MB)", gridcolor="#21262d", zeroline=False, title_font=dict(color="#ffffff"), tickfont=dict(color="#ffffff")),
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig_heap, use_container_width=True, key=f"heap_chart_{iteration_counter}")

            with col_chart2:
                fig_nodes = go.Figure()
                fig_nodes.add_trace(go.Scatter(
                    x=df["step"],
                    y=df["dom_nodes"],
                    mode="lines+markers",
                    name="DOM Nodes",
                    line=dict(color="#ffb74d", width=2.5),
                    marker=dict(size=4)
                ))
                fig_nodes.update_layout(
                    title=dict(text="<b>DOM Node Retention (Detached Elements)</b>", font=dict(size=14, color="#ffffff")),
                    template="plotly_dark",
                    paper_bgcolor="#121820",
                    plot_bgcolor="#121820",
                    height=325,
                    margin=dict(l=15, r=15, t=32, b=15),
                    xaxis=dict(title="Steps / Actions", gridcolor="#21262d", zeroline=False, title_font=dict(color="#ffffff"), tickfont=dict(color="#ffffff")),
                    yaxis=dict(title="Node Count", gridcolor="#21262d", zeroline=False, title_font=dict(color="#ffffff"), tickfont=dict(color="#ffffff")),
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig_nodes, use_container_width=True, key=f"nodes_chart_{iteration_counter}")

    time.sleep(refresh_rate)