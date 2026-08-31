"""Declarative Base for SQLAlchemy Models."""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Note: Individual models will inherit from Base.
# When Alembic runs, importing Base will have all model metadata attached.
