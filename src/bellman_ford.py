def find_negative_cycle(indexed_edges: list[tuple[int, int, float, object]], num_nodes: int) -> list[int] | None:
    """Finds a negative weight cycle in a graph represented by indexed edges.

    Returns a list of node indices forming the negative cycle if one exists, otherwise
    None.
    """
    # dist is 0 for all nodes initially, so that any negative cycle can be detected
    # from any starting node.
    dist = {u: 0 for u, _, _, _ in indexed_edges}
    for _, v, _, _ in indexed_edges:
        if v not in dist:
            dist[v] = 0
    pred = [-1] * num_nodes

    # Loop N - 1 times to relax all edges
    for _ in range(num_nodes - 1):
        for u, v, w, _ in indexed_edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                pred[v] = u

    # On N-th pass, check for negative weight cycles
    for u, v, w, _ in indexed_edges:
        if dist[u] + w < dist[v]:
            # Negative cycle detected, recover it
            return recover_negative_cycle(v, pred, num_nodes)

    return None


def recover_negative_cycle(v: int, pred: list[int], num_nodes: int) -> list[int]:
    """Recovers a negative cycle when given a node from a graph relaxed in N-1 passes
    of the Bellman-Ford algorithm.

    Returned list of node indices forms the negative cycle representing the currencies
    involved in the negative cycle, i.e. the sequence of trades to exploit the arbitrage 
    opportunity.
    """
    # To ensure we are inside the negative cycle, move back N steps
    x = v
    for _ in range(num_nodes):
        x = pred[x]

    # Now x is guaranteed to be in the negative cycle
    cycle = [x]
    curr = pred[x]
    while curr != x:
        cycle.append(curr)
        curr = pred[curr]

    cycle.append(x)
    # Reverse cycle to follow the correct order of traversal
    cycle.reverse()
    return cycle

    