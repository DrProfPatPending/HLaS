import os
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert, Insert
from sqlalchemy.orm import sessionmaker
from db_models import club_logos, metadata
from datetime import datetime

# Update this with your actual database URL or use env var
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hlas:hlas@postgres:5432/hlas")
DEFAULT_LOGOS_DIR = "/opt/hlas/backend/club_logos" if os.path.exists("/opt/hlas/backend/club_logos") else "/app/club_logos"
LOGOS_DIR = os.getenv("LOGOS_DIR", DEFAULT_LOGOS_DIR)

def main():
    print(f"DEBUG: DATABASE_URL is {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()
    print(f"DEBUG: insert is {insert}, module: {getattr(insert, '__module__', 'NO_MODULE')}")
    print(f"DEBUG: club_logos is {club_logos}, type: {type(club_logos)}, module: {getattr(club_logos, '__module__', 'NO_MODULE')}")
    for filename in os.listdir(LOGOS_DIR):
        if filename.lower().endswith(".png"):
            short_name = filename[:-4]
            with open(os.path.join(LOGOS_DIR, filename), "rb") as f:
                image_data = f.read()
            print(f"DEBUG: insert is {insert}, module: {getattr(insert, '__module__', 'NO_MODULE')}\n")
            stmt = insert(club_logos).on_conflict_do_update(
                index_elements=[club_logos.c.club_short_name],
                set_={
                    "image_data": image_data,
                    "mime_type": "image/png",
                    "updated_at": datetime.utcnow(),
                }
            ).values(
                club_short_name=short_name,
                image_data=image_data,
                mime_type="image/png",
                updated_at=datetime.utcnow(),
            )
            session.execute(stmt)
            print(f"Imported {filename} as {short_name}")
    session.commit()
    print("All club logos imported.")

if __name__ == "__main__":
    main()
