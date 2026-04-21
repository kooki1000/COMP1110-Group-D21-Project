from flask import Flask, render_template, jsonify, request
import os
from modules.network_loader import load_network
from modules.journey_generator import find_all_journeys
from modules.scorer import score_and_rank
from modules.validator import validate_inputs

app = Flask(__name__)

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STOPS_FILE = os.path.join(DATA_DIR, "stops.csv")
SEGMENTS_FILE = os.path.join(DATA_DIR, "segments.csv")

# Load network on startup
try:
    STOPS, SEGMENTS, GRAPH = load_network(STOPS_FILE, SEGMENTS_FILE)
    print(f"Loaded {len(STOPS)} stops and {len(SEGMENTS)} segments")
except Exception as e:
    app.logger.exception("Error loading network during startup")
    raise RuntimeError(
        f"Failed to load required network data from {STOPS_FILE} and {SEGMENTS_FILE}"
    ) from e


def get_campus_locations():
    """Extract unique campus locations for grouping."""
    locations = set()
    for stop in STOPS.values():
        if stop["campus_location"]:
            locations.add(stop["campus_location"])
    return sorted(list(locations))


@app.route("/")
def index():
    return render_template("index.html", campuses=get_campus_locations(), stops=STOPS)


@app.route("/api/stops")
def api_stops():
    """Return all stops for autocomplete."""
    stop_list = []
    for sid, info in STOPS.items():
        stop_list.append(
            {
                "id": sid,
                "name": info["stop_name"],
                "campus": info["campus_location"],
                "lat": info.get("lat"),
                "lng": info.get("lng"),
            }
        )
    return jsonify(stop_list)


@app.route("/api/validate", methods=["POST"])
def validate():
    """Validate inputs without calculating routes."""
    data = request.json
    result = validate_inputs(
        data.get("origin"),
        data.get("destination"),
        data.get("preference", "balanced"),
        STOPS,
    )
    return jsonify(result)


@app.route("/api/routes", methods=["POST"])
def find_routes():
    """Find and score routes between stops."""
    data = request.json
    origin = data.get("origin")
    destination = data.get("destination")
    preference = data.get("preference", "balanced")

    # Validate
    validation = validate_inputs(origin, destination, preference, STOPS)
    if not validation["valid"]:
        return jsonify({"error": validation["errors"]}), 400

    # Generate journeys
    journeys = find_all_journeys(GRAPH, origin, destination, max_depth=6)

    if not journeys:
        return jsonify({"routes": [], "message": "No routes found between these stops"})

    # Score and rank
    scored_routes = score_and_rank(journeys, preference)

    # Format for frontend
    routes = []
    for idx, route in enumerate(scored_routes[:5], 1):  # Top 5
        formatted_segments = []
        for seg in route["journey"]["segments"]:
            formatted_segments.append(
                {
                    "from_stop": seg["from_stop_name"],
                    "to_stop": seg["to_stop_name"],
                    "mode": seg["mode"],
                    "duration": seg["duration"],
                    "cost": seg["cost"],
                    "route_name": seg["route_name"],
                    "mode_color": get_mode_color(seg["mode"]),
                    "icon": get_mode_icon(seg["mode"]),
                }
            )

        routes.append(
            {
                "id": idx,
                "rank": idx,
                "total_duration": route["total_duration"],
                "total_cost": round(route["total_cost"], 1),
                "num_transfers": route["num_transfers"],
                "score": round(route["score"], 2),
                "segments": formatted_segments,
                "stop_sequence": route["journey"]["stops"],
            }
        )

    return jsonify({"routes": routes, "count": len(routes)})


def get_mode_color(mode):
    """Return Tailwind color class for transport mode."""
    mode = mode.lower()
    colors = {
        "bus": "red",
        "shuttle": "green",
        "walk": "gray",
        "walking": "gray",
        "minibus": "yellow",
        "taxi": "blue",
        "tram": "purple",
    }
    return colors.get(mode, "blue")


def get_mode_icon(mode):
    """Return Font Awesome icon class for transport mode."""
    mode = mode.lower()
    icons = {
        "bus": "bus",
        "shuttle": "shuttle-van",
        "walk": "walking",
        "walking": "walking",
        "minibus": "taxi",
        "taxi": "taxi",
        "tram": "train",
    }
    return icons.get(mode, "arrow-right")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
