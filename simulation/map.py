import plotly.graph_objects as go
import json
import os

def create_supply_chain_map():
    # Load the port data and simulation results
    ports_path = os.path.join(os.path.dirname(__file__), "..", "data", "ports.json")
    results_path = os.path.join(os.path.dirname(__file__), "..", "data", "results.json")
    
    with open(ports_path, "r") as f:
        nodes = json.load(f)
        
    try:
        with open(results_path, "r") as f:
            results = json.load(f)
            best_route = results.get("best_route", "").split(" → ")
            disaster_node = results.get("disaster", "")
    except FileNotFoundError:
        best_route = []
        disaster_node = ""

    fig = go.Figure()

    # Define colors and sizes for different node types
    type_styles = {
        "factory": {"color": "#00d2ff", "size": 10, "symbol": "square"},
        "backup_factory": {"color": "#3a86ff", "size": 8, "symbol": "square-open"},
        "port": {"color": "#ff006e", "size": 8, "symbol": "circle"},
        "air_hub": {"color": "#ffbe0b", "size": 10, "symbol": "triangle-up"},
        "warehouse": {"color": "#8338ec", "size": 8, "symbol": "diamond"},
        "distribution": {"color": "#fb5607", "size": 8, "symbol": "diamond-open"},
        "raw_supplier": {"color": "#8ac926", "size": 8, "symbol": "hexagon"},
        "customer": {"color": "#ffffff", "size": 10, "symbol": "star"}
    }

    # Plot Nodes
    for node_id, data in nodes.items():
        n_type = data.get("type", "port")
        style = type_styles.get(n_type, type_styles["port"])
        
        # Override style if it's the disaster node
        if node_id == disaster_node:
            marker_color = "#ff0000"
            marker_size = 15
            marker_symbol = "x"
        else:
            marker_color = style["color"]
            marker_size = style["size"]
            marker_symbol = style["symbol"]

        fig.add_trace(go.Scattergeo(
            lon=[data["lon"]],
            lat=[data["lat"]],
            text=f"{node_id}<br>Type: {n_type}<br>Country: {data.get('country', 'N/A')}",
            mode='markers+text' if marker_size > 8 else 'markers',
            textposition="top center",
            textfont=dict(color="rgba(255,255,255,0.7)", size=9),
            marker=dict(
                size=marker_size,
                color=marker_color,
                symbol=marker_symbol,
                line=dict(width=1, color="rgba(255,255,255,0.5)")
            ),
            name=n_type
        ))

    # Plot Best Route (if results exist)
    if len(best_route) > 1:
        route_lons = []
        route_lats = []
        for node in best_route:
            if node in nodes:
                route_lons.append(nodes[node]["lon"])
                route_lats.append(nodes[node]["lat"])
                
        fig.add_trace(go.Scattergeo(
            lon=route_lons,
            lat=route_lats,
            mode='lines',
            line=dict(width=3, color='#00ff00', dash='solid'),
            name="Optimal Recovery Route"
        ))

    # Map Layout styling
    fig.update_layout(
        title="Global Supply Chain War Room",
        geo=dict(
            projection_type="equirectangular",
            showland=True,
            landcolor="#1e1e1e",
            showocean=True,
            oceancolor="#0a0a0a",
            showcountries=True,
            countrycolor="#333333",
            coastlinecolor="#333333",
            bgcolor="#0a0a0a"
        ),
        paper_bgcolor="#0a0a0a",
        font=dict(color="#ffffff"),
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False
    )

    return fig

if __name__ == "__main__":
    fig = create_supply_chain_map()
    fig.show()