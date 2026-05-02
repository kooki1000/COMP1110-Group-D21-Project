"""
network_loader.py
-----------------
Loads the HKU transport network from two CSV files and builds an
adjacency-list graph keyed by stop_id.

stops.csv columns    : stop_id, stop_name, campus_location, remark, lat, lng
segments.csv columns : segment_id, from_stop_id, from_stop_name,
                       to_stop_id, to_stop_name, mode, duration, cost, route_name
"""

import csv
import os


# ── Internal helpers ───────────────────────────────────────────────────────────

def _strip(row):
    """Strip whitespace and carriage-return from every value in a CSV row."""
    return {k.strip(): v.strip() for k, v in row.items()}


# ── Loaders ────────────────────────────────────────────────────────────────────

def load_stops(filepath):
    """
    Load stops from CSV.

    Returns
    -------
    dict  stop_id -> {stop_name, campus_location, remark, lat, lng}

    Raises
    ------
    FileNotFoundError, ValueError
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Stops file not found: {filepath}")

    stops = {}
    skipped = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {"stop_id", "stop_name", "campus_location", "remark"}
        got = {c.strip() for c in (reader.fieldnames or [])}
        if not required.issubset(got):
            raise ValueError(
                f"Stops CSV missing columns. Expected: {required}. Got: {got}"
            )

        for row_num, raw in enumerate(reader, start=2):
            row = _strip(raw)
            sid  = row.get("stop_id", "")
            name = row.get("stop_name", "")

            if not sid or not name:
                skipped.append(row_num)
                continue

            # lat/lng are optional — default to None if absent or blank
            try:
                lat = float(row["lat"]) if row.get("lat") else None
            except ValueError:
                lat = None
            try:
                lng = float(row["lng"]) if row.get("lng") else None
            except ValueError:
                lng = None

            stops[sid] = {
                "stop_name":       name,
                "campus_location": row.get("campus_location", ""),
                "remark":          row.get("remark", ""),
                "lat":             lat,
                "lng":             lng,
            }

    if not stops:
        raise ValueError(f"Stops file is empty or has no valid rows: {filepath}")

    if skipped:
        print(f"[Warning] Skipped {len(skipped)} malformed stop row(s): {skipped}")

    return stops


def load_segments(filepath, valid_stop_ids=None):
    """
    Load segments from CSV.

    Returns
    -------
    list[dict]  each dict has: segment_id, from_stop_id, from_stop_name,
                to_stop_id, to_stop_name, mode, duration (int), cost (float),
                route_name

    Raises
    ------
    FileNotFoundError, ValueError
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Segments file not found: {filepath}")

    segments = []
    skipped  = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {
            "segment_id", "from_stop_id", "from_stop_name",
            "to_stop_id",  "to_stop_name",  "mode",
            "duration",    "cost",          "route_name",
        }
        got = {c.strip() for c in (reader.fieldnames or [])}
        if not required.issubset(got):
            raise ValueError(
                f"Segments CSV missing columns. Expected: {required}. Got: {got}"
            )

        for row_num, raw in enumerate(reader, start=2):
            row     = _strip(raw)
            from_id = row.get("from_stop_id", "")
            to_id   = row.get("to_stop_id",   "")

            if not from_id or not to_id:
                skipped.append((row_num, "missing stop id"))
                continue

            try:
                duration = int(row.get("duration", "0"))
            except ValueError:
                skipped.append((row_num, f"bad duration: {row.get('duration')}"))
                continue

            try:
                cost = float(row.get("cost", "0"))
            except ValueError:
                skipped.append((row_num, f"bad cost: {row.get('cost')}"))
                continue

            if valid_stop_ids:
                for bad_id, label in [(from_id, "from"), (to_id, "to")]:
                    if bad_id not in valid_stop_ids:
                        print(f"[Warning] Row {row_num}: {label}_stop_id '{bad_id}' not in stops.")

            segments.append({
                "segment_id":    row.get("segment_id", ""),
                "from_stop_id":  from_id,
                "from_stop_name": row.get("from_stop_name", ""),
                "to_stop_id":    to_id,
                "to_stop_name":  row.get("to_stop_name", ""),
                "mode":          row.get("mode", "Unknown"),
                "duration":      duration,
                "cost":          cost,
                "route_name":    row.get("route_name", ""),
            })

    if not segments:
        raise ValueError(f"Segments file is empty or has no valid rows: {filepath}")

    if skipped:
        print(f"[Warning] Skipped {len(skipped)} malformed segment row(s).")

    return segments


def build_graph(segments):
    """
    Convert segment list -> adjacency dict.

    Returns
    -------
    dict  from_stop_id -> list of edge dicts
          Each edge: {to_stop_id, to_stop_name, mode, duration, cost,
                      route_name, segment_id}
    """
    graph = {}
    for seg in segments:
        edge = {
            "to_stop_id":   seg["to_stop_id"],
            "to_stop_name": seg["to_stop_name"],
            "mode":         seg["mode"],
            "duration":     seg["duration"],
            "cost":         seg["cost"],
            "route_name":   seg["route_name"],
            "segment_id":   seg["segment_id"],
        }
        graph.setdefault(seg["from_stop_id"], []).append(edge)
    return graph


def load_network(stops_path, segments_path):
    """
    Load everything in one call.

    Returns
    -------
    (stops, segments, graph)
    """
    stops    = load_stops(stops_path)
    segments = load_segments(segments_path, valid_stop_ids=set(stops))
    graph    = build_graph(segments)
    return stops, segments, graph


# ── Display helpers (used by app.py) ──────────────────────────────────────────

def get_campus_groups(stops):
    """Return {campus_location: [(stop_id, stop_name), ...]} sorted."""
    groups = {}
    for sid, info in stops.items():
        campus = info["campus_location"] or "Other"
        groups.setdefault(campus, []).append((sid, info["stop_name"]))
    for campus in groups:
        groups[campus].sort(key=lambda x: x[1])
    return dict(sorted(groups.items()))
