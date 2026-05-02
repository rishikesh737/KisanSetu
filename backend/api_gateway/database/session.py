import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Pulls the connection string from docker-compose.yml
# Falls back to localhost if running outside the container
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://kisan_admin:kisan_password@localhost:5432/kisansetu"
)

# Initialize the engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our models to inherit
Base = declarative_base()
