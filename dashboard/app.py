import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.map import supply_chain, simulate_disruption, run_monte_carlo
from simulation.real_ports import REAL_PORTS
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
    h1 { color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("🚨 Supply Chain War Room")
st.markdown("*Drop a disaster. Get a recovery plan. Instantly.*")
st.divider()

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Disaster Controls")

    disaster_options = [
        n for n, d in REAL_PORTS.items()
        if d["type"] == "port"
    ]

    source_options = [
        n for n, d in REAL_PORTS.items()
        if d["type"] == "supplier"
    ]

    target_options = [
        n for n, d in REAL_PORTS.items()
        if d["type"] == "customer"
    ]

    disaster_node = st.selectbox("🔴 Disrupted Location",   disaster_options)
    source_node   = st.selectbox("📦 Shipment Origin",      source_options)
    target_node   = st.selectbox("🏁 Shipment Destination", target_options)
    ai_model      = st.selectbox("🤖 AI Model",             ["mistral", "phi3"])
    num_runs      = st.slider("🔁 Simulation Runs", 100, 1000, 1000, 100)

    st.divider()
    run_button = st.button(
        "🚀 Run Simulation",
        use_container_width=True,
        type="primary"
    )

    if disaster_node in REAL_PORTS:
        info = REAL_PORTS[disaster_node]
        st.divider()
        st.markdown(f"""
        **Selected Port Info**
        - 📍 Country: {info['country']}
        - 🌐 Lat: {info['lat']}
        - 🌐 Lon: {info['lon']}
        - 🏷️ Type: {info['type']}
        """)

# ─────────────────────────────────────────
# MAIN PANELS
# ─────────────────────────────────────────

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("🗺️ Live Supply Chain World Map")
    map_placeholder = st.empty()

with col2:
    st.subheader("📊 Simulation Results")
    chart_placeholder = st.empty()
    stats_placeholder = st.empty()

st.divider()
st.subheader("📋 AI Recovery Playbook")
playbook_placeholder = st.empty()


# ─────────────────────────────────────────
# DRAW REAL WORLD MAP
# ─────────────────────────────────────────

def draw_world_map(closed_node=None, best_route=None):

    fig = go.Figure()

    # Parse best route edges
    best_route_edges = set()
    if best_route:
        route_nodes = best_route.split(" → ")
        for i in range(len(route_nodes) - 1):
            best_route_edges.add((route_nodes[i], route_nodes[i+1]))

    # Draw all shipping routes
    for u, v in supply_chain.edges():
        if u not in REAL_PORTS or v not in REAL_PORTS:
            continue

        lat0 = REAL_PORTS[u]["lat"]
        lon0 = REAL_PORTS[u]["lon"]
        lat1 = REAL_PORTS[v]["lat"]
        lon1 = REAL_PORTS[v]["lon"]

        if closed_node and (u == closed_node or v == closed_node):
            color, width, dash = "red", 1, "dash"
        elif (u, v) in best_route_edges:
            color, width, dash = "#00E676", 3, "solid"
        else:
            color, width, dash = "rgba(100,100,200,0.3)", 1, "solid"

        fig.add_trace(go.Scattergeo(
            lat       = [lat0, lat1],
            lon       = [lon0, lon1],
            mode      = "lines",
            line      = dict(width=width, color=color, dash=dash),
            hoverinfo = "none",
            showlegend = False
        ))

    # Node colors by type
    type_colors = {
        "supplier":  "#4CAF50",
        "port":      "#2196F3",
        "warehouse": "#FF9800",
        "customer":  "#9C27B0",
    }

    # Draw nodes grouped by type
    for node_type, color in type_colors.items():
        lats, lons, texts, hovers = [], [], [], []

        for node, attrs in REAL_PORTS.items():
            if attrs["type"] != node_type:
                continue
            if node not in supply_chain.nodes():
                continue

            lats.append(attrs["lat"])
            lons.append(attrs["lon"])
            texts.append(node.replace("_", " "))

            edges_out = list(supply_chain.successors(node))
            hover     = f"<b>{node.replace('_',' ')}</b><br>"
            hover    += f"Country: {attrs['country']}<br>"
            hover    += f"Type: {node_type}<br>"
            if edges_out:
                hover += f"Connects to: {len(edges_out)} routes"
            hovers.append(hover)

        node_color = [
            "#F44336" if t.replace(" ", "_") == closed_node else color
            for t in texts
        ]

        fig.add_trace(go.Scattergeo(
            lat          = lats,
            lon          = lons,
            mode         = "markers+text",
            marker       = dict(
                size     = 10,
                color    = node_color,
                line     = dict(width=1, color="white")
            ),
            text         = texts,
            textposition = "top right",
            textfont     = dict(size=8, color="white"),
            hovertext    = hovers,
            hoverinfo    = "text",
            name         = node_type.capitalize(),
            showlegend   = True
        ))

    fig.update_layout(
        paper_bgcolor = "#0e1117",
        plot_bgcolor  = "#0e1117",
        margin        = dict(l=0, r=0, t=10, b=0),
        height        = 500,
        legend        = dict(
            bgcolor   = "rgba(0,0,0,0.5)",
            font      = dict(color="white"),
            x         = 0.01,
            y         = 0.99
        ),
        geo = dict(
            scope           = "world",
            projection_type = "natural earth",
            showland        = True,
            landcolor       = "rgb(40, 40, 60)",
            showocean       = True,
            oceancolor      = "rgb(20, 20, 40)",
            showcoastlines  = True,
            coastlinecolor  = "rgb(80, 80, 100)",
            showcountries   = True,
            countrycolor    = "rgb(60, 60, 80)",
            showframe       = False,
            bgcolor         = "#0e1117",
        )
    )

    return fig


# ─────────────────────────────────────────
# INITIAL MAP
# ─────────────────────────────────────────

map_placeholder.plotly_chart(
    draw_world_map(),
    use_container_width=True
)
chart_placeholder.info("Run a simulation to see results.")
playbook_placeholder.info("Run a simulation to see the AI recovery playbook.")


# ─────────────────────────────────────────
# RUN ON BUTTON CLICK
# ─────────────────────────────────────────

if run_button:

    # Step 1 — Show disaster on map
    map_placeholder.plotly_chart(
        draw_world_map(closed_node=disaster_node),
        use_container_width=True
    )

    # Step 2 — Run simulation
    with st.spinner(f"⚙️ Running {num_runs} simulations..."):
        run_monte_carlo(
            closed_node = disaster_node,
            source      = source_node,
            target      = target_node,
            runs        = num_runs
        )

    # Step 3 — Load results
    with open("data/results.json", "r", encoding="utf-8") as f:
        results = json.load(f)

    # Step 4 — Show charts
    if "route_summary" in results and results["route_summary"]:

        routes      = list(results["route_summary"].keys())
        short_names = [f"Route {i+1}" for i in range(len(routes))]
        avg_days    = [results["route_summary"][r]["avg_days"] for r in routes]
        avg_costs   = [results["route_summary"][r]["avg_cost"] for r in routes]
        success     = [
            float(results["route_summary"][r]["success_rate"].replace("%", ""))
            for r in routes
        ]

        df = pd.DataFrame({
            "Route":        short_names,
            "Full Path":    [r[:60] + "..." for r in routes],
            "Avg Days":     avg_days,
            "Avg Cost ($)": avg_costs,
            "Success (%)":  success
        })

        fig_bar = px.bar(
            df, x="Route", y="Avg Days",
            color                  = "Avg Days",
            color_continuous_scale = "RdYlGn_r",
            title                  = "Average Recovery Days per Route",
            hover_data             = ["Full Path", "Avg Cost ($)"]
        )
        fig_bar.update_layout(
            paper_bgcolor = "#0e1117",
            plot_bgcolor  = "#0e1117",
            font_color    = "white",
            height        = 300,
            margin        = dict(l=0, r=0, t=40, b=0),
            showlegend    = False
        )
        chart_placeholder.plotly_chart(
            fig_bar,
            use_container_width=True
        )
        stats_placeholder.dataframe(
            df[["Route", "Avg Days", "Avg Cost ($)", "Success (%)"]],
            use_container_width=True
        )

    # Step 5 — Update map with best route
    best_route = results.get("best_route", None)
    map_placeholder.plotly_chart(
        draw_world_map(
            closed_node = disaster_node,
            best_route  = best_route,
        ),
        use_container_width=True
    )

    # Step 6 — Generate AI playbook
    with st.spinner("🤖 AI is writing your recovery playbook..."):
        playbook = generate_playbook(model=ai_model)

    playbook_placeholder.markdown(
        f"""
        <div style='background:#1a1a2e; padding:20px;
        border-radius:10px; color:#e0e0e0;
        font-size:14px; line-height:1.8;
        border: 1px solid #333;'>
        {playbook.replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Step 7 — Summary metrics
    st.divider()
    m1, m2, m3, m4 = st.columns(4)

    try:
        all_paths   = list(nx.all_simple_paths(
            supply_chain, source_node, target_node, cutoff=8
        ))
        normal_days = min(
            sum(supply_chain[p][q]['days']
                for p, q in zip(path[:-1], path[1:]))
            for path in all_paths
        ) if all_paths else 0
    except:
        normal_days = 0

    m1.metric("🔴 Disaster",      disaster_node.replace("_", " "))
    m2.metric("⏱️ Normal Route",  f"{round(normal_days, 1)} days")
    m3.metric("🏆 Best Recovery", f"{results['best_avg_days']} days")
    m4.metric("💰 Recovery Cost", f"${results['best_avg_cost']:,}")

    st.success("✅ Simulation complete. Playbook ready.")