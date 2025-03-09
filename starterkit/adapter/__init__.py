"""
Module `adapter`

This module defines the base classes for adapters, including adapter-specific exceptions.

Classes:
    AdapterError: Base exception for adapter errors.
    AdapterNotFoundError: Exception raised when an adapter is not found.
    Adapter: Abstract class for adapters.

Typings:
    R: Generic type for adapters.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

R = TypeVar("R")


class AdapterError(Exception):
    """Base exception for adapter errors."""


class AdapterNotFoundError(AdapterError):
    """
    Exception raised when an adapter is not found.

    Attributes:
        adapter (type): The type of the adapter that was not found.
    """

    def __init__(self, adapter: type) -> None:
        super().__init__(f"Adapter not found for {adapter}")


class Adapter(ABC):
    """
    Abstract class for adapters.

    Methods:
        adapt(adapter: type[R]) -> R | None: Abstract method to adapt a given type.
    """

    @abstractmethod
    def adapt(self, adapter: type[R]) -> R | None:
        pass


def adapt(obj, adapter: type[R]) -> R | None:  # noqa: ANN001
    """
    Adapt an object to the specified adapter type.

    Args:
        obj: The object to be adapted.
        adapter (type[R]): The type of the adapter to adapt to.

    Returns:
        R | None: The adapted object if successful, otherwise None.
    """
    if isinstance(obj, adapter):
        return obj
    if isinstance(obj, Adapter):
        return obj.adapt(adapter=adapter)  # type:ignore[type-abstract]

    return None
