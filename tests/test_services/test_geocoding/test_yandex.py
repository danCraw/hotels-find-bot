import pytest
import json
from unittest.mock import patch, MagicMock

from app.services.geocoding.yandex import yandex_city_geocoding
from app.models.point import Point


@patch("app.services.geocoding.yandex.requests.get")
def test_yandex_city_geocoding_success(mock_get):
    fake_response = {
        "response": {
            "GeoObjectCollection": {
                "featureMember": [
                    {
                        "GeoObject": {
                            "Point": {
                                "pos": "37.617635 55.755814"
                            }
                        }
                    }
                ]
            }
        }
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = fake_response
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    result = yandex_city_geocoding("Москва")
    assert isinstance(result, Point)
    assert result.lat == 55.755814
    assert result.lon == 37.617635


@patch("app.services.geocoding.yandex.requests.get")
def test_yandex_city_geocoding_invalid_json(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_get.return_value = mock_resp

    with pytest.raises(Exception, match="Failed to decode JSON response"):
        yandex_city_geocoding("Москва")


@patch("app.services.geocoding.yandex.requests.get")
def test_yandex_city_geocoding_missing_coordinates(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "response": {
            "GeoObjectCollection": {
                "featureMember": []
            }
        }
    }
    mock_get.return_value = mock_resp

    with pytest.raises(Exception, match="Failed to extract coordinates from JSON response"):
        yandex_city_geocoding("Москва")
