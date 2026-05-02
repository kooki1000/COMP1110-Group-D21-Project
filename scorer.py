"""
scorer.py
---------
Scores raw journeys from journey_finder and returns a ranked list.

Preference modes
----------------
  fastest         – sort by total_duration, then cost, then num_segments
  cheapest        – sort by total_cost, then duration, then num_segments
  fewest_segments – sort by num_segments, then duration, then cost
"""

VALID_PREFERENCES = {"fastest", "cheapest", "fewest_segments"}


def score_journey(raw_journey, stops):
    """
    Add computed statistics to a raw journey dict.

    Parameters
    ----------
    raw_journey : dict  – {stop_ids, edges} from journey_finder
    stops       : dict  – stops dict from network_loader (for stop names)

    Returns
    -------
    dict with added keys: stop_names, total_duration, total_cost,
                          num_segments, segments (formatted list)
    """
    edges          = raw_journey["edges"]
    total_duration = sum(e["duration"] for e in edges)
    total_cost     = sum(e["cost"]     for e in edges)
    num_segments   = len(edges)

    # Build human-readable stop name list
    stop_ids   = raw_journey["stop_ids"]
    stop_names = [
        stops.get(sid, {}).get("stop_name", sid)
        for sid in stop_ids
    ]

    # Build formatted segment list for display
    formatted_segments = []
    for i, edge in enumerate(edges):
        formatted_segments.append({
            "from_stop_id":   stop_ids[i],
            "from_stop_name": stop_names[i],
            "to_stop_id":     edge["to_stop_id"],
            "to_stop_name":   edge["to_stop_name"],
            "mode":           edge["mode"],
            "duration":       edge["duration"],
            "cost":           edge["cost"],
            "route_name":     edge["route_name"],
        })

    return {
        "stop_ids":       stop_ids,
        "stop_names":     stop_names,
        "segments":       formatted_segments,
        "total_duration": total_duration,
        "total_cost":     total_cost,
        "num_segments":   num_segments,
    }


def _sort_key(journey, preference):
    if preference == "fastest":
        return (journey["total_duration"], journey["total_cost"], journey["num_segments"])
    elif preference == "cheapest":
        return (journey["total_cost"], journey["total_duration"], journey["num_segments"])
    else:  # fewest_segments
        return (journey["num_segments"], journey["total_duration"], journey["total_cost"])


def rank_journeys(raw_journeys, preference, stops, top_n=5):
    """
    Score, sort, and return the top-N journeys.

    Parameters
    ----------
    raw_journeys : list  – output of journey_finder.find_all_journeys()
    preference   : str   – "fastest" | "cheapest" | "fewest_segments"
    stops        : dict  – stops dict from network_loader
    top_n        : int   – maximum number of results to return

    Returns
    -------
    list of scored journey dicts, each with a 'rank' key (1-indexed)
    """
    if not raw_journeys:
        return []

    pref = preference.strip().lower()
    if pref not in VALID_PREFERENCES:
        pref = "fastest"

    scored = [score_journey(j, stops) for j in raw_journeys]
    scored.sort(key=lambda j: _sort_key(j, pref))

    results = []
    for rank, journey in enumerate(scored[:top_n], start=1):
        journey["rank"] = rank
        results.append(journey)

    return results
