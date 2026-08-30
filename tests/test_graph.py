import math
import pytest
from src.models import MarketQuote
from src.graph import (
    validate_quote,
    quote_to_edges,
    build_edges,
    build_edge_lookup,
    build_nodes,
    index_edges
)

########################
# CONSTANTS
########################

FEE = 0.01

########################
# SAMPLE OBJECTS
########################

q1 = MarketQuote(
        symbol="BTCUSDT",
        base="BTC",
        quote="USDT",
        bid=62000.0,
        ask=62010.0,
        fee=FEE
    )

q2 = MarketQuote(
    symbol="ETHUSDT",
    base="ETH",
    quote="USDT",
    bid=3000.0,
    ask=3001.0,
    fee=FEE
)

q3 = MarketQuote(
    symbol="SOLUSDT", 
    base="SOL", 
    quote="USDT", 
    bid=150.0, 
    ask=150.2, 
    fee=FEE
)

########################
# TESTS
########################

def test_validate_quote_accepts_valid_quote():
    assert validate_quote(q1) is True

def test_validate_quote_rejects_bad_spread():
    bad_quote = MarketQuote(
        symbol="BTCUSDT", 
        base="BTC", 
        quote="USDT", 
        bid=62010.0, 
        ask=62010.0, 
        fee=FEE
    )
    assert validate_quote(bad_quote) is False

def test_quote_to_edges_returns_two_directed_edges():
    e1, e2 = quote_to_edges(q2)
    pairs = {(e1.u, e1.v), (e2.u, e2.v)}

    assert pairs == {("ETH", "USDT"), ("USDT", "ETH")}

def test_quote_to_edges_uses_expected_rates():
    base_edge, quote_edge = quote_to_edges(q2)

    # One edge should use bid, the other 1/ask
    raw_rates = sorted([base_edge.raw_rate, quote_edge.raw_rate])
    assert raw_rates[0] == pytest.approx(1 / 3001.0)
    assert raw_rates[1] == pytest.approx(3000.0)

def test_edge_weights_are_negative_log_of_effective_rate():
    e1, e2 = quote_to_edges(q1)
    for e in (e1, e2):
        r_effective = e.raw_rate * (1 - e.fee)
        assert e.w == pytest.approx(-math.log(r_effective))

def test_build_edges_skips_invalid_quotes():
    # bid >= ask
    bad1 = MarketQuote(
        symbol="BADUSDT",
        base="BAD",
        quote="USDT",
        bid=10.0,
        ask=9.0,
        fee=FEE
    )
    # bid < 0
    bad2 = MarketQuote(
        symbol="BADUSDT",
        base="BAD",
        quote="USDT",
        bid=-1,
        ask=9.0,
        fee=FEE
    )
    # ask < 0
    bad3 = MarketQuote(
        symbol="BADUSDT",
        base="BAD",
        quote="USDT",
        bid=10.0,
        ask=-1.0,
        fee=FEE
    )

    edges = build_edges([q1, bad1, bad2, bad3])
    assert len(edges) == 2  # Only good quote contributes

def test_build_edge_lookup_contains_directed_pairs():
    edges = build_edges([q3])
    lookup = build_edge_lookup(edges)
    assert ("SOL", "USDT") in lookup
    assert ("USDT", "SOL") in lookup

def test_build_edge_lookup_handles_empty_edges():
    edges = []
    lookup = build_edge_lookup(edges)
    assert lookup == {}

def test_build_edge_lookup_handles_similar_edges():
    q1_duplicate = MarketQuote(
        symbol=q1.symbol,
        base=q1.base,
        quote=q1.quote,
        bid=q2.bid,
        ask=q2.ask,
        fee=q1.fee
    )
    edges = build_edges([q1, q1_duplicate])
    lookup = build_edge_lookup(edges)

    assert len(lookup) == 2

def test_build_nodes_creates_unique_nodes():
    edges = build_edges([q1, q2])
    nodes = build_nodes(edges)
    assert nodes == {"BTC": 0, "USDT": 1, "ETH": 2}

def test_build_nodes_handles_empty_edges():
    edges = []
    nodes = build_nodes(edges)
    assert nodes == {}

def test_build_nodes_handles_duplicate_nodes():
    dupe = MarketQuote(
        symbol=q1.symbol,
        base=q1.base,
        quote=q1.quote,
        bid=q1.bid,
        ask=q1.ask,
        fee=q1.fee
    )
    edges = build_edges([q1, dupe])
    nodes = build_nodes(edges)
    assert nodes == {"BTC": 0, "USDT": 1}

def test_index_edges_returns_correct_tuple():
    edges = build_edges([q1, q2])
    nodes = build_nodes(edges)
    indexed = index_edges(edges, nodes)
    assert indexed == [(nodes["BTC"], nodes["USDT"], edges[0].w, edges[0]), 
                       (nodes["USDT"], nodes["BTC"], edges[1].w, edges[1]),
                       (nodes["ETH"], nodes["USDT"], edges[2].w, edges[2]),
                       (nodes["USDT"], nodes["ETH"], edges[3].w, edges[3])]

def test_index_edges_handles_empty_edges():
    edges = []
    nodes = {}
    indexed = index_edges(edges, nodes)
    assert indexed == []