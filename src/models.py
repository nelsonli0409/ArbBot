from dataclasses import dataclass

@dataclass(frozen=True)
class Edge:
    """
    A directed edge representing a trading edge between two assets in a market.
    """
    u: str
    v: str
    w: float # Weight, represents how profitable the trade is after fees
    symbol: str # The trading pair symbol, e.g., "BTC/USDT"
    action: str # BUY or SELL
    raw_rate: float # The raw exchange rate, either bid or 1/ask
    fee: float # Trading fee for the edge

@dataclass(frozen=True)
class Order:
    """
    Represents an order to trade a specific amount of an asset in the market.
    """
    symbol: str
    action: str
    amount: float # The amount of the asset to trade
    price: float # The price (bid/ask) at which the order will be executed

@dataclass(frozen=True)
class MarketQuote:
    """
    Represents a market quote for a specific trading pair.
    """
    symbol: str
    base: str
    quote: str
    bid: float # The highest price a buyer is willing to pay for the asset
    ask: float # The lowest price a seller is willing to accept for the asset
    fee: float # The trading fee for the market quote
