import pytest

from app.utils import time_from_text_to_seconds, find_coordinates_by_time


class TestTimeFromText:
    def test_valid_hours_singular(self):
        assert time_from_text_to_seconds("3 часа") == 3 * 3600

    def test_valid_hours_plural(self):
        assert time_from_text_to_seconds("5 часов") == 5 * 3600

    def test_valid_minutes_plural(self):
        assert time_from_text_to_seconds("30 минут") == 30 * 60

    def test_combined_time(self):
        assert time_from_text_to_seconds("2 часа 15 минут") == 2 * 3600 + 15 * 60

    def test_invalid_format(self):
        # Неподдерживаемый формат возвращает 0
        assert time_from_text_to_seconds("10 минут и больше") == 0

    def test_empty_string(self):
        assert time_from_text_to_seconds("") == 0

class TestFindCoordinatesByTime:
    @pytest.fixture
    def sample_route_data(self):
        return {
            'steps': [
                {'duration': 60, 'way_points': [0, 1]},
                {'duration': 30, 'way_points': [1, 2]}
            ],
            'coordinates': [
                (0.0, 0.0),
                (1.0, 1.0),
                (2.0, 2.0)
            ]
        }

    def test_at_start(self, sample_route_data):
        point = find_coordinates_by_time(0, sample_route_data)
        assert point.lat == 0.0
        assert point.lon == 0.0

    def test_middle_first_step(self, sample_route_data):
        point = find_coordinates_by_time(30, sample_route_data)
        assert point.lat == 1.0
        assert point.lon == 1.0

    def test_middle_second_step(self, sample_route_data):
        point = find_coordinates_by_time(75, sample_route_data)
        assert point.lat == 2.0
        assert point.lon == 2.0

    def test_exceed_total_time(self, sample_route_data):
        point = find_coordinates_by_time(100, sample_route_data)
        assert point.lat == 2.0
        assert point.lon == 2.0
