from fastapi import FastAPI
from services.weather_service import fetch_5_day_forecast
from services.mandi_service import fetch_mandi_prices

app = FastAPI(title="KisanSetu API")


@app.get("/")
async def root():
    return {"status": "healthy", "service": "KisanSetu API"}


@app.get("/api/v1/weather/{district}")
async def get_weather(district: str):
    """
    Endpoint for the Flutter app and IVR to fetch weather by district.
    """
    weather_data = await fetch_5_day_forecast(district_name=district)
    return weather_data


@app.get("/api/v1/mandi/{crop}")
async def get_mandi_prices(crop: str):
    """
    Endpoint to fetch daily Mandi prices for a specific crop.
    """
    mandi_data = await fetch_mandi_prices(crop_name=crop)
    return mandi_data
