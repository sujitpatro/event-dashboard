from sqlalchemy import create_engine, text

DATABASE_URL = (
    "postgresql://neondb_owner:npg_JjueGQ49vUas@ep-winter-resonance-a1rika9x-pooler.ap-southeast-1.aws.neon.tech/"
    "neondb?sslmode=require"
)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.fetchone())
