"""Address endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models import Address
from app.schemas import AddressCreate, AddressNearby, AddressRead, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])

DbSession = Annotated[Session, Depends(get_db)]


def get_address_or_404(address_id: int, db: DbSession) -> Address:
    address = crud.get_address(db, address_id)
    if address is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
    return address


ExistingAddress = Annotated[Address, Depends(get_address_or_404)]


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(data: AddressCreate, db: DbSession):
    return crud.create_address(db, data)


# Declared before "/{address_id}" so "nearby" is not parsed as an id.
@router.get("/nearby", response_model=list[AddressNearby])
def get_nearby_addresses(
    db: DbSession,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    distance_km: Annotated[float, Query(gt=0, le=20040, description="Search radius in km")],
):
    return [
        AddressNearby(
            **AddressRead.model_validate(address).model_dump(),
            distance_km=round(distance, 3),
        )
        for address, distance in crud.find_nearby(db, latitude, longitude, distance_km)
    ]


@router.get("", response_model=list[AddressRead])
def list_addresses(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    return crud.list_addresses(db, skip, limit)


@router.get("/{address_id}", response_model=AddressRead)
def read_address(address: ExistingAddress):
    return address


@router.patch("/{address_id}", response_model=AddressRead)
def update_address(data: AddressUpdate, address: ExistingAddress, db: DbSession):
    return crud.update_address(db, address, data)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address: ExistingAddress, db: DbSession):
    crud.delete_address(db, address)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
