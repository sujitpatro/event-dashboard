# database.py
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Put your full connection string here:
DATABASE_URL = "postgresql://neondb_owner:npg_JjueGQ49vUas@ep-winter-resonance-a1rika9x-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, future=True)
