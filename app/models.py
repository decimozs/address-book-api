"""ORM models."""
from sqlalchemy import Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    street: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    # Speeds up the bounding-box pre-filter used by the nearby search.
    __table_args__ = (
        Index("ix_addresses_lat_lon", "latitude", "longitude"),
        # Prevents the same address being stored twice.
        UniqueConstraint("name", "street", "city", "country", name="uq_address_identity"),
    )
