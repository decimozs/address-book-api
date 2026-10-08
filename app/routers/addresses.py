"""Address endpoints."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app import crud
from app.dependencies import DbSession
from app.models import Address
from app.schemas import AddressCreate, AddressNearby, AddressRead, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


def get_address_or_404(address_id: int, db: DbSession) -> Address:
    address = crud.get_address(db, address_id)
    if address is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Address not found")
    return address


ExistingAddress = Annotated[Address, Depends(get_address_or_404)]

NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"description": "Address not found"}
}


@router.post(
    "",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an address",
)
def create_address(data: AddressCreate, db: DbSession) -> Address:
    """Validate and store a new address, including its coordinates."""
    return crud.create_address(db, data)


# Declared before "/{address_id}" so "nearby" is not parsed as an id.
@router.get(
    "/nearby",
    response_model=list[AddressNearby],
    summary="Find addresses within a distance",
)
def get_nearby_addresses(
    db: DbSession,
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    distance_km: Annotated[float, Query(gt=0, le=20040, description="Search radius in km")],
) -> list[AddressNearby]:
    """Return addresses within `distance_km` of the given coordinates.

    Results are sorted nearest first and include the computed `distance_km`
    (great-circle distance in kilometres).
    """
    return [
        AddressNearby(
            **AddressRead.model_validate(address).model_dump(),
            distance_km=round(distance, 3),
        )
        for address, distance in crud.find_nearby(db, latitude, longitude, distance_km)
    ]


@router.get("", response_model=list[AddressRead], summary="List addresses")
def list_addresses(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Address]:
    """List stored addresses ordered by id, with `skip`/`limit` pagination."""
    return crud.list_addresses(db, skip, limit)


@router.get(
    "/{address_id}",
    response_model=AddressRead,
    responses=NOT_FOUND,
    summary="Get an address",
)
def read_address(address: ExistingAddress) -> Address:
    """Return a single address by id."""
    return address


@router.patch(
    "/{address_id}",
    response_model=AddressRead,
    responses=NOT_FOUND,
    summary="Update an address",
)
def update_address(
    data: AddressUpdate, address: ExistingAddress, db: DbSession
) -> Address:
    """Partially update an address; only the supplied fields change."""
    return crud.update_address(db, address, data)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Delete an address",
)
def delete_address(address: ExistingAddress, db: DbSession) -> Response:
    """Permanently delete an address."""
    crud.delete_address(db, address)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
