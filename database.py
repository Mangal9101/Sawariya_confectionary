import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

if os.environ.get("RENDER"):
    DATABASE_URL = "sqlite:////data/sawariya.db"
else:
    DATABASE_URL = "sqlite:///./sawariya.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()