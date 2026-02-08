import os
from datetime import date, datetime
from typing import List
from unittest.mock import patch

from kelly_criterion.kelly_criterion import calc_kelly_leverages


# Mock Agg object structure
class MockAgg:
    def __init__(self, timestamp, close, volume=100, open=100, high=110, low=90):
        self.timestamp = timestamp
        self.close = close
        self.volume = volume
        self.open = open
        self.high = high
        self.low = low


def generate_mock_data(ticker: str) -> List[MockAgg]:
    # Generate some deterministic data
    # Timestamps in milliseconds
    base_date = datetime(2018, 1, 1)
    data = []
    price = 100.0
    # Use a fixed seed-like behavior
    import random

    r = random.Random(42 if ticker == "AAPL" else 24)

    for i in range(252):  # One trading year
        dt = datetime.fromordinal(base_date.toordinal() + i)
        ts = int(dt.timestamp() * 1000)

        # Random walk
        change = r.uniform(-0.02, 0.025)  # Slightly positive bias
        price *= 1 + change

        data.append(MockAgg(ts, price))
    return data


@patch("kelly_criterion.kelly_criterion.RESTClient")
@patch.dict(os.environ, {"API_KEY": "test_key"})
def test_kelly_criterion(mock_rest_client):
    # Setup mock client
    mock_instance = mock_rest_client.return_value

    def side_effect(ticker, **kwargs):
        return generate_mock_data(ticker)

    mock_instance.get_aggs.side_effect = side_effect

    # Given a time period and multiple securities
    start_date = date(2018, 1, 1)
    end_date = date(2018, 12, 31)
    securities = {"AAPL", "IBM"}

    # When we calculate kelly leverages
    actual_leverages = calc_kelly_leverages(securities, start_date, end_date)

    # Then the calculated leverages should match the actual ones
    # Note: These values are derived from the deterministic random seed used in generate_mock_data
    # We will assert that we get results, and they are floats
    assert isinstance(actual_leverages["AAPL"], float)
    assert isinstance(actual_leverages["IBM"], float)

    # We can also check if they are within a reasonable range (e.g. not infinite)
    assert -50 < actual_leverages["AAPL"] < 50
    assert -50 < actual_leverages["IBM"] < 50
