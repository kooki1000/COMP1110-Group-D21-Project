"""
network_loader.py
-----------------
Reads the HKU transport network from two CSV files (stops and segments),
builds an adjacency-list graph, and provides helper functions to inspect
the loaded network.

CSV formats expected
--------------------
stops.csv  :  stop_id, stop_name, campus_location, remark
segments.csv: segment_id, from_stop_id, from_stop_name,
              to_stop_id, to_stop_name, mode, duration, cost, route_name
"""

import csv
import os


# ── Loading helpers ──────────────────────────────────────────────────────


def load_stops(filepath):
    """
    Load stops from a CSV file.

    Parameters
    ----------
    filepath : str
        Path to the stops CSV file.

    Returns
    -------
    dict
        A dictionary mapping stop_id -> {stop_name, campus_location, remark}.

    Raises
    ------
    FileNotFoundError  – if the file does not exist.
    ValueError         – if the file is empty or has no data rows.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Stops file not found: {filepath}")

    stops = {}
    skipped = []  # track rows that could not be parsed

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Check that the header contains the columns we need
        required = {"stop_id", "stop_name", "campus_location", "remark"}
        if reader.fieldnames is None or not required.issubset(
            {col.strip() for col in reader.fieldnames}
        ):
            raise ValueError(
                f"Stops CSV is missing required columns. "
                f"Expected: {required}. Got: {reader.fieldnames}"
            )

        for row_num, row in enumerate(reader, start=2):  # row 1 = header
            # Strip whitespace / carriage-return characters from every value
            row = {k.strip(): v.strip() for k, v in row.items()}

            stop_id = row.get("stop_id", "")
            stop_name = row.get("stop_name", "")

            # Basic validation: skip if id or name is blank
            if not stop_id or not stop_name:
                skipped.append(row_num)
                continue

            stops[stop_id] = {
                "stop_name": stop_name,
                "campus_location": row.get("campus_location", ""),
                "remark": row.get("remark", ""),
            }

    if not stops:
        raise ValueError(f"Stops file is empty or contains no valid rows: {filepath}")

    if skipped:
        print(f"[Warning] Skipped {len(skipped)} malformed row(s) in stops file "
              f"(line numbers: {skipped})")

    return stops


def load_segments(filepath, valid_stop_ids=None):
    """
    Load segments from a CSV file.

    Parameters
    ----------
    filepath : str
        Path to the segments CSV file.
    valid_stop_ids : set or None
        If provided, segments referencing unknown stop_ids are flagged as
        warnings but still loaded (the network may intentionally contain
        stops not in the main stops file).

    Returns
    -------
    list[dict]
        Each dict has keys: segment_id, from_stop_id, from_stop_name,
        to_stop_id, to_stop_name, mode, duration (int), cost (float),
        route_name.

    Raises
    ------
    FileNotFoundError  – if the file does not exist.
    ValueError         – if the file is empty or has no data rows.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Segments file not found: {filepath}")

    segments = []
    skipped = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {
            "segment_id", "from_stop_id", "from_stop_name",
            "to_stop_id", "to_stop_name", "mode", "duration", "cost", "route_name",
        }
        if reader.fieldnames is None or not required.issubset(
            {col.strip() for col in reader.fieldnames}
        ):
            raise ValueError(
                f"Segments CSV is missing required columns. "
                f"Expected: {required}. Got: {reader.fieldnames}"
            )

        for row_num, row in enumerate(reader, start=2):
            row = {k.strip(): v.strip() for k, v in row.items()}

            from_id = row.get("from_stop_id", "")
            to_id = row.get("to_stop_id", "")

            # Must have both endpoints
            if not from_id or not to_id:
                skipped.append((row_num, "missing stop id"))
                continue

            # Parse numeric fields safely
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

            # Warn about unknown stops (but still load the segment)
            if valid_stop_ids is not None:
                if from_id not in valid_stop_ids:
                    print(f"[Warning] Segment row {row_num}: "
                          f"from_stop_id '{from_id}' not in stops file.")
                if to_id not in valid_stop_ids:
                    print(f"[Warning] Segment row {row_num}: "
                          f"to_stop_id '{to_id}' not in stops file.")

            segments.append({
                "segment_id": row.get("segment_id", ""),
                "from_stop_id": from_id,
                "from_stop_name": row.get("from_stop_name", ""),
                "to_stop_id": to_id,
                "to_stop_name": row.get("to_stop_name", ""),
                "mode": row.get("mode", "Unknown"),
                "duration": duration,
                "cost": cost,
                "route_name": row.get("route_name", ""),
            })

    if not segments:
        raise ValueError(
            f"Segments file is empty or contains no valid rows: {filepath}"
        )

    if skipped:
        print(f"[Warning] Skipped {len(skipped)} malformed row(s) in segments file:")
        for line, reason in skipped:
            print(f"  Line {line}: {reason}")

    return segments


# ── Graph builder ────────────────────────────────────────────────────────


def build_graph(segments):
    """
    Convert a list of segment dicts into an adjacency-list graph.

    Parameters
    ----------
    segments : list[dict]
        Output of load_segments().

    Returns
    -------
    dict
        Mapping from_stop_id -> list of edge dicts.
        Each edge dict: {to_stop_id, to_stop_name, mode, duration, cost,
                         route_name, segment_id}
    """
    graph = {}

    for seg in segments:
        origin = seg["from_stop_id"]
        edge = {
            "to_stop_id": seg["to_stop_id"],
            "to_stop_name": seg["to_stop_name"],
            "mode": seg["mode"],
            "duration": seg["duration"],
            "cost": seg["cost"],
            "route_name": seg["route_name"],
            "segment_id": seg["segment_id"],
        }
        graph.setdefault(origin, []).append(edge)

    return graph


# ── Convenience: load everything at once ─────────────────────────────────


def load_network(stops_path, segments_path):
    """
    Load the full network in one call.

    Returns
    -------
    tuple (stops, segments, graph)
        stops    – dict  {stop_id: {stop_name, campus_location, remark}}
        segments – list  [segment dicts]
        graph    – dict  {from_stop_id: [edge, edge, ...]}
    """
    stops = load_stops(stops_path)
    segments = load_segments(segments_path, valid_stop_ids=set(stops.keys()))
    graph = build_graph(segments)
    return stops, segments, graph


# ── Display helpers ──────────────────────────────────────────────────────


def list_stops(stops):
    """Print all stops sorted alphabetically by name."""
    print(f"\n{'ID':<8} {'Stop Name':<40} {'Location':<30}")
    print("-" * 80)
    for sid, info in sorted(stops.items(), key=lambda x: x[1]["stop_name"]):
        print(f"{sid:<8} {info['stop_name']:<40} {info['campus_location']:<30}")
    print(f"\nTotal stops: {len(stops)}")


def network_summary(stops, segments, graph):
    """Print a summary of the loaded network."""
    # Count transport modes
    mode_counts = {}
    for seg in segments:
        mode = seg["mode"]
        mode_counts[mode] = mode_counts.get(mode, 0) + 1

    # Count how many stops have outgoing edges
    connected = sum(1 for sid in stops if sid in graph)

    print("\n========== NETWORK SUMMARY ==========")
    print(f"  Stops loaded    : {len(stops)}")
    print(f"  Segments loaded : {len(segments)}")
    print(f"  Stops with links: {connected} / {len(stops)}")
    print(f"\n  Segments by transport mode:")
    for mode, count in sorted(mode_counts.items()):
        print(f"    {mode:<25} {count:>3} segments")
    print("=" * 40)


# ── Quick self-test when run directly ────────────────────────────────────


if __name__ == "__main__":
    # When run directly, try to load the CSVs from the project folder
    import sys

    # Allow passing custom paths; fall back to defaults
    stops_file = sys.argv[1] if len(sys.argv) > 1 else "data/stops.csv"
    segs_file = sys.argv[2] if len(sys.argv) > 2 else "data/segments.csv"

    try:
        stops, segments, graph = load_network(stops_file, segs_file)
        list_stops(stops)
        network_summary(stops, segments, graph)

        # Show a sample adjacency entry
        sample_id = "S001"
        if sample_id in graph:
            print(f"\nSample edges from {sample_id} "
                  f"({stops[sample_id]['stop_name']}):")
            for edge in graph[sample_id]:
                print(f"  -> {edge['to_stop_name']:<35} "
                      f"{edge['mode']:<20} "
                      f"{edge['duration']:>3} min  "
                      f"HK${edge['cost']:<6.1f}  "
                      f"({edge['route_name']})")

    except (FileNotFoundError, ValueError) as e:
        print(f"[Error] {e}")
        sys.exit(1)
