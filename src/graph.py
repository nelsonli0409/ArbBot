from models import Edge, MarketQuote
from math import log

def validate_quote(q: MarketQuote) -> bool:
    """Returns true if symbol/base/quote are non-empty, bid/ask are non-negative,
    bid <= ask, and 0 <= fee < 1.

    Takes a market quote as input to validate.
    """
    return (
        bool(q.symbol and q.base and q.quote) and
        q.bid >= 0 and
        q.ask >= 0 and
        q.bid <= q.ask and
        0 <= q.fee < 1
    )

def quote_to_edges(q: MarketQuote) -> tuple[Edge, Edge]:
    """Converts a market quote into two directed edges representing the trading pair.

    Returns a tuple of two edges, the base and quote directions of the trading pair.
    """
    base_edge = Edge(
        u=q.base,
        v=q.quote,
        w=-log(q.bid*(1-q.fee)),
        symbol=q.symbol,
        action="sell",
        raw_rate=q.bid,
        fee=q.fee
    )

    quote_edge = Edge(
        u=q.quote,
        v=q.base,
        w=-log((1/q.ask)*(1-q.fee)),
        symbol=q.symbol,
        action="buy",
        raw_rate=(1/q.ask),
        fee=q.fee
    )

    return base_edge, quote_edge

def build_edges(quotes: list[MarketQuote]) -> list[Edge]:
    """Builds a list of edges from a list of market quotes.
    
    Returns a list of directed edges representing all valid market quotes.
    """
    edges = []
    for q in quotes:
        if validate_quote(q):
            edges.extend(quote_to_edges(q))
    return edges

def build_edge_lookup(edges: list[Edge]) -> dict[str, list[Edge]]:
    """Builds a dictionary mapping a currency to its outgoing edges.
    
    Returns a dictionary where the keys are currency symbols and the values are lists of edges
    originating from that currency.
    """
    lookup = {}
    for e in edges:
        # Add edge to dict mapping from currency to outgoing edges
        if e.u not in lookup:
            lookup[e.u] = []
        lookup[e.u].append(e)
    return lookup