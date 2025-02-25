from abc import ABC
from typing import Generic, TypeVar

from validator.adapter import Adapter
from validator.validation import Validator

T = TypeVar("T")
R = TypeVar("R")


class Service(Adapter, ABC, Generic[T]):
    """Abstract base class for services.

    Attributes:
        T: The type of objects the service works with.
    """

    def __init__(self, validator: Validator[T]) -> None:
        """Initialize the service with a validator.

        Args:
            validator: The validator instance for validating objects of type T.
        """
        self._validator = validator

    @property
    def validator(self) -> Validator[T]:
        """Get the validator instance.

        Returns:
            The validator instance for validating objects of type T.
        """
        return self._validator

    def adapt(self, adapter: type[R]) -> R | None:
        if adapter is Validator:
            return self.validator  # type: ignore[return-value]
        return None
