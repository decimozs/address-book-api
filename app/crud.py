"""Database operations, kept separate from HTTP concerns."""
import logging

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import DuplicateAddressError
from app.geo import bounding_box, haversine_km
from app.models import Address
from app.schemas import AddressCreate, AddressUpdate

logger = logging.getLogger(__name__)


def _commit(db: Session) -> None:
    """Commit, translating a unique-constraint violation into a domain error."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAddressError("Address already exists") from exc


def create_address(db: Session, data: AddressCreate) -> Address:
    address = Address(**data.model_dump())
    db.add(address)
    _commit(db)
    logger.info("Created address id=%s", address.id)
    return address


def get_address(db: Session, address_id: int) -> Address | None:
    return db.get(Address, address_id)


def list_addresses(db: Session, skip: int = 0, limit: int = 100) -> tuple[list[Address], int]:
    """Return one page of addresses and the total number stored."""
    stmt = select(Address).order_by(Address.id).offset(skip).limit(limit)
    total = db.scalar(select(func.count()).select_from(Address)) or 0
    return list(db.scalars(stmt)), total


def update_address(db: Session, address: Address, data: AddressUpdate) -> Address:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(address, field, value)
    _commit(db)
    logger.info("Updated address id=%s fields=%s", address.id, sorted(changes))
    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()
    logger.info("Deleted address id=%s", address.id)


def find_nearby(
    db: Session, latitude: float, longitude: float, distance_km: float
) -> list[tuple[Address, float]]:
    """Addresses within distance_km of the point, nearest first.

    A bounding box narrows candidates in SQL; haversine then gives the exact
    distance and trims the box corners.
    """
    min_lat, max_lat, min_lon, max_lon = bounding_box(latitude, longitude, distance_km)
    stmt = select(Address).where(
        Address.latitude.between(min_lat, max_lat),
        Address.longitude.between(min_lon, max_lon),
    )
    results = []
    for address in db.scalars(stmt):
        distance = haversine_km(latitude, longitude, address.latitude, address.longitude)
        if distance <= distance_km:
            results.append((address, distance))
    results.sort(key=lambda pair: pair[1])
    logger.info(
        "Nearby search lat=%s lon=%s radius_km=%s found=%d",
        latitude, longitude, distance_km, len(results),
    )
    return results
