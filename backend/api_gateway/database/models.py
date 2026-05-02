from sqlalchemy import Column, Integer, String, Float, DateTime
from database.session import Base
from datetime import datetime


class Farmer(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True)
    district = Column(String)
    # NEW: Critical for IVR Language Routing
    preferred_language = Column(String(10), default="hi")


class DiseaseScan(Base):
    __tablename__ = "disease_scans"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer)  # Assuming a foreign key setup later
    # NEW: AI Inference Tracking
    crop_type = Column(String)
    disease_detected = Column(String)
    confidence = Column(Float)
    image_url = Column(String)  # For cloud storage fallback


class MarketPrice(Base):
    __tablename__ = "market_prices"
    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String)
    district = Column(String)
    price = Column(Float)
    # NEW: Caching Control
    cache_expires_at = Column(DateTime)
