import pytest
import requests
from unittest.mock import patch, Mock
from src.models import MarketQuote
from src.config import DataFeedConfig
from src.data_feed import (
    fetch_book_ticker_raw,
    build_symbol_map,
    normalize_book_ticker_row,
    fetch_quotes
)

########################
# CONSTANTS
########################

DEFAULT_CONFIG = DataFeedConfig(base_url="https://example.test", timeout_sec=2.5)

########################
# TESTS
########################

def test_fetch_book_ticker_raw_returns_api_json():
    response = Mock()
    response.json.return_value = [
        {"symbol": "BTCUSDT", "bidPrice": "100000.00", "askPrice": "100001.00"}
    ]
    
    # Patch the requests.get method to return the mocked response
    with patch("src.data_feed.requests.get", return_value=response) as mock_get:
        result = fetch_book_ticker_raw(DEFAULT_CONFIG)

    assert result == response.json.return_value

    # Ensure the API was called with the correct URL and timeout
    mock_get.assert_called_once_with(
        "https://example.test/api/v3/ticker/bookTicker",
        timeout=2.5
    )
    # Ensure raise_for_status was not called during the test
    response.raise_for_status.assert_called_once()

def test_fetch_book_ticker_raw_returns_empty_list_on_request(caplog):
    with patch(
        "src.data_feed.requests.get",
        side_effect=requests.RequestException("connection refused")
    ):
        result = fetch_book_ticker_raw(DEFAULT_CONFIG)

    assert result == []
    assert "connection refused" in caplog.text

def test_build_symbol_map_returns_base_and_quote():
    response = Mock()
    response.json.return_value = {
        "symbols": [
            {"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT"},
            {"symbol": "ETHBTC", "baseAsset": "ETH", "quoteAsset": "BTC"},
            {"symbol": "SOLBTC", "baseAsset": "SOL", "quoteAsset": "BTC"}
        ]
    }

    with patch("src.data_feed.requests.get", return_value=response) as mock_get:
        result = build_symbol_map(DEFAULT_CONFIG)

    assert result == {
        "BTCUSDT": ("BTC", "USDT"),
        "ETHBTC": ("ETH", "BTC"),
        "SOLBTC": ("SOL", "BTC")
    }

    mock_get.assert_called_once_with(
        "https://example.test/api/v3/exchangeInfo",
        timeout=2.5
    )
    response.raise_for_status.assert_called_once()

def test_build_symbol_map_returns_empty_dict_on_request_error(caplog):
    with patch(
        "src.data_feed.requests.get",
        side_effect=requests.RequestException("connection refused")
    ):
        result = build_symbol_map(DEFAULT_CONFIG)

    assert result == {}
    assert "connection refused" in caplog.text

def test_build_symbol_map_returns_empty_dict_on_http_error(caplog):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("503 Server Error")

    with patch("src.data_feed.requests.get", return_value=response):
        result = build_symbol_map(DEFAULT_CONFIG)

    assert result == {}
    assert "503 Server Error" in caplog.text

def test_normalize_book_ticker_row_rejects_crossed_market():
    result = normalize_book_ticker_row(
        {"symbol": "BTCUSDT", "bidPrice": "100.00", "askPrice": "100.00"},
        fee=0.01,
        symbol_map={"BTCUSDT": ("BTC", "USDT")}
    )

    assert result is None

def test_fetch_quotes_normalizes_valid_rows():
    raw_rows = [
        {"symbol": "BTCUSDT", "bidPrice": "100000.00", "askPrice": "100001.00"},
        {"symbol": "BADPAIR", "bidPrice": "1.00", "askPrice": "2.00"}
    ]

    symbol_map = {"BTCUSDT": ("BTC", "USDT")}

    # Patch the fetch_book_ticker_raw and build_symbol_map functions to return the test data
    with (
        patch("src.data_feed.fetch_book_ticker_raw", return_value=raw_rows),
        patch("src.data_feed.build_symbol_map", return_value=symbol_map)
    ):
        quotes = fetch_quotes(0.01, DEFAULT_CONFIG)

    assert quotes == [
        MarketQuote(
            symbol="BTCUSDT",
            base="BTC",
            quote="USDT",
            bid=100000.00,
            ask=100001.00,
            fee=0.01
        )
    ]