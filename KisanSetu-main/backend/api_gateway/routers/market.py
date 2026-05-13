from fastapi import APIRouter
from services.mandi_service import fetch_mandi_prices

router = APIRouter()


@router.get("/{crop}")
async def get_mandi_prices(crop: str):
    """
    Fetch daily Mandi prices for a specific crop.
    """
    return await fetch_mandi_prices(crop_name=crop)
