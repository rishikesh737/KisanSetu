import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Pulls the connection string from docker-compose.yml
# Falls back to SQLite for local testing
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql"):
    # Use SQLite for local testing when no PostgreSQL available
    SQLALCHEMY_DATABASE_URL = "sqlite:///./kisansetu.db"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./kisansetu.db"

# Initialize the engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit
Base = declarative_base()
