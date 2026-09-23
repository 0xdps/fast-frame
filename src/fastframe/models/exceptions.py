class DoesNotExist(LookupError):
    pass


class MultipleObjectsReturned(LookupError):
    pass


class ValidationError(ValueError):
    """Raised when model/field validation fails.

    Optionally carries a structured ``errors`` dict mapping field names to
    error messages, so APIs can return per-field 422 responses::

        raise ValidationError("Validation failed", errors={"email": "Invalid"})

    ``str(exc)`` still returns a readable message, so existing callers that
    do ``except ValidationError as e: ... str(e)`` keep working.
    """

    def __init__(self, message: str = "Validation failed", *, errors: dict | None = None) -> None:
        self.errors: dict = errors or {}
        if self.errors and message == "Validation failed":
            message = str(self.errors)
        super().__init__(message)
