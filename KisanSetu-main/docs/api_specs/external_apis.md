# 🌍 External Integrations API Specs

This document defines the endpoints that communicate with third-party services (OpenWeatherMap and Data.gov.in).

---

## 1. Weather Forecast
Fetches a 5-day / 3-hour interval weather forecast for a specified location.

*   **Endpoint:** `/api/v1/weather/{city}`
*   **Method:** `GET`
*   **Path Parameters:**
    *   `city` (string): The name of the city/district (e.g., `Goa`, `Pune`).

### Success Response (200 OK)
```json
{
  "status": "success",
  "data": {
    "list": [
      {
        "dt_txt": "2026-05-02 12:00:00",
        "main": {
          "temp": 31.21,
          "humidity": 54
        },
        "weather": [
          {
            "main": "Clear",
            "description": "clear sky"
          }
        ]
      }
    ],
    "city": {
      "name": "Goa"
    }
  }
}
```


## 2. Mandi Market Prices
Fetches the 10 most recent market prices for a specific commodity from the Indian Government's Agmarknet database.

* Endpoint: /api/v1/mandi/{crop}
* Method: GET
* Path Parameters:
* crop (string): The name of the commodity (e.g., Tomato, Onion).
      * Query Parameters:
* state_code (string, optional, default: Goa): The state to filter by (e.g., Maharashtra).
      * Success Response (200 OK)
  
### Success Response (200 OK)
```json
  
{
  "status": "success",
  "crop": "Tomato",
  "state": "Maharashtra",
  "data": [
    {
      "market": "Pune",
      "min_price": 1200,
      "max_price": 1800,
      "modal_price": 1500,
      "arrival_date": "02/05/2026"
    }
  ]
}
```
Note: If no data is available for the given crop/state combination today, the data array will return empty [].
