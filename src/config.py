from dataclasses import dataclass

BINANCE_API_URL = "https://api.binance.com"

@dataclass(frozen=True)
class DataFeedConfig:
    """
    Configuration for the data feed.
    """
    base_url: str = BINANCE_API_URL
    timeout_sec: float = 5.0