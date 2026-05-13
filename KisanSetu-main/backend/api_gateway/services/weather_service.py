import os
import httpx
from dotenv import load_dotenv

# Load the variables from the .env file
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"


async def fetch_5_day_forecast(district_name: str, state_code: str = "IN"):
    """
    Fetches the 5-day weather forecast for a given district.
    """
    if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == "your_actual_api_key_here":
        return {"error": "Weather API key is missing or invalid."}

    # OpenWeather expects a query like "Pune,IN"
    query = f"{district_name},{state_code}"

    params = {
        "q": query,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",  # Returns temperature in Celsius
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            data = response.json()

            # TODO: We can parse this raw data later to make it cleaner for the Flutter app
            return {"status": "success", "data": data}

        except httpx.HTTPStatusError as e:
            return {"error": f"Failed to fetch weather: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
