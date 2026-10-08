"""Domain exceptions raised by the data layer."""


class DuplicateAddressError(Exception):
    """An address with the same name, street, city and country already exists."""
