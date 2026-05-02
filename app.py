"""
app.py
------
Smart HKU Transport Advisor — with map version.
Run with:  python -m streamlit run app.py
"""

import os, sys
import streamlit as st
import folium
from streamlit_folium import st_folium

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from network_loader import load_network, get_campus_groups
from journey_finder import find_all_journeys
from scorer import rank_journeys
from validator import validate_query, validate_journey_results

st.set_page_config(
    page_title="HKU Transport Navigator",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background: #f1f5f9 !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
footer { display: none !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 0.5rem !important; }

body, p, span, div, label, li, h1, h2, h3, h4, h5, h6,
.stMarkdown, .stMarkdown *, [data-testid="stMarkdownContainer"] *,
[data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] *,
.element-container { color: #1e293b !important; }

/* ALL BUTTONS */
.stButton > button {
    background-color: white !important;
    color: #1e293b !important;
    border: 2px solid #cbd5e1 !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all .15s !important;
}
.stButton > button:hover {
    border-color: #94a3b8 !important;
    background-color: #f8fafc !important;
    color: #1e293b !important;
}
.stButton > button p { color: inherit !important; }

/* FIND ROUTES primary */
[data-testid="baseButton-primary"],
[data-testid="baseButton-primary"] * {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
[data-testid="baseButton-primary"]:hover { background-color: #1d4ed8 !important; }

/* SELECTBOX */
[data-baseweb="select"] > div, [data-baseweb="select"] > div > div {
    background-color: white !important; color: #1e293b !important; border-color: #cbd5e1 !important;
}
[data-baseweb="popover"] *, [data-baseweb="menu"] *,
[role="option"], [data-baseweb="option"] {
    background-color: white !important; color: #1e293b !important;
}
[role="option"]:hover, [data-baseweb="option"]:hover { background-color: #f1f5f9 !important; }

/* RADIO */
[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] > div { gap: 6px !important; }
[data-testid="stRadio"] > div > label {
    flex: 1 !important; background: white !important;
    border: 2px solid #e2e8f0 !important; border-radius: 10px !important;
    padding: 10px 6px !important; text-align: center !important;
    cursor: pointer !important; color: #1e293b !important;
}
[data-testid="stRadio"] > div > label:hover { border-color: #94a3b8 !important; }
[data-testid="stRadio"] > div > label:has(input:checked) {
    border-color: #2563eb !important; background: #eff6ff !important;
}
[data-testid="stRadio"] > div > label p { color: #1e293b !important; }

/* HEADER */
.app-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
    padding: 14px 22px; border-radius: 12px; margin-bottom: 14px;
    display: flex; align-items: center; gap: 14px;
    box-shadow: 0 2px 8px rgba(30,64,175,.25);
}
.app-header * { color: white !important; }
.app-header h1 { margin: 0; font-size: 1.35rem; font-weight: 700; }
.app-header p  { margin: 0; font-size: 0.78rem; opacity: 0.85; }

.field-label {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; color: #64748b !important; margin: 10px 0 2px 0;
}
.section-title { font-size: 1rem; font-weight: 700; color: #1e293b !important; margin-bottom: 12px; }

.route-card { background: white; border: 2px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
.route-card * { color: #1e293b !important; }
.route-card.active { border-color: #2563eb; background: #eff6ff; }
.route-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px; }
.rank-badge { font-size:.7rem; font-weight:800; padding:3px 8px; border-radius:6px; border:1px solid; }
.rank-1 { background:#fef9c3 !important; color:#854d0e !important; border-color:#fde047 !important; }
.rank-2 { background:#f1f5f9 !important; color:#475569 !important; border-color:#cbd5e1 !important; }
.rank-3 { background:#fff7ed !important; color:#9a3412 !important; border-color:#fdba74 !important; }
.rank-n { background:#f8fafc !important; color:#64748b !important; border-color:#e2e8f0 !important; }
.route-stats { font-size:.82rem; color:#475569 !important; }
.route-cost  { font-size:1.05rem; font-weight:700; color:#1e293b !important; }

.timeline { border-left: 2px solid #e2e8f0; margin-left: 6px; padding-left: 12px; }
.seg-row { position:relative; margin-bottom:10px; }
.seg-row::before {
    content:""; position:absolute; left:-17px; top:5px; width:9px; height:9px;
    border-radius:50%; border:2px solid white; box-shadow:0 0 0 2px #3b82f6; background:#3b82f6;
}
.seg-from, .seg-to { font-size:.82rem; font-weight:600; color:#1e293b !important; }
.seg-info { display:flex; align-items:center; gap:6px; margin:3px 0; flex-wrap:wrap; }

.mode-badge { font-size:.68rem; font-weight:600; padding:2px 7px; border-radius:4px; border:1px solid; white-space:nowrap; }
.mode-mtr     { background:#ffe4e6 !important; color:#9f1239 !important; border-color:#fecdd3 !important; }
.mode-citybus { background:#fef3c7 !important; color:#92400e !important; border-color:#fde68a !important; }
.mode-gmb     { background:#dcfce7 !important; color:#166534 !important; border-color:#bbf7d0 !important; }
.mode-shuttle { background:#dbeafe !important; color:#1e3a8a !important; border-color:#bfdbfe !important; }
.mode-walking { background:#f1f5f9 !important; color:#475569 !important; border-color:#cbd5e1 !important; }

.error-box { background:#fef2f2; border:1px solid #fecaca; color:#991b1b !important; border-radius:8px; padding:10px 14px; font-size:.85rem; margin-bottom:10px; }
.empty-state { text-align:center; padding:28px 16px; }
.empty-state * { color:#94a3b8 !important; }
.empty-icon { font-size:2.2rem; margin-bottom:8px; }
.results-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #e2e8f0; }
.results-title { font-weight:700; color:#1e293b !important; font-size:.95rem; }
.results-count { font-size:.72rem; font-weight:600; background:#f1f5f9 !important; color:#475569 !important; padding:2px 9px; border-radius:12px; }

[data-testid="stMetric"] { background:white; border:1px solid #e2e8f0; border-radius:10px; padding:10px 12px; }
[data-testid="stMetricLabel"] p { font-size:.75rem !important; color:#64748b !important; }
[data-testid="stMetricValue"] { font-size:1.1rem !important; font-weight:700 !important; color:#1e293b !important; }
hr { border-color:#e2e8f0 !important; margin:12px 0 !important; }

/* Hide Leaflet attribution */
.leaflet-control-attribution { display: none !important; }
</style>
""", unsafe_allow_html=True)

MODE_COLOURS = {"MTR":"#dc2626","Citybus":"#d97706","Green Minibus":"#16a34a","HKU Shuttle Bus":"#2563eb","Walking":"#64748b"}
MODE_CSS     = {"MTR":"mode-mtr","Citybus":"mode-citybus","Green Minibus":"mode-gmb","HKU Shuttle Bus":"mode-shuttle","Walking":"mode-walking"}
MODE_ICONS   = {"MTR":"🚇","Citybus":"🚌","Green Minibus":"🚐","HKU Shuttle Bus":"🔵","Walking":"🚶"}
HKU_CENTER   = [22.2831, 114.1371]

@st.cache_resource
def get_network():
    base = os.path.join(APP_DIR, "data")
    return load_network(os.path.join(base,"stops.csv"), os.path.join(base,"segments.csv"))

try:
    stops, segments, graph = get_network()
    network_ok = True
except Exception as e:
    stops, segments, graph = {}, [], {}
    network_ok = False
    network_error = str(e)

for key, default in [("routes",[]),("active_route",0),("error_msg",""),("searched",False),("swap_flag",False),("origin_val",""),("dest_val","")]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div style="font-size:1.8rem">🚌</div>
  <div><h1>HKU Transport Navigator</h1><p>Campus Route Planner &nbsp;·&nbsp; COMP1110 Group D21</p></div>
</div>""", unsafe_allow_html=True)

col_map, col_panel = st.columns([3, 2], gap="medium")

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL
# ══════════════════════════════════════════════════════════════════════════════
with col_panel:

    if not network_ok:
        st.error(f"Failed to load network: {network_error}")
        st.stop()

    label_to_id, id_to_label = {}, {}
    for sid, info in stops.items():
        label_to_id[info["stop_name"]] = sid
        id_to_label[sid] = info["stop_name"]
    all_labels = ["Select a stop..."] + sorted(label_to_id.keys())

    if st.session_state.swap_flag:
        st.session_state.origin_val, st.session_state.dest_val = st.session_state.dest_val, st.session_state.origin_val
        st.session_state.swap_flag = False

    st.markdown('<p class="section-title">🗺️ Plan Your Route</p>', unsafe_allow_html=True)

    st.markdown('<p class="field-label">Origin</p>', unsafe_allow_html=True)
    origin_label = st.selectbox("Origin", all_labels,
        index=all_labels.index(id_to_label[st.session_state.origin_val]) if st.session_state.origin_val in id_to_label else 0,
        label_visibility="collapsed", key="origin_select")
    if origin_label != "Select a stop...":
        st.session_state.origin_val = label_to_id.get(origin_label, "")

    c1, c2, c3 = st.columns([3, 1, 3])
    with c2:
        if st.button("⇅", use_container_width=True, key="swap_btn"):
            st.session_state.swap_flag = True
            st.rerun()

    st.markdown('<p class="field-label">Destination</p>', unsafe_allow_html=True)
    dest_label = st.selectbox("Destination", all_labels,
        index=all_labels.index(id_to_label[st.session_state.dest_val]) if st.session_state.dest_val in id_to_label else 0,
        label_visibility="collapsed", key="dest_select")
    if dest_label != "Select a stop...":
        st.session_state.dest_val = label_to_id.get(dest_label, "")

    st.divider()

    st.markdown('<p class="field-label">Route Preference</p>', unsafe_allow_html=True)
    preference = st.radio("preference",
        options=["fastest","cheapest","fewest_segments"],
        format_func=lambda x: {"fastest":"⚡ Fastest","cheapest":"💰 Cheapest","fewest_segments":"🔀 Fewest Transfers"}[x],
        horizontal=True, label_visibility="collapsed", key="pref_radio")

    st.markdown("<br>", unsafe_allow_html=True)
    find_clicked = st.button("🔍  Find Routes", type="primary", use_container_width=True, key="find_btn")

    if find_clicked:
        origin_id = st.session_state.origin_val
        dest_id   = st.session_state.dest_val
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
        st.markdown(f'<div class="error-box">⚠️ {st.session_state.error_msg}</div>', unsafe_allow_html=True)

    routes = st.session_state.routes

    if routes:
        count = len(routes)
        st.markdown(f'''<div class="results-header">
          <span class="results-title">Suggested Routes</span>
          <span class="results-count">{count} route{"s" if count!=1 else ""}</span>
        </div>''', unsafe_allow_html=True)

        for route in routes:
            rank     = route["rank"]
            rank_cls = f"rank-{rank}" if rank <= 3 else "rank-n"
            active   = "active" if rank-1 == st.session_state.active_route else ""

            segs_html = '<div class="timeline">'
            for seg in route["segments"]:
                mode     = seg["mode"]
                mode_cls = MODE_CSS.get(mode, "mode-walking")
                icon     = MODE_ICONS.get(mode, "🚌")
                segs_html += f"""
                <div class="seg-row">
                  <div class="seg-from">{seg['from_stop_name']}</div>
                  <div class="seg-info">
                    <span class="mode-badge {mode_cls}">{icon} {mode}</span>
                    <span style="font-size:.7rem;color:#64748b;">{seg['route_name']} &nbsp;·&nbsp; {seg['duration']} min &nbsp;·&nbsp; HK${int(seg['cost'])}</span>
                  </div>
                </div>"""
            segs_html += f'<div class="seg-to">📍 {route["stop_names"][-1]}</div></div>'

            st.markdown(f"""
            <div class="route-card {active}">
              <div class="route-header">
                <div>
                  <span class="rank-badge {rank_cls}">#{rank}</span>
                  <span class="route-stats" style="margin-left:8px;">{route['total_duration']} min &nbsp;·&nbsp; {route['num_segments']} seg{"s" if route['num_segments']!=1 else ""}</span>
                </div>
                <div class="route-cost">HK${route['total_cost']:.0f}</div>
              </div>
              {segs_html}
            </div>""", unsafe_allow_html=True)

            if st.button(f"📍 Show on Map  (Route #{rank})", key=f"map_btn_{rank}"):
                st.session_state.active_route = rank - 1
                st.rerun()

    elif st.session_state.searched and not st.session_state.error_msg:
        st.markdown('<div class="empty-state"><div class="empty-icon">🗺️</div><p>No routes found.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-icon">🚌</div><p>Select origin and destination, then press <b>Find Routes</b>.</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LEFT MAP
# ══════════════════════════════════════════════════════════════════════════════
with col_map:

    routes       = st.session_state.routes
    active_idx   = st.session_state.active_route
    active_route = routes[active_idx] if routes and active_idx < len(routes) else None

    if active_route:
        lats = [stops[s]["lat"] for s in active_route["stop_ids"] if stops.get(s,{}).get("lat")]
        lngs = [stops[s]["lng"] for s in active_route["stop_ids"] if stops.get(s,{}).get("lng")]
        centre = [sum(lats)/len(lats), sum(lngs)/len(lngs)] if lats else HKU_CENTER
        zoom = 15
    else:
        centre = HKU_CENTER
        zoom = 14

    # attr=" " removes the Leaflet/OSM attribution text
    m = folium.Map(
        location=centre, zoom_start=zoom,
        tiles="OpenStreetMap", zoom_control=True,
        scrollWheelZoom=True, attr=" "
    )

    # Route polylines
    if active_route:
        coords = [[stops[s]["lat"], stops[s]["lng"]]
                  for s in active_route["stop_ids"]
                  if stops.get(s,{}).get("lat") and stops.get(s,{}).get("lng")]
        for i in range(len(coords)-1):
            mode   = active_route["segments"][i]["mode"] if i < len(active_route["segments"]) else "Walking"
            colour = MODE_COLOURS.get(mode, "#64748b")
            folium.PolyLine(
                [coords[i], coords[i+1]], color=colour, weight=5, opacity=0.9,
                tooltip=f"{mode}: {active_route['segments'][i]['route_name']}",
            ).add_to(m)

    # Markers
    origin_id = st.session_state.origin_val
    dest_id   = st.session_state.dest_val

    for sid, info in stops.items():
        lat, lng = info.get("lat"), info.get("lng")
        if lat is None or lng is None:
            continue

        if active_route and sid in active_route["stop_ids"]:
            if sid == active_route["stop_ids"][0]:
                fill, radius, stroke = "#22c55e", 11, "#15803d"
            elif sid == active_route["stop_ids"][-1]:
                fill, radius, stroke = "#ef4444", 11, "#b91c1c"
            else:
                fill, radius, stroke = "#f59e0b", 8, "#d97706"
        elif sid == origin_id:
            fill, radius, stroke = "#22c55e", 9, "#15803d"
        elif sid == dest_id:
            fill, radius, stroke = "#ef4444", 9, "#b91c1c"
        else:
            fill, radius, stroke = "#3b82f6", 6, "#1d4ed8"

        popup_html = f"""
        <div style="font-family:Arial,sans-serif;min-width:160px;padding:4px">
          <b style="color:#1e293b;font-size:13px">{info["stop_name"]}</b><br>
          <span style="color:#64748b;font-size:11px">{info["campus_location"]}</span><br>
          <span style="color:#94a3b8;font-size:10px;display:block;margin-top:3px">{info["remark"]}</span>
        </div>"""

        folium.CircleMarker(
            location=[lat, lng], radius=radius,
            color=stroke, weight=2, fill=True,
            fill_color=fill, fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=info["stop_name"],
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:16px;left:16px;z-index:1000;
                background:white;padding:10px 14px;border-radius:10px;
                border:1px solid #e2e8f0;font-family:Arial,sans-serif;
                box-shadow:0 2px 8px rgba(0,0,0,.12);color:#1e293b;">
      <b style="color:#1e293b;font-size:12px;display:block;margin-bottom:6px;">Transport Mode</b>
      <div style="display:flex;flex-direction:column;gap:4px;font-size:11px;">
        <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:18px;height:3px;background:#dc2626;border-radius:2px;"></span><span style="color:#1e293b;">MTR</span></div>
        <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:18px;height:3px;background:#d97706;border-radius:2px;"></span><span style="color:#1e293b;">Citybus</span></div>
        <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:18px;height:3px;background:#16a34a;border-radius:2px;"></span><span style="color:#1e293b;">Green Minibus</span></div>
        <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:18px;height:3px;background:#2563eb;border-radius:2px;"></span><span style="color:#1e293b;">HKU Shuttle</span></div>
        <div style="display:flex;align-items:center;gap:6px;"><span style="display:inline-block;width:18px;height:3px;background:#64748b;border-radius:2px;"></span><span style="color:#1e293b;">Walking</span></div>
      </div>
      <div style="margin-top:8px;padding-top:6px;border-top:1px solid #e2e8f0;display:flex;gap:10px;font-size:11px;">
        <div style="display:flex;align-items:center;gap:3px;"><span style="color:#22c55e;font-size:14px;">●</span><span style="color:#1e293b;">Origin</span></div>
        <div style="display:flex;align-items:center;gap:3px;"><span style="color:#ef4444;font-size:14px;">●</span><span style="color:#1e293b;">Dest</span></div>
        <div style="display:flex;align-items:center;gap:3px;"><span style="color:#f59e0b;font-size:14px;">●</span><span style="color:#1e293b;">Stop</span></div>
      </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, use_container_width=True, height=670, returned_objects=[])

    if active_route:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("⏱ Duration",  f"{active_route['total_duration']} min")
        m2.metric("💰 Cost",      f"HK$ {active_route['total_cost']:.0f}")
        m3.metric("🔀 Segments",  active_route['num_segments'])
        m4.metric("🏆 Rank",      f"#{active_route['rank']}")
