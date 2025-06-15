import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

import sys
sys.path.append("/home/ubuntu/Crawler")
from main import parse_normalized_date, clean_html, save_to_mongo

@pytest.fixture
def mock_mongo_collection():
    with patch("main.collection") as mock_collection:
        yield mock_collection

def test_parse_normalized_date_today():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    assert parse_normalized_date("сегодня") == today

def test_parse_normalized_date_tomorrow():
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    assert parse_normalized_date("завтра") == tomorrow

def test_parse_normalized_date_after_tomorrow():
    after_tomorrow = (datetime.now() + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    assert parse_normalized_date("послезавтра") == after_tomorrow

def test_parse_normalized_date_full_date_ru():
    assert parse_normalized_date("08 июня 2025") == datetime(2025, 6, 8)

def test_parse_normalized_date_full_date_dot():
    assert parse_normalized_date("08.06.2025") == datetime(2025, 6, 8)

def test_parse_normalized_date_day_month_ru():
    current_year = datetime.now().year
    assert parse_normalized_date("8 июня") == datetime(current_year, 6, 8)

def test_parse_normalized_date_invalid():
    assert parse_normalized_date("неверная дата") is None


def test_clean_html_basic():
    html_input = "<p>Hello <strong>World</strong>!</p>"
    expected_output = "<p>Hello <strong>World</strong>!</p>"
    assert clean_html(html_input) == expected_output

def test_clean_html_unallowed_tags():
    html_input = "<div><script>alert('hi');</script><p>Test</p></div>"
    expected_output = "<div><p>Test</p></div>"
    assert clean_html(html_input) == expected_output

def test_clean_html_attributes():
    html_input = "<a href=\"#\" class=\"btn\">Link</a>"
    expected_output = "<a href=\"#\">Link</a>"
    assert clean_html(html_input) == expected_output


def test_save_to_mongo_new_event(mock_mongo_collection):
    mock_mongo_collection.find_one.return_value = None
    events = [{
        "title": "Test Event",
        "date": "2025-01-01",
        "location": "Test Location",
        "source": "test"
    }]
    result = save_to_mongo(events)
    mock_mongo_collection.insert_one.assert_called_once_with(events[0])
    assert result == 1

def test_save_to_mongo_existing_event(mock_mongo_collection):
    mock_mongo_collection.find_one.return_value = {"title": "Existing Event"}
    events = [{
        "title": "Existing Event",
        "date": "2025-01-01",
        "location": "Test Location",
        "source": "test"
    }]
    result = save_to_mongo(events)
    mock_mongo_collection.insert_one.assert_not_called()
    assert result == 0

def test_save_to_mongo_no_collection():
    with patch("main.collection", None):
        events = [{
            "title": "Test Event",
            "date": "2025-01-01",
            "location": "Test Location",
            "source": "test"
        }]
        result = save_to_mongo(events)
        assert result == 0


