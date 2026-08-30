from .models import Edge, Order, SimulationResult

def index_to_symbol(cycle: list[int], nodes: dict[str, int]) -> list[str]:
    """Converts a cycle of node indices into a cycle of currency symbols based on the
    nodes dictionary.
    
    Returns a list of currency symbols corresponding to the node indices in the cycle.
    """
    inverse_nodes = {v: k for k, v in nodes.items()}
    return [inverse_nodes[i] for i in cycle]

def validate_cycle(
    currency_cycle: list[str], 
    edge_lookup: dict[tuple[str, str], Edge]
) -> tuple[str, str] | bool:
    """Validates that a given currency cycle can be executed based on the available
    edges.

    Returns True if all consecutive currency pairs in the cycle have corresponding
    edges in the edge lookup, otherwise returns the first missing edge.
    """
    for i in range(len(currency_cycle)):
        u = currency_cycle[i]
        v = currency_cycle[(i + 1) % len(currency_cycle)]
        if (u, v) not in edge_lookup:
            return (u, v)
    return True

def cycle_to_orders(
    currency_cycle: list[str], 
    edge_lookup: dict[tuple[str, str], Edge],
    start_amount: float
) -> list[Order]:
    """Converts a cycle of currency symbols into a list of orders based on the edge
    lookup.

    Returns a list of orders needed to profit from the arbitrage.
    """
    orders = []

    missing_edge = validate_cycle(currency_cycle, edge_lookup)
    if missing_edge is not True:
        raise ValueError(f"The provided cycle has missing edge: {missing_edge}")

    trade_amount = start_amount
    for i in range(len(currency_cycle)):
        u = currency_cycle[i]
        # Loops around to the beginning of the cycle if at the last element
        v = currency_cycle[(i + 1) % len(currency_cycle)]
        edge = edge_lookup.get((u, v))

        orders.append(Order(
            symbol=edge.symbol,
            action=edge.action,
            amount=trade_amount,
            # raw rate is stored as buy or 1/ask, so if buying we take the inverse
            price=(1 / edge.raw_rate) if edge.action == "BUY" else edge.raw_rate,
            fee=edge.fee
        ))

        trade_amount = trade_amount * ( edge.raw_rate * ( 1 - edge.fee ) )

    return orders

def simulate_cycle(
    currency_cycle: list[str],
    edge_lookup: dict[tuple[str, str], Edge],
    start_amount: float,
    slippage_bps_buy: float = 0.0,
    slippage_bps_sell: float = 0.0, 
) -> SimulationResult:
    """Simulates the execution of a arbitrage cycle and returns the result.

    Returns a SimulationResult containing the final amount, the profit and loss, and
    the list of orders executed.
    """
    if start_amount <= 0:
        raise ValueError("Start amount must be greater than zero.")

    orders = cycle_to_orders(currency_cycle, edge_lookup, start_amount)

    # Apply slippage to each amount
    final_amount = start_amount
    for order in orders:
        slippage = slippage_bps_buy if order.action == "BUY" else slippage_bps_sell
        rate = (1 / order.price) if order.action == "BUY" else order.price
        final_amount = final_amount * rate * (1 - order.fee) * (1 - slippage / 10000)

    return SimulationResult(
        start_currency=currency_cycle[0],
        start_amount=start_amount,
        final_amount=final_amount,
        pnl_abs=final_amount - start_amount,
        pnl_pct=((final_amount / start_amount) - 1) * 100,
        orders=orders,
        cycle=currency_cycle
    )