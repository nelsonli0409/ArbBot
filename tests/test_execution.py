import pytest
from src.models import Order, MarketQuote
from src.execution import (
    index_to_symbol,
    validate_cycle,
    cycle_to_orders,
    simulate_cycle
)
from src.graph import (
    build_edges,
    build_edge_lookup
)

########################
# CONSTANTS
########################

DEFAULT_FEE = 0.01
DEFAULT_START_AMOUNT = 1000.0

########################
# SAMPLE OBJECTS
########################

q1 = MarketQuote(
        symbol="BTCUSDT",
        base="BTC",
        quote="USDT",
        bid=62000.0,
        ask=62010.0,
        fee=DEFAULT_FEE
    )

q2 = MarketQuote(
    symbol="ETHUSDT",
    base="ETH",
    quote="USDT",
    bid=3000.0,
    ask=3001.0,
    fee=DEFAULT_FEE
)

q3 = MarketQuote(
    symbol="SOLUSDT", 
    base="SOL", 
    quote="USDT", 
    bid=150.0, 
    ask=150.2, 
    fee=DEFAULT_FEE
)

o1 = Order(
    base="BTC",
    quote="USDT",
    amount=DEFAULT_START_AMOUNT,
    rate=1/62010.0,
    fee=DEFAULT_FEE
)

o2 = Order(
    base="ETH",
    quote="USDT",
    amount=DEFAULT_START_AMOUNT * (o1.rate * (1 - DEFAULT_FEE)),
    rate=1/3001.0,
    fee=DEFAULT_FEE
)

o3 = Order(
    base="BTC",
    quote="USDT",
    amount=DEFAULT_START_AMOUNT * (o2.rate * (1 - DEFAULT_FEE)),
    rate=62010.0,
    fee=DEFAULT_FEE
)

########################
# TESTS
########################

def test_index_to_symbol_correctness():
    nodes = {"BTC": 0, "ETH": 1, "USDT": 2}
    cycle = [1, 0, 2]
    currency_symbols = index_to_symbol(cycle, nodes)
    assert currency_symbols == ["ETH", "BTC", "USDT"]

def test_index_to_symbol_empty_cycle():
    nodes = {"BTC": 0, "ETH": 1, "USDT": 2}
    cycle = []
    currency_symbols = index_to_symbol(cycle, nodes)
    assert currency_symbols == []

def test_index_to_symbol_nonexistent_node():
    nodes = {"BTC": 0, "ETH": 1, "USDT": 2}
    cycle = [0, 4, 1]
    with pytest.raises(KeyError):
        index_to_symbol(cycle, nodes)

def test_index_to_symbol_invalid_index():
    nodes = {"BTC": 0, "ETH": 1, "USDT": 2}
    cycle = [0, 3, 1]
    with pytest.raises(KeyError):
        index_to_symbol(cycle, nodes)

def test_validate_cycle_correctness():
    currency_cycle = ["BTC", "ETH", "USDT"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)
    assert validate_cycle(currency_cycle, edge_lookup) == True

def test_validate_cycle_invalid():
    currency_cycle = ["BTC", "ETH", "SOL"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)
    assert validate_cycle(currency_cycle, edge_lookup) == ("ETH", "SOL")

def test_cycle_to_orders_correctness():
    currency_cycle = ["BTC", "USDT", "ETH"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)
    orders = cycle_to_orders(currency_cycle, edge_lookup, DEFAULT_START_AMOUNT)
    assert len(orders) == 3
    assert orders[0] == o1
    assert orders[1] == o2
    assert orders[2] == o3

def test_cycle_to_orders_invalid_currency():
    currency_cycle = ["BTC", "USDT", "SOL"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)
    with pytest.raises(KeyError):
        cycle_to_orders(currency_cycle, edge_lookup, DEFAULT_START_AMOUNT)
