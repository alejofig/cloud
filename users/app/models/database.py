from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DB_USER=os.getenv("DB_USER","example")
DB_PASSWORD= os.getenv("DB_PASSWORD","example")
DB_HOST=os.getenv("DB_HOST","localhost")
DB_PORT=os.getenv("DB_PORT",5434)
DB_NAME=os.getenv("DB_NAME","example")

# DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# DATABASE_URL="postgresql://example:example@db/example"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
async def init_db():
    try:

        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise e