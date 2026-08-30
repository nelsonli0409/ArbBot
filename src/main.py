from .config import DataFeedConfig
from .data_feed import fetch_quotes
from .graph import (
    build_edges, 
    build_edge_lookup,
    build_nodes,
    index_edges
)
from .bellman_ford import find_negative_cycle
from .execution import (
    index_to_symbol, 
    simulate_cycle
)

def main() -> None:
    # Configuration and initial parameters for the arbitrage bot
    FEE = 0.001
    START_CURRENCY = "USDT"
    START_AMOUNT = 1000.0
    SLIPPAGE_BUY_BPS = 10 # PLACEHOLDER
    SLIPPAGE_SELL_BPS = 10 # PLACEHOLDER
    CONFIG = DataFeedConfig( "https://api.binance.us", 5.0 )

    # Fetch latest quotes, build graph structures for arbitrage detection
    quotes = fetch_quotes(FEE, CONFIG)
    if not quotes:
        print("No quotes fetched.")
        return

    edges = build_edges(quotes)
    edge_lookup = build_edge_lookup(edges)
    nodes = build_nodes(edges)
    indexed_edges = index_edges(edges, nodes)

    # Detect potential negative cycles
    cycle_indices = find_negative_cycle(indexed_edges, len(nodes))
    if not cycle_indices:
        print("No negative cycle found.")
        return

    # Convert cycle indices to currency symbols and simulate the arbitrage cycle
    currency_cycle = index_to_symbol(cycle_indices, nodes)
    result = simulate_cycle(
        currency_cycle,
        edge_lookup,
        START_CURRENCY,
        START_AMOUNT,
        SLIPPAGE_BUY_BPS,
        SLIPPAGE_SELL_BPS
    )

    # Summary
    print("Currency cycle:", currency_cycle)
    print("Start currency:", START_CURRENCY)
    print("Start amount:", START_AMOUNT)
    print("Slippage buy (bps):", SLIPPAGE_BUY_BPS)
    print("Slippage sell (bps):", SLIPPAGE_SELL_BPS)
    print("Result:", result)

if __name__ == "__main__":
    main()