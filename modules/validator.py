
"""
validator.py
------------
Input and network validation for the Smart HKU Transport Advisor.

All functions return a ValidationResult namedtuple:
    .ok      – True if the input is valid, False otherwise
    .error   – Human-readable error string (empty string when ok=True)

Usage
-----
    from validator import validate_query, validate_network_loaded, ValidationResult

    result = validate_query("S001", "S002", "fastest", stops, graph)
    if not result.ok:
        print(result.error)
    else:
        # safe to proceed
"""

from collections import namedtuple

# ── Return type ───────────────────────────────────────────────────────────────

ValidationResult = namedtuple("ValidationResult", ["ok", "error"])

_OK = ValidationResult(ok=True, error="")


def _fail(message):
    return ValidationResult(ok=False, error=message)


# ── Constants ─────────────────────────────────────────────────────────────────

VALID_PREFERENCES = {"fastest", "cheapest", "fewest_segments"}

# Human-friendly display names used in error messages
PREFERENCE_DISPLAY = {
    "fastest":         "fastest",
    "cheapest":        "cheapest",
    "fewest_segments": "fewest_segments",
}


# ── Network-level validators ──────────────────────────────────────────────────


def validate_network_loaded(stops, segments=None):
    """
    Check that the network has been loaded before any query is run.

    Parameters
    ----------
    stops    : dict or None   – the stops dictionary from network_loader
    segments : list or None   – optional; the segments list from network_loader

    Returns
    -------
    ValidationResult
    """
    if not stops:
        return _fail(
            "No network loaded. Please load a network file before querying."
        )
    if segments is not None and not segments:
        return _fail(
            "The loaded network contains no segments. "
            "Check the segments CSV file."
        )
    return _OK


# ── Stop-name / ID resolution ─────────────────────────────────────────────────


def resolve_stop(user_input, stops):
    """
    Try to match a user-supplied string to a stop in the network.

    Matching rules (in priority order):
      1. Exact stop_id match   (e.g. "S001")
      2. Exact stop_name match (case-insensitive)
      3. Partial stop_name match (case-insensitive, must be unique)

    Parameters
    ----------
    user_input : str   – what the user typed
    stops      : dict  – {stop_id: {stop_name, ...}} from network_loader

    Returns
    -------
    (stop_id, stop_name)  on success
    (None,    error_msg)  on failure
    """
    text = user_input.strip()

    # 1. Exact stop_id
    if text in stops:
        return text, stops[text]["stop_name"]

    # 2. Exact stop_name (case-insensitive)
    lower = text.lower()
    for sid, info in stops.items():
        if info["stop_name"].lower() == lower:
            return sid, info["stop_name"]

    # 3. Partial match
    matches = [
        (sid, info["stop_name"])
        for sid, info in stops.items()
        if lower in info["stop_name"].lower()
    ]

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        names = ", ".join(f"{sid} ({name})" for sid, name in matches)
        return None, (
            f"'{user_input}' matches multiple stops: {names}. "
            f"Please be more specific."
        )

    return None, (
        f"Stop '{user_input}' not found in the network. "
        f"Use 'List stops' from the menu to see all available stops."
    )


# ── Query validators ──────────────────────────────────────────────────────────


def validate_stop_id(stop_id, stops, label="Stop"):
    """
    Confirm that a stop_id exists in the loaded network.

    Parameters
    ----------
    stop_id : str   – the stop ID to look up
    stops   : dict  – stops dict from network_loader
    label   : str   – used in the error message ("Origin", "Destination", etc.)

    Returns
    -------
    ValidationResult
    """
    if not isinstance(stop_id, str) or not stop_id.strip():
        return _fail(f"{label} cannot be empty.")

    if stop_id.strip() not in stops:
        return _fail(
            f"{label} '{stop_id}' is not a recognised stop ID. "
            f"Use 'List stops' to see available stops."
        )
    return _OK


def validate_preference(preference):
    """
    Check that the preference mode is one of the supported options.

    Parameters
    ----------
    preference : str – the preference string entered by the user

    Returns
    -------
    ValidationResult
    """
    if not isinstance(preference, str) or not preference.strip():
        return _fail(
            "Preference mode cannot be empty. "
            f"Valid options: {', '.join(sorted(VALID_PREFERENCES))}."
        )

    normalised = preference.strip().lower()

    if normalised not in VALID_PREFERENCES:
        return _fail(
            f"'{preference}' is not a valid preference mode. "
            f"Valid options are: {', '.join(sorted(VALID_PREFERENCES))}."
        )
    return _OK


def validate_origin_destination(origin_id, destination_id, stops):
    """
    Validate both stops and confirm they are different.

    Parameters
    ----------
    origin_id      : str  – stop ID for the journey start
    destination_id : str  – stop ID for the journey end
    stops          : dict – stops dict from network_loader

    Returns
    -------
    ValidationResult
    """
    result = validate_stop_id(origin_id, stops, label="Origin")
    if not result.ok:
        return result

    result = validate_stop_id(destination_id, stops, label="Destination")
    if not result.ok:
        return result

    if origin_id.strip() == destination_id.strip():
        name = stops[origin_id.strip()]["stop_name"]
        return _fail(
            f"Origin and destination are the same stop ({name}). "
            f"Please enter two different stops."
        )
    return _OK


def validate_query(origin_id, destination_id, preference, stops, graph=None):
    """
    Full validation for a journey query.

    Checks (in order):
      1. Network is loaded
      2. Origin stop exists
      3. Destination stop exists
      4. Origin != Destination
      5. Preference mode is valid
      6. (Optional) Origin has at least one outgoing edge in the graph

    Parameters
    ----------
    origin_id      : str        – stop ID for journey start
    destination_id : str        – stop ID for journey end
    preference     : str        – one of "fastest", "cheapest", "fewest_segments"
    stops          : dict       – stops dict from network_loader
    graph          : dict|None  – adjacency graph; if provided, reachability is checked

    Returns
    -------
    ValidationResult
    """
    # 1. Network loaded
    result = validate_network_loaded(stops)
    if not result.ok:
        return result

    # 2 + 3 + 4. Stops exist and differ
    result = validate_origin_destination(origin_id, destination_id, stops)
    if not result.ok:
        return result

    # 5. Preference is valid
    result = validate_preference(preference)
    if not result.ok:
        return result

    # 6. Origin has outgoing edges
    if graph is not None:
        oid = origin_id.strip()
        if oid not in graph or not graph[oid]:
            name = stops[oid]["stop_name"]
            return _fail(
                f"'{name}' has no outgoing connections in the network. "
                f"No journeys can be generated from this stop."
            )

    return _OK


# ── Journey result validator ──────────────────────────────────────────────────


def validate_journey_results(journeys, origin_id, destination_id, stops):
    """
    Check whether the journey generator returned usable results.

    Parameters
    ----------
    journeys       : list  – list of candidate journey dicts
    origin_id      : str
    destination_id : str
    stops          : dict

    Returns
    -------
    ValidationResult
    """
    if not journeys:
        origin_name = stops.get(origin_id, {}).get("stop_name", origin_id)
        dest_name   = stops.get(destination_id, {}).get("stop_name", destination_id)
        return _fail(
            f"No routes found from '{origin_name}' to '{dest_name}' "
            f"within the segment limit. "
            f"The two stops may not be connected in the current network, "
            f"or a higher depth limit may be needed."
        )
    return _OK


# ── Backward-compatible wrapper for Flask API ─────────────────────────────────


def validate_inputs(origin, destination, preference, stops):
    """
    Validate route planning inputs for the Flask API.

    Returns a dict with keys "valid" (bool) and "errors" (list[str]),
    compatible with the /api/validate and /api/routes endpoints.
    """
    result = validate_network_loaded(stops)
    if not result.ok:
        return {"valid": False, "errors": [result.error]}

    errors = []

    if not origin or not destination:
        errors.append("Please select both origin and destination")
        return {"valid": False, "errors": errors}

    if origin not in stops:
        errors.append(f"Origin stop '{origin}' not found")

    if destination not in stops:
        errors.append(f"Destination stop '{destination}' not found")

    if not errors and origin == destination:
        errors.append("Origin and destination cannot be the same")

    if preference not in ["speed", "cost", "balanced"]:
        errors.append("Invalid preference mode")

    return {"valid": len(errors) == 0, "errors": errors}
