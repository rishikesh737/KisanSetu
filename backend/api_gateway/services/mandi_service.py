import os
import httpx
from dotenv import load_dotenv

load_dotenv()

AGMARKNET_API_KEY = os.getenv("AGMARKNET_API_KEY")
RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"


async def fetch_mandi_prices(crop_name: str, state_code: str = "Goa"):
    """
    Fetches real-time Mandi prices directly from the Indian Government (data.gov.in).
    """
    if not AGMARKNET_API_KEY or AGMARKNET_API_KEY == "optional_if_required":
        return {"error": "Agmarknet API key is missing or invalid."}

    # data.gov.in uses specific filter parameters in the URL
    params = {
        "api-key": AGMARKNET_API_KEY,
        "format": "json",
        "filters[state]": state_code.title(),
        "filters[commodity]": crop_name.title(),
        "limit": 10,  # Fetch the 10 most recent market reports
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()
            print(f"DEBUG: Government API Response: {data}")

            # The government API returns a list of dictionaries inside the 'records' key
            records = data.get("records", [])

            # Clean up the data to match the contract we promised the Flutter team
            # Updated loop logic inside fetch_mandi_prices
            cleaned_data = []
            for item in records:
                cleaned_data.append(
                    {
                        # Checking both lowercase and title case to be safe
                        "market": item.get("market") or item.get("Market") or "Unknown",
                        "min_price": item.get("min_price")
                        or item.get("Min_Price")
                        or 0,
                        "max_price": item.get("max_price")
                        or item.get("Max_Price")
                        or 0,
                        "modal_price": item.get("modal_price")
                        or item.get("Modal_Price")
                        or 0,
                        "arrival_date": item.get("arrival_date")
                        or item.get("Arrival_Date")
                        or "",
                    }
                )

            return {
                "status": "success",
                "crop": crop_name,
                "state": state_code,
                "data": cleaned_data,
            }

        except httpx.HTTPStatusError as e:
            return {"error": f"Failed to fetch Mandi data: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {repr(e)}"}
