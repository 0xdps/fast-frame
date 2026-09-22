class DoesNotExist(LookupError):
    pass


class MultipleObjectsReturned(LookupError):
    pass


class ValidationError(ValueError):
    """Raised when model/field validation fails."""

    pass
