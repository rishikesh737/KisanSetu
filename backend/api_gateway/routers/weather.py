from fastapi import APIRouter
from services.weather_service import fetch_5_day_forecast

router = APIRouter()


@router.get("/{district}")
async def get_weather(district: str):
    """
    Fetch 5-day weather forecast by district.
    """
    return await fetch_5_day_forecast(district_name=district)
