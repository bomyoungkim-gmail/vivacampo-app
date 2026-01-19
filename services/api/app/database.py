from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from app.config import settings

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.env == "local"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
