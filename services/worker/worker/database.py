from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from worker.config import settings

# Create engine
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
