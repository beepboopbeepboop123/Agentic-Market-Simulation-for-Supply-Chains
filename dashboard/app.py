import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os

# Allow imports from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.map import supply_chain, simulate_disruption, run_monte_carlo
from agents.playbook import generate_playbook

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    layout="wide",
    page_title="Supply Chain War Room",
    page_icon="🚨"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("🚨 Supply Chain War Room")
st.markdown("*Drop a disaster. Get a recovery plan. Instantly.*")
st.divider()

# ─────────────────────────────────────────
# SIDEBAR — DISASTER CONTROLS
# ─────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Disaster Controls")

    disaster_node = st.selectbox(
        "Select Disrupted Location",
        [
            "Shanghai_Port",
            "Singapore_Port",
            "LA_Port",
            "Houston_Port",
            "Warehouse_California",
            "Warehouse_Texas",
        ]
    )

    source_node = st.selectbox(
        "Shipment Origin",
        ["Supplier_China", "Supplier_Vietnam", "Supplier_India"]
    )

    target_node = st.selectbox(
        "Shipment Destination",
        ["Customer_NewYork", "Customer_Chicago"]
    )

    ai_model = st.selectbox(
        "AI Model",
        ["mistral", "phi3"]
    )

    num_runs = st.slider(
        "Simulation Runs",
        min_value=100,
        max_value=1000,
        value=1000,
        step=100
    )

    run_button = st.button(
        "🚀 Run Simulation",
        use_container_width=True,
        type="primary"
    )

# ─────────────────────────────────────────
# MAIN PANELS
# ─────────────────────────────────────────

col1, col2, col3 = st.columns([1.2, 1, 1.2])

with col1:
    st.subheader("🗺️ Supply Chain Map")
    map_placeholder = st.empty()

with col2:
    st.subheader("📊 Simulation Results")
    chart_placeholder = st.empty()
    stats_placeholder = st.empty()

with col3:
    st.subheader("📋 Recovery Playbook")
    playbook_placeholder = st.empty()


# ─────────────────────────────────────────
# DRAW MAP FUNCTION
# ─────────────────────────────────────────

def draw_map(closed_node=None, best_route=None):

    # Node positions
    pos = {
        "Supplier_China":       (0,   3),
        "Supplier_Vietnam":     (0,   2),
        "Supplier_India":       (0,   1),
        "Shanghai_Port":        (2,   3.5),
        "Singapore_Port":       (2,   2),
        "Mumbai_Port":          (2,   0.5),
        "LA_Port":              (4,   3),
        "Houston_Port":         (4,   1.5),
        "Warehouse_California": (6,   3),
        "Warehouse_Texas":      (6,   1.5),
        "Customer_NewYork":     (8,   3),
        "Customer_Chicago":     (8,   1.5),
    }

    node_colors = {
        "supplier":  "#4CAF50",
        "port":      "#2196F3",
        "warehouse": "#FF9800",
        "customer":  "#9C27B0",
    }

    # Build best route set for highlighting
    best_route_edges = set()
    if best_route:
        route_nodes = best_route.split(" → ")
        for i in range(len(route_nodes) - 1):
            best_route_edges.add((route_nodes[i], route_nodes[i+1]))

    fig = go.Figure()

    # Draw edges
    for u, v in supply_chain.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        if closed_node and (u == closed_node or v == closed_node):
            color, width, dash = "#F44336", 1, "dash"
        elif (u, v) in best_route_edges:
            color, width, dash = "#00E676", 3, "solid"
        else:
            color, width, dash = "#555555", 1, "solid"

        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(color=color, width=width, dash=dash),
            hoverinfo="none",
            showlegend=False
        ))

    # Draw nodes
    for node, (x, y) in pos.items():
        if node not in supply_chain.nodes():
            continue

        ntype = supply_chain.nodes[node].get('type', 'port')
        color = "#F44336" if node == closed_node else node_colors.get(ntype, "#888")
        symbol = "x" if node == closed_node else "circle"

        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(size=18, color=color, symbol=symbol),
            text=[node.replace("_", " ")],
            textposition="top center",
            textfont=dict(size=8, color="white"),
            hovertext=f"{node} ({ntype})",
            hoverinfo="text",
            showlegend=False
        ))

    fig.update_layout(
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        margin=dict(l=0, r=0, t=10, b=10),
        height=380,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    return fig


# ─────────────────────────────────────────
# INITIAL MAP (before any simulation)
# ─────────────────────────────────────────

map_placeholder.plotly_chart(draw_map(), use_container_width=True)
chart_placeholder.info("Run a simulation to see results.")
playbook_placeholder.info("Run a simulation to see the playbook.")


# ─────────────────────────────────────────
# RUN SIMULATION ON BUTTON CLICK
# ─────────────────────────────────────────

if run_button:

    # ── Step 1: Update map with disaster ──
    map_placeholder.plotly_chart(
        draw_map(closed_node=disaster_node),
        use_container_width=True
    )

    # ── Step 2: Run simulation ─────────────
    with st.spinner(f"Running {num_runs} simulations..."):
        run_monte_carlo(
            closed_node=disaster_node,
            source=source_node,
            target=target_node,
            runs=num_runs
        )

    # ── Step 3: Load results ───────────────
    with open("data/results.json", "r") as f:
        results = json.load(f)

    # ── Step 4: Show charts ────────────────
    if "route_summary" in results:
        routes      = list(results["route_summary"].keys())
        short_names = [r.split(" → ")[2] + " route" for r in routes]
        avg_days    = [results["route_summary"][r]["avg_days"] for r in routes]
        avg_costs   = [results["route_summary"][r]["avg_cost"] for r in routes]
        success     = [float(results["route_summary"][r]["success_rate"].replace("%","")) for r in routes]

        df = pd.DataFrame({
            "Route":        short_names,
            "Avg Days":     avg_days,
            "Avg Cost ($)": avg_costs,
            "Success (%)":  success
        })

        fig_bar = px.bar(
            df, x="Route", y="Avg Days",
            color="Avg Days",
            color_continuous_scale="RdYlGn_r",
            title="Average Recovery Days per Route"
        )
        fig_bar.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font_color="white",
            height=220,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False
        )
        chart_placeholder.plotly_chart(fig_bar, use_container_width=True)
        stats_placeholder.dataframe(df, use_container_width=True)

    # ── Step 5: Update map with best route ─
    best_route = results.get("best_route", None)
    map_placeholder.plotly_chart(
        draw_map(closed_node=disaster_node, best_route=best_route),
        use_container_width=True
    )

    # ── Step 6: Generate playbook ──────────
    with st.spinner("AI is writing your recovery playbook..."):
        playbook = generate_playbook(model=ai_model)

    playbook_placeholder.markdown(
        f"""
        <div style='background:#1a1a2e; padding:15px;
        border-radius:8px; color:white;
        font-size:13px; height:380px;
        overflow-y:scroll; line-height:1.6'>
        {playbook.replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.success("✅ Simulation complete. Playbook ready.")