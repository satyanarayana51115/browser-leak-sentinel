import os
import sys
import subprocess
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Browser Leak Sentinel | Runtime Profiler",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# High-Contrast Mobile Optimized Theme
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 4.2rem;
        padding-bottom: 0.8rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .header-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #00E676;
        letter-spacing: -0.5px;
        margin-top: 6px;
        margin-bottom: 2px;
        line-height: 1.35;
    }
    .header-sub {
        font-size: 0.92rem;
        font-weight: 600;
        color: #8b949e;
        margin-bottom: 1.0rem;
    }
    .metric-card {
        background-color: #121820;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3);
    }
    .metric-card-alert {
        background-color: #121820;
        border: 2px solid #ff7b72;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 4px 14px rgba(255, 123, 114, 0.2);
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    .metric-value-blue {
        font-size: 1.85rem;
        font-weight: 800;
        color: #58a6ff;
        margin-top: 3px;
        margin-bottom: 3px;
    }
    .metric-value-orange {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ff9b5e;
        margin-top: 3px;
        margin-bottom: 3px;
    }
    .metric-sub-white {
        font-size: 0.8rem;
        font-weight: 600;
        color: #ffffff;
    }
    .metric-sub-danger {
        font-size: 0.8rem;
        font-weight: 700;
        color: #ff7b72;
    }
    .alert-banner {
        background-color: #181114;
        border: 1.5px solid #ff4b4b;
        border-radius: 6px;
        padding: 8px 16px;
        color: #ffffff;
        font-weight: 600;
        font-size: 0.88rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }
    .alert-banner strong {
        color: #ff6b6b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

METRICS_FILE = os.path.join(os.path.dirname(__file__), "..", "reports", "live_telemetry.csv")
ENGINE_SCRIPT = os.path.join(os.path.dirname(__file__), "profiler_engine.py")

# Sidebar Controls
st.sidebar.markdown("### ⚙️ Profiler Controls")

# Single-Click Profiler Launcher
if st.sidebar.button("▶️ Start Live Profiler Run", type="primary", use_container_width=True):
    if os.path.exists(METRICS_FILE):
        try:
            os.remove(METRICS_FILE)
        except Exception:
            pass
    subprocess.Popen([sys.executable, ENGINE_SCRIPT])
    st.sidebar.success("🚀 Profiler started! Telemetry streaming...")

st.sidebar.markdown("---")
refresh_rate = st.sidebar.slider("Telemetry Refresh Rate (sec)", min_value=0.5, max_value=2.0, value=1.0, step=0.25)
auto_refresh = st.sidebar.checkbox("Live Auto-Refresh", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **🎯 Architecture Overview**
    - **Engine:** Playwright Async CDP
    - **API:** `Performance.getMetrics`
    - **Target:** Detached DOM Tree Retention
    - **Detection:** Heap Slope Analysis
    """
)

# Header Section
st.markdown('<div class="header-title">⚡ Browser Leak Sentinel — Runtime Memory Profiler</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Playwright Chrome DevTools Protocol (CDP) • Live JS Heap & Retained DOM Engine</div>', unsafe_allow_html=True)

# Dedicated Single Viewport Container to prevent duplicate renders
dashboard_container = st.empty()

# Load CSV Telemetry
df = pd.DataFrame()
if os.path.exists(METRICS_FILE):
    try:
        df = pd.read_csv(METRICS_FILE)
    except Exception:
        pass

with dashboard_container.container():
    if not df.empty and len(df) > 0:
        latest = df.iloc[-1]
        first = df.iloc[0]

        current_heap = latest.get("js_heap_used_mb", 0.0)
        total_heap = latest.get("js_heap_total_mb", 0.0)
        current_nodes = int(latest.get("dom_nodes", 0))
        listeners = int(latest.get("js_event_listeners", 0))
        step = int(latest.get("step", len(df)))

        initial_heap = first.get("js_heap_used_mb", current_heap)
        heap_delta = round(current_heap - initial_heap, 2)
        initial_nodes = int(first.get("dom_nodes", current_nodes))
        nodes_delta = current_nodes - initial_nodes

        is_leaking = heap_delta > 100 or nodes_delta > 50000

        # Top Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">JS HEAP (CURRENT)</div>
                    <div class="metric-value-blue">{current_heap} MB</div>
                    <div class="metric-sub-white">Allocated: {total_heap} MB</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            card_class = "metric-card-alert" if is_leaking else "metric-card"
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="metric-label">HEAP GROWTH (DELTA)</div>
                    <div class="metric-value-orange">+{heap_delta} MB</div>
                    <div class="metric-sub-danger">CRITICAL SLOPE</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="metric-label">ACTIVE DOM NODES</div>
                    <div class="metric-value-orange">{current_nodes:,}</div>
                    <div class="metric-sub-danger">Detached: +{nodes_delta:,} nodes</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">AUTOMATED ACTIONS</div>
                    <div class="metric-value-blue">{step}</div>
                    <div class="metric-sub-white">Listeners: {listeners}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Sentinel Alert Banner
        if is_leaking:
            st.markdown(
                f"""
                <div class="alert-banner">
                    🚨 <strong>HIGH-CONFIDENCE LEAK DETECTED:</strong> Heap inflated by +{heap_delta} MB across {step} actions with {nodes_delta:,} retained detached DOM nodes!
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Visual Charts with Restored Markers (Dots)
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            fig_heap = go.Figure()
            fig_heap.add_trace(
                go.Scatter(
                    x=df["step"],
                    y=df["js_heap_used_mb"],
                    mode="lines+markers",
                    name="Heap Used",
                    line=dict(color="#ff5555", width=2.5),
                    marker=dict(size=6, color="#ffffff"),
                )
            )
            fig_heap.update_layout(
                title=dict(text="<b>JS Heap Used vs Action Iterations</b>", font=dict(color="#ffffff", size=13)),
                template="plotly_dark",
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                height=320,
                margin=dict(l=35, r=15, t=35, b=25),
                xaxis=dict(title="Steps / Actions", gridcolor="#21262d", zeroline=False),
                yaxis=dict(title="Memory (MB)", gridcolor="#21262d", zeroline=False),
            )
            st.plotly_chart(fig_heap, use_container_width=True)

        with chart_col2:
            fig_dom = go.Figure()
            fig_dom.add_trace(
                go.Scatter(
                    x=df["step"],
                    y=df["dom_nodes"],
                    mode="lines+markers",
                    name="DOM Nodes",
                    line=dict(color="#e3b341", width=2.5),
                    marker=dict(size=6, color="#ffffff"),
                )
            )
            fig_dom.update_layout(
                title=dict(text="<b>DOM Node Retention (Detached Elements)</b>", font=dict(color="#ffffff", size=13)),
                template="plotly_dark",
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                height=320,
                margin=dict(l=35, r=15, t=35, b=25),
                xaxis=dict(title="Steps / Actions", gridcolor="#21262d", zeroline=False),
                yaxis=dict(title="Node Count", gridcolor="#21262d", zeroline=False),
            )
            st.plotly_chart(fig_dom, use_container_width=True)

    else:
        st.info("Awaiting telemetry stream... Click '▶️ Start Live Profiler Run' in the sidebar.")

# Auto-Refresh Loop
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()