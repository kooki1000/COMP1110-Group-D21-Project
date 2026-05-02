def find_all_journeys(graph, start_id, goal_id, max_depth=8):
    journeys = []

    def dfs(current_id, stop_ids, edges, visited):
        if len(edges) >= max_depth:
            return

        for edge in graph.get(current_id, []):
            next_id = edge["to_stop_id"]

            if next_id in visited:
                continue

            stop_ids.append(next_id)
            edges.append(edge)
            visited.add(next_id)

            if next_id == goal_id:
                # Valid complete journey — record a copy
                journeys.append({
                    "stop_ids": stop_ids[:],
                    "edges":    edges[:],
                })
            else:
                dfs(next_id, stop_ids, edges, visited)

            stop_ids.pop()
            edges.pop()
            visited.remove(next_id)

    dfs(start_id, [start_id], [], {start_id})
    return journeys
