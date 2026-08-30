from dataclasses import dataclass

@dataclass(frozen=True)
class DataFeedConfig:
    """
    Configuration for the data feed.
    """
    base_url: str
    timeout_sec: float = 5.0