"""Open-Meteo API client for fetching hourly precipitation probability."""
import requests
from datetime import datetime, timezone


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_rain_forecast(latitude: float, longitude: float, hours_ahead: int) -> list[dict]:
    """
    Fetch precipitation probability for the next `hours_ahead` hours.

    Returns a list of dicts:
        [{"time": datetime, "precipitation_probability": int}, ...]
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation_probability",
        "forecast_days": 2,
        "timezone": "auto",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    times = data["hourly"]["time"]
    probs = data["hourly"]["precipitation_probability"]

    now = datetime.now(timezone.utc).astimezone()
    results = []

    for time_str, prob in zip(times, probs):
        # Open-Meteo returns times like "2026-04-01T08:00"
        dt = datetime.fromisoformat(time_str)
        if dt.tzinfo is None:
            # Attach the local timezone offset returned in the response
            tz_offset_seconds = data.get("utc_offset_seconds", 0)
            from datetime import timedelta
            tz = timezone(timedelta(seconds=tz_offset_seconds))
            dt = dt.replace(tzinfo=tz)

        diff_hours = (dt - now).total_seconds() / 3600
        if 0 <= diff_hours <= hours_ahead:
            results.append({
                "time": dt,
                "precipitation_probability": prob if prob is not None else 0,
            })

    return results
