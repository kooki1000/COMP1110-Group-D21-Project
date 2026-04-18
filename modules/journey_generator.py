def find_all_journeys(graph, start, goal, max_depth=6):
    """
    Depth-limited DFS to find all paths from start to goal.
    Returns list of journeys, each containing stops and edges.
    """
    journeys = []

    def dfs(current, path_stops, path_edges):
        # Stop if path is too long
        if len(path_stops) > max_depth + 1:
            return

        # Found valid journey (at least one segment)
        if current == goal and len(path_stops) > 1:
            journeys.append({"stops": path_stops[:], "segments": path_edges[:]})
            return

        # Explore neighbors
        for edge in graph.get(current, []):
            to_id = edge["to_stop_id"]
            if to_id not in path_stops:  # Avoid cycles
                path_stops.append(to_id)
                path_edges.append(edge)
                dfs(to_id, path_stops, path_edges)
                path_stops.pop()
                path_edges.pop()

    dfs(start, [start], [])
    return journeys
