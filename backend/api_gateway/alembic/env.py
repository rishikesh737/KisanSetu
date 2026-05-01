import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. Add the current directory to Python's path so it can find your models
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.models import Base

# this is the Alembic Config object
config = context.config

# 2. Tell Alembic to use the Docker environment variable for the Database URL
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL"))

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Point Alembic to your SQLAlchemy models
target_metadata = Base.metadata
