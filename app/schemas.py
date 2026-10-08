"""Pydantic schemas: request validation and response serialisation."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, examples=["Head Office"])
    street: str = Field(min_length=1, max_length=200, examples=["1 Infinite Loop"])
    city: str = Field(min_length=1, max_length=100, examples=["Cupertino"])
    state: str | None = Field(default=None, max_length=100, examples=["CA"])
    postal_code: str | None = Field(default=None, max_length=20, examples=["95014"])
    country: str = Field(min_length=1, max_length=100, examples=["USA"])
    latitude: float = Field(ge=-90, le=90, examples=[37.33182])
    longitude: float = Field(ge=-180, le=180, examples=[-122.03118])

    @field_validator("name", "street", "city", "country")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Reject whitespace-only strings and trim the rest."""
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    """Partial update: only the supplied fields are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    street: str | None = Field(default=None, min_length=1, max_length=200)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("name", "street", "city", "country")
    @classmethod
    def not_blank(cls, value: str | None) -> str | None:
        """Same trimming/blank rule as on create, applied only when supplied."""
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class AddressRead(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class AddressNearby(AddressRead):
    distance_km: float
