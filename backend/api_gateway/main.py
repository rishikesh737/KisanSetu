from fastapi import FastAPI
from routers import weather, market, ivr

app = FastAPI(title="KisanSetu API Gateway")

# Register routers with clear versioned prefixes
app.include_router(weather.router, prefix="/api/v1/weather", tags=["Weather"])
app.include_router(market.router, prefix="/api/v1/mandi", tags=["Market"])
# Disease inference has been moved to on-device TFLite (Phase 2 Pivot)
app.include_router(ivr.router, prefix="/api/v1/ivr", tags=["Voice Engine"])


@app.get("/")
async def root():
    return {"status": "healthy", "service": "KisanSetu API Gateway"}
