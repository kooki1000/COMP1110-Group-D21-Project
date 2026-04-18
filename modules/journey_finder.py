def find_all_journeys(graph, start, goal, max_depth=10):
    journeys = []

    def dfs(current, path_stops, path_edges):
        # Stop if path is too long
        if len(path_stops) > max_depth + 1:
            return
        # Found a valid journey (at least one segment)
        if current == goal and len(path_stops) > 1:
            journeys.append((path_stops[:], path_edges[:]))
            return

        for to_name, mode, dur, cst, rte in graph.get(current, []):
            if to_name not in path_stops:  
                edge = {
                    'mode': mode,
                    'duration': dur,
                    'cost': cst,
                    'route': rte
                }
                path_stops.append(to_name)
                path_edges.append(edge)
                dfs(to_name, path_stops, path_edges)
                path_stops.pop()
                path_edges.pop()

    dfs(start, [start], [])
    return journeys
