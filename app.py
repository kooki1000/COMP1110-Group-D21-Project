"""
app.py
------
Smart HKU Transport Advisor — with map version.
Run with:  python -m streamlit run app.py
"""

import os
import sys
import streamlit as st
import folium
from streamlit_folium import st_folium

from network_loader import load_network
from journey_finder import find_all_journeys
from scorer import rank_journeys
from validator import validate_query, validate_journey_results

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

st.set_page_config(
    page_title="Smart HKU Transport Navigator",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
/* GLOBAL STYLES */
html, body, [data-testid="stAppViewContainer"] { background: #f8fafc !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
footer { display: none !important; }
.block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; max-width: 98% !important; }

body, p, span, div, label, li, h1, h2, h3, h4, h5, h6,
.stMarkdown, .stMarkdown *, [data-testid="stMarkdownContainer"] *,
[data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] *,
.element-container { color: #0f172a !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important; }

/* ALL STANDARD BUTTONS (e.g., Show on Map) */
.stButton > button {
    background-color: white !important;
    color: #475569 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all .2s ease !important;
}
.stButton > button:hover {
    border-color: #94a3b8 !important;
    color: #0f172a !important;
    background-color: #f1f5f9 !important;
}

/* PRIMARY CALL-TO-ACTION BUTTON (Find Routes) */
[data-testid="baseButton-primary"],
[data-testid="baseButton-primary"] * {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    padding: 12px 0 !important;
    margin-top: 4px !important;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2), 0 2px 4px -1px rgba(37, 99, 235, 0.1) !important;
    transition: all 0.2s ease !important;
}
[data-testid="baseButton-primary"]:hover { 
    background-color: #1d4ed8 !important; 
    box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.3), 0 4px 6px -1px rgba(37, 99, 235, 0.15) !important;
    transform: translateY(-1px);
}
[data-testid="baseButton-primary"]:active {
    transform: translateY(0);
}

/* INPUT SELECTBOXES */
[data-baseweb="select"] > div {
    background-color: #f1f5f9 !important; 
    color: #1e293b !important; 
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
[data-baseweb="select"] > div:hover {
    border-color: #cbd5e1 !important;
}
[data-baseweb="select"] > div > div {
    background-color: transparent !important; 
}
[data-baseweb="popover"] *, [data-baseweb="menu"] *,
[role="option"], [data-baseweb="option"] {
    background-color: white !important; color: #0f172a !important;
}
[role="option"]:hover, [data-baseweb="option"]:hover { background-color: #f1f5f9 !important; }

/* SEGMENTED CONTROL (ROUTE PREFERENCE) */
[data-testid="stRadio"] { margin-bottom: 2px; }
[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] > div[role="radiogroup"] {
    display: grid !important;
    grid-template-columns: 1fr 1fr 1fr !important;
    background: #f1f5f9;
    padding: 6px;
    border-radius: 10px;
    gap: 6px !important;
    border: 1px solid #e2e8f0;
}
[data-testid="stRadio"] label[data-baseweb="radio"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    margin: 0 !important;
    padding: 6px 4px !important;
    min-height: 48px !important;
    border-radius: 8px !important;
    border: 1px solid transparent !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

[data-testid="stRadio"] label[data-baseweb="radio"] > div:nth-last-child(2) { display: none !important; }
[data-testid="stRadio"] label[data-baseweb="radio"] > div:last-child {
    display: flex !important; justify-content: center !important; width: 100% !important; height: 100% !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"] p {
    white-space: normal !important; margin: 0 !important; font-size: 0.85rem !important;
    color: #64748b !important; font-weight: 500 !important; text-align: center !important; line-height: 1.2 !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {
    background: white !important; border-color: #cbd5e1 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p {
    color: #2563eb !important; font-weight: 700 !important;
}

/* TYPOGRAPHY & LABELS */
.plan-route-title { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 24px; color: #0f172a; line-height: 1.1; }
.field-label {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: #64748b !important; margin: 12px 0 6px 0;
}

/* ROUTE CARDS */
.route-card { 
    background: white; border: 1px solid #e2e8f0; border-radius: 12px; 
    padding: 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); transition: all 0.2s ease;
}
.route-card:hover { border-color: #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
.route-card.active { border: 2px solid #3b82f6; box-shadow: 0 4px 12px rgba(59,130,246,0.1); background: #f8fafc; }
.route-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; }
.rank-badge { font-size:0.75rem; font-weight:700; background: #e2e8f0; color:#475569; padding:4px 10px; border-radius:12px; }
.rank-1 { background:#2563eb !important; color:white !important; box-shadow: 0 2px 4px rgba(37,99,235,0.2) !important;}
.route-stats { font-size:0.85rem; color:#64748b !important; }
.route-cost  { font-size:1.1rem; font-weight:700; color:#0f172a !important; }

/* TIMELINE */
.timeline { border-left: 2px solid #e2e8f0; margin-left: 6px; padding-left: 14px; }
.seg-row { position:relative; margin-bottom:12px; }
.seg-row::before {
    content:""; position:absolute; left:-20px; top:4px; width:10px; height:10px;
    border-radius:50%; border:2px solid white; box-shadow:0 0 0 1px #cbd5e1; background:#cbd5e1;
}
.seg-row.active-node::before { background:#3b82f6; box-shadow:0 0 0 2px #3b82f6; }
.seg-from, .seg-to { font-size:0.85rem; font-weight:600; color:#0f172a !important; }
.seg-info { display:flex; align-items:center; gap:8px; margin:4px 0; flex-wrap:wrap; }
.mode-badge { font-size:0.7rem; font-weight:600; padding:2px 8px; border-radius:6px; color:#475569; background:#f1f5f9; border: 1px solid #e2e8f0;}

/* UTILS */
.error-box { background:#fef2f2; border:1px solid #fecaca; color:#991b1b !important; border-radius:10px; padding:12px; font-size: 0.85rem; margin-bottom:12px; }
.empty-state { text-align:center; padding:32px 16px; border-radius: 12px; background: white; border: 1px dashed #cbd5e1; margin-top: 10px; }
.empty-state p { color:#64748b !important; font-size: 0.9rem; margin:0;}
.results-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #e2e8f0; }
.results-title { font-weight:700; color:#0f172a !important; font-size:1rem; }
.results-count { font-size:.75rem; font-weight:600; background:#f1f5f9 !important; color:#475569 !important; padding:4px 10px; border-radius:12px; }

/* METRICS */
[data-testid="stMetric"] { background:white; border:1px solid #e2e8f0; border-radius:12px; padding:12px; transition: all 0.2s ease;}
[data-testid="stMetric"]:hover { border-color: #cbd5e1; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); }
[data-testid="stMetricLabel"] p { font-size:0.8rem !important; color:#64748b !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { font-size:1.4rem !important; font-weight:700 !important; color:#0f172a !important; }
</style>
""",
    unsafe_allow_html=True,
)

MODE_COLOURS = {
    "MTR": "#dc2626",
    "Citybus": "#d97706",
    "Green Minibus": "#16a34a",
    "HKU Shuttle Bus": "#2563eb",
    "Walking": "#64748b",
}
HKU_CENTER = [22.2831, 114.1371]


@st.cache_resource
def get_network():
    base = os.path.join(APP_DIR, "data")
    return load_network(
        os.path.join(base, "stops.csv"), os.path.join(base, "segments.csv")
    )


try:
    stops, segments, graph = get_network()
    network_ok = True
except Exception as e:
    stops, segments, graph = {}, [], {}
    network_ok = False
    network_error = str(e)

label_to_id, id_to_label = {}, {}
if network_ok:
    for sid, info in stops.items():
        label_to_id[info["stop_name"]] = sid
        id_to_label[sid] = info["stop_name"]
all_labels = ["Select a stop..."] + sorted(label_to_id.keys())

for key, default in [
    ("routes", []),
    ("active_route", 0),
    ("error_msg", ""),
    ("searched", False),
    ("origin_val", ""),
    ("dest_val", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

col_panel, col_map = st.columns([1.2, 3], gap="large")


# ══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL (NAVIGATION SEARCH)
# ══════════════════════════════════════════════════════════════════════════════
with col_panel:
    if not network_ok:
        st.error(f"Failed to load network: {network_error}")
        st.stop()

    st.markdown(
        '<div class="plan-route-title">Plan Your Route</div>', unsafe_allow_html=True
    )

    st.markdown(
        '<p class="field-label">Smart HKU Transport Advisor</p>', unsafe_allow_html=True
    )

    origin_label = st.selectbox(
        "Origin",
        all_labels,
        index=all_labels.index(id_to_label[st.session_state.origin_val])
        if st.session_state.origin_val in id_to_label
        else 0,
        label_visibility="collapsed",
        key="origin_select",
    )
    if origin_label != "Select a stop...":
        st.session_state.origin_val = label_to_id.get(origin_label, "")
    else:
        st.session_state.origin_val = ""

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    dest_label = st.selectbox(
        "Destination",
        all_labels,
        index=all_labels.index(id_to_label[st.session_state.dest_val])
        if st.session_state.dest_val in id_to_label
        else 0,
        label_visibility="collapsed",
        key="dest_select",
    )
    if dest_label != "Select a stop...":
        st.session_state.dest_val = label_to_id.get(dest_label, "")
    else:
        st.session_state.dest_val = ""

    st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

    preference = st.radio(
        "preference",
        options=["fastest", "cheapest", "fewest_segments"],
        format_func=lambda x: {
            "fastest": "Fastest",
            "cheapest": "Cheapest",
            "fewest_segments": "Fewest Transfers",
        }[x],
        horizontal=True,
        label_visibility="collapsed",
        key="pref_radio",
    )

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    find_clicked = st.button(
        "Find Routes", type="primary", use_container_width=True, key="find_btn"
    )

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    if find_clicked:
        origin_id = st.session_state.origin_val
        dest_id = st.session_state.dest_val
        result = validate_query(origin_id, dest_id, preference, stops, graph)
        if not result.ok:
            st.session_state.error_msg = result.error
            st.session_state.routes = []
            st.session_state.searched = True
        else:
            raw = find_all_journeys(graph, origin_id, dest_id, max_depth=8)
            no_routes = validate_journey_results(raw, origin_id, dest_id, stops)
            if not no_routes.ok:
                st.session_state.error_msg = no_routes.error
                st.session_state.routes = []
            else:
                st.session_state.routes = rank_journeys(raw, preference, stops, top_n=5)
                st.session_state.active_route = 0
                st.session_state.error_msg = ""
            st.session_state.searched = True

    if st.session_state.error_msg:
        st.markdown(
            f'<div class="error-box">{st.session_state.error_msg}</div>',
            unsafe_allow_html=True,
        )

    routes = st.session_state.routes

    if routes:
        count = len(routes)
        st.markdown(
            f"""<div class="results-header">
          <span class="results-title">Suggested Routes</span>
          <span class="results-count">{count} route{"s" if count!=1 else ""}</span>
        </div>""",
            unsafe_allow_html=True,
        )

        for route in routes:
            rank = route["rank"]
            rank_cls = f"rank-{rank}" if rank <= 3 else "rank-n"
            active = "active" if rank - 1 == st.session_state.active_route else ""

            segs_html = '<div class="timeline">'
            for seg in route["segments"]:
                mode = seg["mode"]
                segs_html += f"""
                <div class="seg-row active-node">
                  <div class="seg-from">{seg['from_stop_name']}</div>
                  <div class="seg-info">
                    <span class="mode-badge">{mode}</span>
                    <span style="font-size:0.75rem;color:#64748b;">{seg['route_name']} &nbsp;·&nbsp; {seg['duration']} min &nbsp;·&nbsp; HK${int(seg['cost'])}</span>
                  </div>
                </div>"""
            segs_html += f'<div class="seg-row"><div class="seg-to">{route["stop_names"][-1]}</div></div></div>'

            st.markdown(
                f"""
            <div class="route-card {active}">
              <div class="route-header">
                <div>
                  <span class="rank-badge {rank_cls}">#{rank}</span>
                  <span class="route-stats" style="margin-left:10px;">{route['total_duration']} min &nbsp;·&nbsp; HK${route['total_cost']:.0f}</span>
                </div>
              </div>
              {segs_html}
            </div>""",
                unsafe_allow_html=True,
            )

            if st.button(f"Show on Map (Route #{rank})", key=f"map_btn_{rank}"):
                st.session_state.active_route = rank - 1
                st.rerun()

    elif st.session_state.searched and not st.session_state.error_msg:
        st.markdown(
            '<div class="empty-state"><p>No routes found between these locations.</p></div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL (MAP VIEW)
# ══════════════════════════════════════════════════════════════════════════════
with col_map:
    routes = st.session_state.routes
    active_idx = st.session_state.active_route
    active_route = routes[active_idx] if routes and active_idx < len(routes) else None

    # Handle summary metrics if a route is active
    if active_route:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Duration", f"{active_route['total_duration']} min")
        m2.metric("Cost", f"HK${active_route['total_cost']:.0f}")
        m3.metric("Segments", active_route["num_segments"])
        m4.metric("Rank", f"#{active_route['rank']}")
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    if active_route:
        lats = [
            stops[s]["lat"]
            for s in active_route["stop_ids"]
            if stops.get(s, {}).get("lat")
        ]
        lngs = [
            stops[s]["lng"]
            for s in active_route["stop_ids"]
            if stops.get(s, {}).get("lng")
        ]
        centre = [sum(lats) / len(lats), sum(lngs) / len(lngs)] if lats else HKU_CENTER
        zoom = 15
    else:
        centre = HKU_CENTER
        zoom = 14

    # Setup core map configuration
    m = folium.Map(
        location=centre,
        zoom_start=zoom,
        tiles=None,
        zoom_control=True,
        scrollWheelZoom=True,
    )

    # Add multiple tile layers
    folium.TileLayer("CartoDB positron", name="Light Map (Default)").add_to(m)

    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite",
        attr="Esri",
        show=False,
    ).add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark Map", show=False).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Standard Map", show=False).add_to(m)

    # Route polylines
    if active_route:
        coords = [
            [stops[s]["lat"], stops[s]["lng"]]
            for s in active_route["stop_ids"]
            if stops.get(s, {}).get("lat") and stops.get(s, {}).get("lng")
        ]
        for i in range(len(coords) - 1):
            mode = (
                active_route["segments"][i]["mode"]
                if i < len(active_route["segments"])
                else "Walking"
            )
            colour = MODE_COLOURS.get(mode, "#3b82f6")
            folium.PolyLine(
                [coords[i], coords[i + 1]],
                color=colour,
                weight=6,
                opacity=0.8,
                tooltip=f"{mode}: {active_route['segments'][i]['route_name']}",
            ).add_to(m)

    # Markers
    origin_id = st.session_state.origin_val
    dest_id = st.session_state.dest_val

    for sid, info in stops.items():
        lat, lng = info.get("lat"), info.get("lng")
        if lat is None or lng is None:
            continue

        if active_route and sid in active_route["stop_ids"]:
            if sid == active_route["stop_ids"][0]:
                fill, radius, stroke = "#22c55e", 10, "#ffffff"
            elif sid == active_route["stop_ids"][-1]:
                fill, radius, stroke = "#ef4444", 10, "#ffffff"
            else:
                fill, radius, stroke = "#64748b", 7, "#ffffff"
        elif sid == origin_id:
            fill, radius, stroke = "#22c55e", 9, "#ffffff"
        elif sid == dest_id:
            fill, radius, stroke = "#ef4444", 9, "#ffffff"
        else:
            # Matches the normal yellow/orange 'Stop' color in our custom legend
            fill, radius, stroke = "#f59e0b", 6, "#ffffff"

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;min-width:160px;padding:4px">
          <b style="color:#0f172a;font-size:13px">{info["stop_name"]}</b><br>
          <span style="color:#64748b;font-size:11px">{info["campus_location"]}</span><br>
          <span style="color:#94a3b8;font-size:10px;display:block;margin-top:3px">{info["remark"]}</span>
        </div>"""

        folium.CircleMarker(
            location=[lat, lng],
            radius=radius,
            color=stroke,
            weight=2,
            fill=True,
            fill_color=fill,
            fill_opacity=1.0,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=info["stop_name"],
        ).add_to(m)

    # Add  custom UI legend
    legend_html = """
    <style>
        .leaflet-control-attribution { display: none !important; }
    </style>
    <div style="
        position: absolute;
        bottom: 30px;
        left: 30px;
        min-width: 180px;
        background-color: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        z-index: 1000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #0f172a;
        border: 1px solid #e2e8f0;
    ">
        <div style="font-weight: 700; font-size: 15px; margin-bottom: 12px; letter-spacing: -0.01em;">Transport Mode</div>
        
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 20px; height: 3px; background-color: #dc2626; margin-right: 12px; border-radius: 2px;"></div>
            <span style="font-size: 14px; font-weight: 500;">MTR</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 20px; height: 3px; background-color: #d97706; margin-right: 12px; border-radius: 2px;"></div>
            <span style="font-size: 14px; font-weight: 500;">Citybus</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 20px; height: 3px; background-color: #16a34a; margin-right: 12px; border-radius: 2px;"></div>
            <span style="font-size: 14px; font-weight: 500;">Green Minibus</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 20px; height: 3px; background-color: #2563eb; margin-right: 12px; border-radius: 2px;"></div>
            <span style="font-size: 14px; font-weight: 500;">HKU Shuttle</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 14px;">
            <div style="width: 20px; height: 3px; background-color: #64748b; margin-right: 12px; border-radius: 2px;"></div>
            <span style="font-size: 14px; font-weight: 500;">Walking</span>
        </div>
        
        <div style="border-top: 1px solid #e2e8f0; margin: 12px 0;"></div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: #22c55e; margin-right: 6px;"></div>
                <span style="font-size: 13px; font-weight: 500;">Origin</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: #ef4444; margin-right: 6px;"></div>
                <span style="font-size: 13px; font-weight: 500;">Dest</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: #f59e0b; margin-right: 6px;"></div>
                <span style="font-size: 13px; font-weight: 500;">Stop</span>
            </div>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Add the layer control logic
    folium.LayerControl(position="topright").add_to(m)

    # Render map
    st_folium(
        m,
        use_container_width=True,
        height=750 if not active_route else 600,
        returned_objects=[],
    )
