"""
validator.py
------------
Input validation for the Smart HKU Transport Advisor.

All functions return a ValidationResult(ok, error).
"""

from collections import namedtuple

ValidationResult = namedtuple("ValidationResult", ["ok", "error"])

_OK = ValidationResult(ok=True, error="")

def _fail(msg):
    return ValidationResult(ok=False, error=msg)


VALID_PREFERENCES = {"fastest", "cheapest", "fewest_segments"}


# ── Network ────────────────────────────────────────────────────────────────────

def validate_network_loaded(stops):
    if not stops:
        return _fail("No network loaded. Please check the data files.")
    return _OK


# ── Query ──────────────────────────────────────────────────────────────────────

def validate_query(origin_id, destination_id, preference, stops, graph=None):
    """
    Full validation for a journey query. Returns on first failure.
    """
    result = validate_network_loaded(stops)
    if not result.ok:
        return result

    if not origin_id:
        return _fail("Please select an origin stop.")
    if not destination_id:
        return _fail("Please select a destination stop.")

    if origin_id not in stops:
        return _fail(f"Origin '{origin_id}' not found in network.")
    if destination_id not in stops:
        return _fail(f"Destination '{destination_id}' not found in network.")

    if origin_id == destination_id:
        name = stops[origin_id]["stop_name"]
        return _fail(f"Origin and destination are the same ({name}). Please choose two different stops.")

    pref = (preference or "").strip().lower()
    if pref not in VALID_PREFERENCES:
        return _fail(
            f"'{preference}' is not a valid preference. "
            f"Choose from: {', '.join(sorted(VALID_PREFERENCES))}."
        )

    if graph is not None:
        if origin_id not in graph or not graph[origin_id]:
            name = stops[origin_id]["stop_name"]
            return _fail(f"'{name}' has no outgoing connections in the network.")

    return _OK


# ── Results ────────────────────────────────────────────────────────────────────

def validate_journey_results(journeys, origin_id, destination_id, stops):
    if not journeys:
        o = stops.get(origin_id, {}).get("stop_name", origin_id)
        d = stops.get(destination_id, {}).get("stop_name", destination_id)
        return _fail(
            f"No routes found from '{o}' to '{d}' within the segment limit. "
            "The stops may not be connected in the current network."
        )
    return _OK
