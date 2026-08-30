import math
import pytest
from src.models import Edge, MarketQuote
from src.graph import (
    build_edges,
    build_nodes,
    index_edges
)
from src.bellman_ford import (
    find_negative_cycle,
    recover_negative_cycle
)

########################
# SAMPLE OBJECTS
########################
# bid/ask are powers of two so 1/ask is exact in floating point and fee is 0, avoiding
# rounding noise

# NEGATIVE CYCLE OBJECTS (USDT -> BTC -> ETH -> SOL -> USDT)
neg_q1 = MarketQuote(symbol="BTCUSDT", base="BTC", quote="USDT", bid=7.0, ask=8.0, fee=0.0)
neg_q2 = MarketQuote(symbol="ETHBTC", base="ETH", quote="BTC", bid=3.5, ask=4.0, fee=0.0)
neg_q3 = MarketQuote(symbol="SOLETH", base="SOL", quote="ETH", bid=1.5, ask=2.0, fee=0.0)
# bid=70 is above the 64 breakeven point, so the round trip yields more than 1 USDT
neg_q4 = MarketQuote(symbol="SOLUSDT", base="SOL", quote="USDT", bid=70.0, ask=71.0, fee=0.0)

# NO NEGATIVE CYCLE OBJECTS (same 4 currencies)
pos_q1 = MarketQuote(symbol="BTCUSDT", base="BTC", quote="USDT", bid=7.0, ask=8.0, fee=0.0)
pos_q2 = MarketQuote(symbol="ETHBTC", base="ETH", quote="BTC", bid=3.5, ask=4.0, fee=0.0)
pos_q3 = MarketQuote(symbol="SOLETH", base="SOL", quote="ETH", bid=1.5, ask=2.0, fee=0.0)
# bid=60 is below the 64 breakeven point, so the round trip yields less than 1 USDT
pos_q4 = MarketQuote(symbol="SOLUSDT", base="SOL", quote="USDT", bid=60.0, ask=61.0, fee=0.0)

# ISOLATED COMPONENT OBJECT (shares no currency with BTC/ETH/SOL/USDT)
iso_q1 = MarketQuote(symbol="DOGESHIB", base="DOGE", quote="SHIB", bid=10.0, ask=10.1, fee=0.0)

# ZERO-WEIGHT CYCLE OBJECTS (round trip yields exactly 1 USDT)
zero_q1 = MarketQuote(symbol="BTCUSDT", base="BTC", quote="USDT", bid=7.0, ask=8.0, fee=0.0)
zero_q2 = MarketQuote(symbol="ETHBTC", base="ETH", quote="BTC", bid=3.5, ask=4.0, fee=0.0)
zero_q3 = MarketQuote(symbol="SOLETH", base="SOL", quote="ETH", bid=1.5, ask=2.0, fee=0.0)
# bid=64 is the exact breakeven point (1/8 * 1/4 * 1/2 * 64 == 1), giving a zero-weight cycle
zero_q4 = MarketQuote(symbol="SOLUSDT", base="SOL", quote="USDT", bid=64.0, ask=65.0, fee=0.0)

########################
# HELPER FUNCTIONS
########################

def is_cycle_rotation(cycle: list[int], expected: list[int]) -> bool:
    """Checks whether cycle is a rotation of expected, since a cycle has no fixed
    starting node.

    Returns True if cycle is some rotation of expected, False otherwise.
    """
    if cycle is None or len(cycle) != len(expected):
        return False
    doubled = expected + expected

    # Check all possible rotations of expected to see if any match the cycle
    return any(doubled[i:i + len(expected)] == cycle for i in range(len(expected)))

########################
# TESTS
########################

def test_find_negative_cycle_correctness():
    edges = build_edges([neg_q1, neg_q2, neg_q3, neg_q4])
    nodes = build_nodes(edges)
    indexed_edges = index_edges(edges, nodes)
    cycle = find_negative_cycle(indexed_edges, len(nodes))
    # USDT -> BTC -> ETH -> SOL, expressed as node indices assigned by build_nodes
    expected = [nodes["USDT"], nodes["BTC"], nodes["ETH"], nodes["SOL"]]

    assert is_cycle_rotation(cycle, expected)

def test_find_negative_cycle_no_cycle():
    edges = build_edges([pos_q1, pos_q2, pos_q3, pos_q4, iso_q1])
    nodes = build_nodes(edges)
    indexed_edges = index_edges(edges, nodes)
    cycle = find_negative_cycle(indexed_edges, len(nodes))

    assert cycle is None

def test_find_negative_cycle_zero_weight():
    edges = build_edges([zero_q1, zero_q2, zero_q3, zero_q4])
    nodes = build_nodes(edges)
    indexed_edges = index_edges(edges, nodes)
    cycle = find_negative_cycle(indexed_edges, len(nodes))

    assert cycle is None

def test_recover_negative_cycle_correctness():
    # Nodes 0 -> 1 form a tail leading into the cycle 2 -> 3 -> 4 -> 2
    pred = [1, 2, 4, 2, 3]
    cycle = recover_negative_cycle(0, pred, 5)

    assert is_cycle_rotation(cycle, [2, 3, 4])
