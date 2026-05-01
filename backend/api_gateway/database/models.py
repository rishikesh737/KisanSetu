# backend/api_gateway/database/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    language = Column(
        String(10), nullable=False, default="en"
    )  # e.g., 'mr' for Marathi, 'kok' for Konkani
    state = Column(String(50), nullable=False)
    district = Column(String(50), nullable=False)
    primary_crop = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # A farmer can have many disease scans
    scans = relationship("DiseaseScan", back_populates="farmer")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(50), index=True)
    district = Column(String(50), index=True)
    market = Column(String(50))
    commodity = Column(String(50), index=True)
    min_price = Column(Float)
    max_price = Column(Float)
    modal_price = Column(Float)
    arrival_date = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)


class DiseaseScan(Base):
    __tablename__ = "disease_scans"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"))
    image_path = Column(String(255))  # Where the image is stored
    detected_disease = Column(String(100))
    confidence_score = Column(Float)
    scanned_at = Column(DateTime, default=datetime.datetime.utcnow)

    farmer = relationship("Farmer", back_populates="scans")
