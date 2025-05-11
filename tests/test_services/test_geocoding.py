import json

import pytest
from unittest.mock import Mock, patch

import requests

from app.config import OPEN_ROUTE_SERVICE_API_KEY
from app.models.point import Point
from app.services.geocoding import (
    openrouteservice_city_geocoding,
    openrouteservice_reverse_geocoding
)

@pytest.fixture
def mock_requests_get():
    with patch('requests.get') as mock_get:
        yield mock_get

@pytest.fixture
def mock_requests_request():
    with patch('requests.request') as mock_request:
        yield mock_request

def test_city_geocoding_success(mock_requests_request):
    mock_response = Mock()
    mock_response.text = json.dumps({
        "features": [
            {
                "geometry": {"coordinates": [37.6176, 55.7558]},
                "properties": {"name": "Moscow"}
            }
        ]
    })
    mock_requests_request.return_value = mock_response

    result = openrouteservice_city_geocoding("Moscow")

    assert isinstance(result, Point)
    assert result.lat == 55.7558
    assert result.lon == 37.6176
    mock_requests_request.assert_called_once_with(
        "GET",
        f"https://api.openrouteservice.org/geocode/search"
        f"?api_key={OPEN_ROUTE_SERVICE_API_KEY}&text=Moscow"
    )

def test_city_geocoding_no_features(mock_requests_request):
    mock_response = Mock()
    mock_response.text = json.dumps({"features": []})
    mock_requests_request.return_value = mock_response

    with pytest.raises(IndexError):
        openrouteservice_city_geocoding("InvalidCity")

def test_reverse_geocoding_success(mock_requests_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "layer": "locality",
                    "name": "Москва"
                }
            }
        ]
    }
    mock_requests_get.return_value = mock_response
    point = Point(lat=55.7558, lon=37.6176)

    result = openrouteservice_reverse_geocoding(point)

    assert result == "Москва"
    mock_requests_get.assert_called_once_with(
        f"https://api.openrouteservice.org/geocode/reverse"
        f"?api_key={OPEN_ROUTE_SERVICE_API_KEY}"
        f"&point.lon=37.6176&point.lat=55.7558"
    )

def test_reverse_geocoding_fallback(mock_requests_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        "features": [
            {
                "properties": {
                    "layer": "street",
                    "name": "Тверская улица"
                }
            }
        ]
    }
    mock_requests_get.return_value = mock_response
    point = Point(lat=55.7558, lon=37.6176)

    result = openrouteservice_reverse_geocoding(point)

    assert result == "Тверская улица"

def test_reverse_geocoding_empty_features(mock_requests_get):
    mock_response = Mock()
    mock_response.json.return_value = {"features": []}
    mock_requests_get.return_value = mock_response
    point = Point(lat=0, lon=0)

    result = openrouteservice_reverse_geocoding(point)

    assert result is None

def test_reverse_geocoding_http_error(mock_requests_get):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
    mock_requests_get.return_value = mock_response
    point = Point(lat=55.7558, lon=37.6176)

    with pytest.raises(requests.HTTPError):
        openrouteservice_reverse_geocoding(point)
        