import os
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker
from db_models import club_logos, metadata
from datetime import datetime

# Update this with your actual database URL or use env var
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/hlas")
LOGOS_DIR = os.getenv("LOGOS_DIR", "/app/club_logos")

def main():
    engine = create_engine(DATABASE_URL)
    metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()
    for filename in os.listdir(LOGOS_DIR):
        if filename.lower().endswith(".png"):
            short_name = filename[:-4]
            with open(os.path.join(LOGOS_DIR, filename), "rb") as f:
                image_data = f.read()
            stmt = insert(club_logos).values(
                club_short_name=short_name,
                image_data=image_data,
                mime_type="image/png",
                updated_at=datetime.utcnow(),
            ).on_conflict_do_update(
                index_elements=[club_logos.c.club_short_name],
                set_={
                    "image_data": image_data,
                    "mime_type": "image/png",
                    "updated_at": datetime.utcnow(),
                }
            )
            session.execute(stmt)
            print(f"Imported {filename} as {short_name}")
    session.commit()
    print("All club logos imported.")

if __name__ == "__main__":
    main()
