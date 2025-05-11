import requests
from app.models.point import Point
from app.models.step import Step

cancellation_map = {
    "FULLY_REFUNDABLE": "Да",
    "PARTIALLY_REFUNDABLE": "Частично",
    "NON_REFUNDABLE": "Нет"
}


def time_from_text_to_seconds(time: str):
    words = time.split()
    time_in_seconds = 0
    try:
        if len(words) == 2:  # 4 часа; 5 часов; 42 минуты; 50 минут
            if words[1] == 'часа' or words[1] == 'часов':
                time_in_seconds = int(words[0]) * 3600
            elif words[1] == 'минуты' or words[1] == 'минут':
                time_in_seconds = int(words[0]) * 60
        elif len(words) == 4:  # 4 часа 5 минут; 5 часов 42 минуты и тд
            time_in_seconds = int(words[0]) * 3600 + int(words[2]) * 60
    except:
        raise Exception("Пожалуйста, введите данные в верном формате")
    finally:
        return time_in_seconds


def find_coordinates_by_time(time: int, route_data: dict) -> Point:
    """Find the coordinates of the point on the route by time"""

    cur_time = 0
    path_steps: list[dict] = route_data['steps']
    path_coords = route_data['coordinates']

    for step in path_steps:
        step_ = Step(**step)
        if time <= cur_time + step_.duration:
            if time == cur_time:
                lon, lat = path_coords[step_.way_points[0]]
            else:
                part_in_the_list_of_coords = (time - cur_time) / step_.duration
                index = int(len(step_.way_points) * part_in_the_list_of_coords)
                lon, lat = path_coords[step_.way_points[index]]
            return Point(lat=lat, lon=lon)
        cur_time += step_.duration

    # If time exceeds the total duration, return the last coordinate
    lon, lat = path_coords[-1]
    point = Point(lat=lat, lon=lon)
    return point


async def get_hotel_booking_offer(offer_id, affiliate_clid=None):
    base_url = f"https://whitelabel.travel.yandex-net.ru/hotels/booking/offers/{offer_id}"

    params = {}
    if affiliate_clid:
        params["affiliate_clid"] = affiliate_clid

    try:
        response = requests.get(
            url=base_url,
            params=params,
            headers={
                "Accept": "application/json",
                "User-Agent": "Python Hotel Booking Client"
            }
        )
        return response

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise


async def create_hotel_booking_order(
        booking_token: str,
        customer_email: str,
        customer_phone: str,
        guests: list[dict],
        use_deferred_payments: bool = False,
        comment: str = None,
        promo_codes: list[str] = None
) -> dict:
    url = "https://whitelabel.travel.yandex-net.ru/hotels/booking/orders"

    payload = {
        "booking_token": booking_token,
        "use_deferred_payments": use_deferred_payments,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "guests": guests
    }

    if comment:
        payload["comment"] = comment
    if promo_codes:
        payload["promo_codes"] = promo_codes

    try:
        response = requests.post(
            url=url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Python Hotel Booking Client"
            }
        )
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise


async def start_hotel_booking_payment(
        order_id: str,
        return_url: str,
        theme: str | None = "light",
        device: str | None = "desktop"
) -> dict:
    url = f"https://whitelabel.travel.yandex-net.ru/hotels/booking/orders/{order_id}/payment/start"

    payload = {
        "return_url": return_url
    }

    if theme:
        payload["theme"] = theme
    if device:
        payload["device"] = device

    try:
        response = requests.post(
            url=url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Python Hotel Booking Client"
            }
        )
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Payment start error: {e}")
        raise


async def get_hotel_booking_status(order_id: str) -> dict:
    url = f"https://whitelabel.travel.yandex-net.ru/hotels/booking/orders/{order_id}/status"

    try:
        response = requests.get(
            url=url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Python Hotel Booking Client"
            }
        )
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Status check error: {e}")
        raise
