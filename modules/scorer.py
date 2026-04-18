def score_and_rank(journeys, preference="balanced"):
    """
    Score journeys based on user preference.
    preference: 'speed', 'cost', or 'balanced'
    """
    scored = []

    for journey in journeys:
        total_duration = sum(seg["duration"] for seg in journey["segments"])
        total_cost = sum(seg["cost"] for seg in journey["segments"])
        num_transfers = len(journey["segments"]) - 1

        # Calculate composite score based on preference
        if preference == "speed":
            # Lower duration is better, cost is secondary
            score = total_duration * 1.0 + total_cost * 0.1 + num_transfers * 5
        elif preference == "cost":
            # Lower cost is better, duration secondary
            score = total_cost * 1.0 + total_duration * 0.05 + num_transfers * 2
        else:  # balanced
            # Normalize duration (assume max 60 min) and cost (assume max 50 HKD)
            norm_duration = total_duration / 60.0
            norm_cost = total_cost / 50.0
            score = norm_duration * 0.4 + norm_cost * 0.4 + num_transfers * 0.2

        scored.append(
            {
                "journey": journey,
                "score": score,
                "total_duration": total_duration,
                "total_cost": total_cost,
                "num_transfers": num_transfers,
                "num_segments": len(journey["segments"]),
            }
        )

    # Sort by score (lower is better)
    scored.sort(key=lambda x: x["score"])
    return scored
