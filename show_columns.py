from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://neondb_owner:npg_JjueGQ49vUas@ep-winter-resonance-a1rika9x-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public'
        ORDER BY table_name, ordinal_position;
    """))

    for row in result:
        print(row)
