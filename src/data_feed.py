from .models import MarketQuote
from .config import DataFeedConfig
import requests
import logging

DEFAULT_CONFIG = DataFeedConfig(base_url="https://api.binance.us")

def fetch_book_ticker_raw(config: DataFeedConfig = DEFAULT_CONFIG) -> list[dict]:
    """Fetches raw best bid/ask rows from exchange REST endpoint.
    
    Returns a list of raw json data from the exchange.
    """
    try:
        url = f"{config.base_url}/api/v3/ticker/bookTicker"
        response = requests.get(url, timeout=config.timeout_sec)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching book ticker: {e}")
        return []

def build_symbol_map(config: DataFeedConfig = DEFAULT_CONFIG) -> dict[str, tuple[str, str]]:
    """Parses a Binance trading pair symbol into its base and quote assets.
    
    Returns a tuple containing the base and quote assets.
    """
    url = f"{config.base_url}/api/v3/exchangeInfo"
    currency_symbols = {}
    try:
        response = requests.get(url, timeout=config.timeout_sec)
        response.raise_for_status()
        exchange_info = response.json()

        for s in exchange_info['symbols']:
            currency_symbols[s['symbol']] = (s['baseAsset'], s['quoteAsset'])
        
        return currency_symbols
    except requests.RequestException as e:
        logging.error(f"Error fetching exchange info: {e}")

    return {}

def normalize_book_ticker_row(
    row: dict, 
    fee: float, 
    symbol_map: dict[str, tuple[str, str]]
) -> MarketQuote | None:
    """Converts a raw row into MarketQuote.
    
    Returns a MarketQuote object if the row is valid, otherwise None.
    """
    try:
        symbol = row.get('symbol')
        if not symbol or symbol not in symbol_map:
            return None

        base, quote = symbol_map[symbol]
        bid = float(row['bidPrice'])
        ask = float(row['askPrice'])

        # Return None instead of raising error because inactive/delisted pairs may
        # have invalid bid/ask prices
        if bid <= 0 or ask <= 0 or bid >= ask:
            return None
        
        return MarketQuote(
            symbol=symbol,
            base=base,
            quote=quote,
            bid=bid,
            ask=ask,
            fee=fee
        )
    except (KeyError, ValueError, TypeError) as e:
        logging.debug(f"Error normalizing book ticker row {row}: {e}")
        return None

def fetch_quotes(fee: float, config: DataFeedConfig = DEFAULT_CONFIG) -> list[MarketQuote]:
    """Fetch and normalize all quotes for downstream graph construction.
    
    Returns a list of normalized MarketQuote objects.
    """
    raw_rows = fetch_book_ticker_raw(config)
    symbol_map = build_symbol_map(config)
    quotes = []
    for row in raw_rows:
        quote = normalize_book_ticker_row(row, fee, symbol_map)
        if quote is not None:
            quotes.append(quote)
    return quotes