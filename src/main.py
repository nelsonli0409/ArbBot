import argparse
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

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Arbitrage Bot")
    p.add_argument("--base-url", type=str, default="https://api.binance.us")
    p.add_argument("--timeout-sec", type=float, default=5.0)
    p.add_argument("--fee", type=float, default=0.001)
    p.add_argument("--start-currency", type=str, default="USDT")
    p.add_argument("--start-amount", type=float, default=1000.0)
    p.add_argument("--slippage-buy-bps", type=float, default=10.0)
    p.add_argument("--slippage-sell-bps", type=float, default=10.0)
    p.add_argument(
        "--min-pnl-pct", 
        type=float, 
        default=0.2, 
        help="Only report cycles with profit/loss percentage above this threshold"
    )
    return p.parse_args()

def main() -> None:
    # Configuration and initial parameters for the arbitrage bot
    args = parse_args()
    config = DataFeedConfig(args.base_url, args.timeout_sec)

    # Fetch latest quotes, build graph structures for arbitrage detection
    quotes = fetch_quotes(args.fee, config)
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
        args.start_amount,
        args.slippage_buy_bps,
        args.slippage_sell_bps
    )

    # Summary
    print("Currency cycle:", result.cycle)
    print("Orders:", result.orders)
    print("Start currency:", args.start_currency)
    print("Start amount:", args.start_amount)
    print("Final amount:", result.final_amount)
    print("Profit/Loss (absolute):", result.pnl_abs)
    print("Profit/Loss (percentage):", result.pnl_pct)
    print("Slippage buy (bps):", args.slippage_buy_bps)
    print("Slippage sell (bps):", args.slippage_sell_bps)

if __name__ == "__main__":
    main()