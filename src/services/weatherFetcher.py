import os
import requests
import pandas as pd

def fetch_weather(api_key, location, start_date, end_date, cache_dir="weather_cache"):
    os.makedirs(cache_dir, exist_ok=True)
    cache_filename = f"{location.replace(',', '_')}_{start_date}_{end_date}.csv"
    cache_path = os.path.join(cache_dir, cache_filename)

    #Use cached file if it exists, bc visual crossing has rate limit
    if os.path.exists(cache_path):
        print(f"Using cached weather data: {cache_path}")
        return pd.read_csv(cache_path, parse_dates=["timestamp"])

    #Call Visual Crossing API
    url = (
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
        f"{location}/{start_date}/{end_date}?unitGroup=us&include=hours&key={api_key}&contentType=json"
    )
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    #Parse hourly weather data
    hourly_data = []
    for day in data['days']:
        for hour in day['hours']:
            hourly_data.append({
                'timestamp': pd.to_datetime(hour['datetimeEpoch'], unit='s', utc=True).tz_convert('US/Central'),
                'temperature': hour.get('temp'),
                'windspeed': hour.get('windspeed'),
                'solar_irradiance': hour.get('solarradiation', None)
            })

    df = pd.DataFrame(hourly_data)
    df['timestamp'] = df['timestamp'].dt.floor('H')

    #Save to cache
    df.to_csv(cache_path, index=False)
    print(f"Cached weather data at: {cache_path}")
    return df