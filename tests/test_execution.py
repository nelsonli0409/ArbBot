import pytest
from src.models import Order, MarketQuote, SimulationResult
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

DEFAULT_FEE = 0.001
DEFAULT_SLIPPAGE = 0.01
DEFAULT_START_AMOUNT = 1000.00
DEFAULT_FINAL_AMOUNT = (
    DEFAULT_START_AMOUNT 
    * ((1 - DEFAULT_FEE) ** 3) 
    * ((1 - DEFAULT_SLIPPAGE / 10000) ** 3) 
    * (1/62010.00 * 1/10052.00 * 3000.00))

########################
# SAMPLE OBJECTS
########################

q1 = MarketQuote(
    symbol="BTCUSDT",
    base="BTC",
    quote="USDT",
    bid=62000.00,
    ask=62010.00,
    fee=DEFAULT_FEE
)

q2 = MarketQuote(
    symbol="ETHUSDT",
    base="ETH",
    quote="USDT",
    bid=3000.00,
    ask=3001.00,
    fee=DEFAULT_FEE
)

q3 = MarketQuote(
    symbol="SOLUSDT", 
    base="SOL", 
    quote="USDT", 
    bid=150.00, 
    ask=150.20, 
    fee=DEFAULT_FEE
)

q4 = MarketQuote(
    symbol="ETHBTC",
    base="ETH",
    quote="BTC",
    bid=10050.00,
    ask=10052.00,
    fee=DEFAULT_FEE
)

o1 = Order(
    symbol="BTCUSDT",
    action="BUY",
    amount=DEFAULT_START_AMOUNT,
    price=62010.00,
    fee=DEFAULT_FEE
)

o2 = Order(
    symbol="ETHBTC",
    action="BUY",
    amount=o1.amount / o1.price * (1 - DEFAULT_FEE),
    price=10052.00,
    fee=DEFAULT_FEE
)

o3 = Order(
    symbol="ETHUSDT",
    action="SELL",
    amount=o2.amount / o2.price * (1 - DEFAULT_FEE),
    price=3000.00,
    fee=DEFAULT_FEE
)

s1 = SimulationResult(
    start_currency = "BTC",
    start_amount = DEFAULT_START_AMOUNT,
    final_amount = DEFAULT_FINAL_AMOUNT,
    pnl_abs = DEFAULT_FINAL_AMOUNT - DEFAULT_START_AMOUNT,
    pnl_pct = ((DEFAULT_FINAL_AMOUNT / DEFAULT_START_AMOUNT) - 1) * 100,
    orders = [o1, o2, o3],
    cycle = ["USDT", "BTC", "ETH"]
)

########################
# HELPER FUNCTIONS
########################

def approx_orders(orders: list[Order], expected: list[Order]) -> bool:
    """Assert that all fields, besides the amount, of two orders are equal, and
    approximately equal for the amount. (Needed because floating point arithmetic
    causes small differences in the amount.)

    Returns true if all fields match as described, false otherwise.
    """
    if len(orders) != len(expected):
        return False
    for order, exp in zip(orders, expected):
        if not (
            order.symbol == exp.symbol and
            order.action == exp.action and
            order.amount == pytest.approx(exp.amount) and
            order.price == exp.price and
            order.fee == exp.fee        
        ):
            return False
    # True if all orders match approximately, False otherwise
    return True

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
    currency_cycle = ["USDT", "BTC", "ETH"]
    edges = build_edges([q1, q2, q4])
    edge_lookup = build_edge_lookup(edges)

    assert validate_cycle(currency_cycle, edge_lookup) == True

def test_validate_cycle_invalid():
    currency_cycle = ["BTC", "ETH", "USDT"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)

    assert validate_cycle(currency_cycle, edge_lookup) == ("BTC", "ETH")

def test_cycle_to_orders_correctness():
    currency_cycle = ["USDT", "BTC", "ETH"]
    edges = build_edges([q1, q2, q4])
    edge_lookup = build_edge_lookup(edges)
    orders = cycle_to_orders(currency_cycle, edge_lookup, DEFAULT_START_AMOUNT)

    assert len(orders) == 3
    assert approx_orders(orders, [o1, o2, o3]) == True

def test_cycle_to_orders_invalid_currency():
    currency_cycle = ["BTC", "USDT", "SOL"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)

    with pytest.raises(ValueError):
        cycle_to_orders(currency_cycle, edge_lookup, DEFAULT_START_AMOUNT)

def test_simulate_cycle_correctness():
    currency_cycle = ["USDT", "BTC", "ETH"]
    edges = build_edges([q1, q2, q4])
    edge_lookup = build_edge_lookup(edges)
    result = simulate_cycle(currency_cycle, edge_lookup, DEFAULT_START_AMOUNT, DEFAULT_SLIPPAGE, DEFAULT_SLIPPAGE)

    assert result.final_amount == DEFAULT_FINAL_AMOUNT
    assert result.pnl_abs == DEFAULT_FINAL_AMOUNT - DEFAULT_START_AMOUNT
    assert result.pnl_pct == ((DEFAULT_FINAL_AMOUNT / DEFAULT_START_AMOUNT) - 1) * 100
    assert approx_orders(result.orders, [o1, o2, o3]) == True
    assert result.cycle == ["USDT", "BTC", "ETH"]

def test_simulate_cycle_invalid():
    currency_cycle = ["BTC", "USDT", "SOL"]
    edges = build_edges([q1, q2])
    edge_lookup = build_edge_lookup(edges)

    with pytest.raises(ValueError):
        simulate_cycle(currency_cycle, edge_lookup, DEFAULT_START_AMOUNT, DEFAULT_SLIPPAGE, DEFAULT_SLIPPAGE)

def test_simulate_cycle_no_start_amount():
    currency_cycle = ["USDT", "BTC", "ETH"]
    edges = build_edges([q1, q2, q4])
    edge_lookup = build_edge_lookup(edges)

    with pytest.raises(ValueError):
        simulate_cycle(currency_cycle, edge_lookup, 0, DEFAULT_SLIPPAGE, DEFAULT_SLIPPAGE)