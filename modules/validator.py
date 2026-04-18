def validate_inputs(origin, destination, preference, stops):
    """Validate route planning inputs."""
    errors = []

    if not origin or not destination:
        errors.append("Please select both origin and destination")
        return {"valid": False, "errors": errors}

    if origin == destination:
        errors.append("Origin and destination cannot be the same")

    if origin not in stops:
        errors.append(f"Origin stop '{origin}' not found")

    if destination not in stops:
        errors.append(f"Destination stop '{destination}' not found")

    if preference not in ["speed", "cost", "balanced"]:
        errors.append("Invalid preference mode")

    return {"valid": len(errors) == 0, "errors": errors}
