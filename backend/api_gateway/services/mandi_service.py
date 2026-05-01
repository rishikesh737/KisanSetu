import httpx


async def fetch_mandi_prices(crop_name: str, state_code: str = "Goa"):
    """
    Fetches current Mandi prices for a specific crop.
    (Mock implementation for MVP until Agmarknet API access is secured)
    """
    # TODO: Replace with actual httpx call to data.gov.in / Agmarknet

    mock_data = {
        "status": "success",
        "crop": crop_name,
        "state": state_code,
        "data": [
            {
                "market": "Bicholim",
                "min_price": 2400,
                "max_price": 2800,
                "modal_price": 2500,
                "unit": "Quintal",
            },
            {
                "market": "Panaji",
                "min_price": 2500,
                "max_price": 2900,
                "modal_price": 2600,
                "unit": "Quintal",
            },
        ],
    }

    return mock_data
