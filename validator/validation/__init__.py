import functools
import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
from types import MappingProxyType
from typing import Any, ClassVar, Generic, TypeVar

from validator import logger
from validator.adapter import Adapter, AdapterNotFoundError, adapt

T = TypeVar("T")
R = TypeVar("R")


class Mode(Enum):
    AND = 1
    OR = 2


@dataclass(frozen=True)
class ValidatorResult(ABC):
    """Immutable class for validation results.

    Attributes:
        rule: The rule that was validated.
        level: The level of the validation.
        message: An optional message for validation level.
        stacktrace: An optional stack trace for the validation.
        kwargs: Additional keyword arguments.
    """

    @total_ordering
    class Level(Enum):
        """Enumeration class to represent different levels with a defined total order."""

        OK = 1
        WARNING = 2
        ERROR = 4

        def __eq__(self, other: object) -> bool:
            """Checks if two enumeration instances are equal by comparing their values.

            Args:
                other (Any): The other enumeration instance to compare.

            Returns:
                bool: True if the values are equal, otherwise False.
            """
            if isinstance(other, ValidatorResult.Level):
                return self.value == other.value
            return NotImplemented

        def __lt__(self, other: object) -> bool:
            """Checks if the current instance is less than another instance by comparing their
            values.

            Args:
                other (Any): The other enumeration instance to compare.

            Returns:
                bool: True if the current value is less, otherwise False.
            """
            if isinstance(other, ValidatorResult.Level):
                return self.value < other.value
            return NotImplemented

    level: Level
    message: str | None = field(default=None)
    stacktrace: traceback.StackSummary | None = field(default=None, repr=False)
    kwargs: dict[str, Any] = field(default_factory=dict, kw_only=True)

    def __new__(cls, *args: list, **kwargs: dict) -> "ValidatorResult":  # noqa:ARG003
        """Ensure ValidationResult cannot be instantiated directly.

        Args:
            cls: The class itself.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Raises:
            TypeError: If an attempt is made to instantiate ValidationResult directly.
        """
        if cls is ValidatorResult:
            msg = f"Cannot instantiate abstract class {cls.__name__} directly"
            raise TypeError(msg)
        return super().__new__(cls)

    def __bool__(self) -> bool:
        """Check if the ValidationResult instance is valid.

        Returns:
            bool: True if the ValidationResult instance is valid, False otherwise.
        """
        return self.level < ValidatorResult.Level.ERROR

    @classmethod
    def ok(cls, **kwargs: object) -> "ValidatorResult":
        """Create a successful validation result.

        Args:
            kwargs: Additional keyword arguments.

        Returns:
            A ValidationResult instance indicating success.
        """
        return type("", (cls,), {})(level=ValidatorResult.Level.OK, kwargs=kwargs)

    @classmethod
    def warning(cls, message: str | None = None, **kwargs: object) -> "ValidatorResult":
        """Create a warning validation result.

        Args:
            message: The warning message.
            kwargs: Additional keyword arguments.

        Returns:
            A ValidationResult instance indicating failure.
        """
        validation_result = type("", (cls,), {})(
            level=ValidatorResult.Level.WARNING, message=message, kwargs=kwargs
        )
        object.__setattr__(validation_result, "stacktrace", traceback.extract_stack())
        return validation_result

    @classmethod
    def error(cls, message: str, **kwargs: object) -> "ValidatorResult":
        """Create a failed validation result.

        Args:
            message: The failure message.
            kwargs: Additional keyword arguments.

        Returns:
            A ValidationResult instance indicating failure.
        """
        validation_result = type("", (cls,), {})(
            level=ValidatorResult.Level.ERROR, message=message, kwargs=kwargs
        )
        object.__setattr__(validation_result, "stacktrace", traceback.extract_stack())
        return validation_result


ok = ValidatorResult.ok
warning = ValidatorResult.warning
error = ValidatorResult.error


@dataclass(frozen=True)
class ValidatorError(Exception):
    """Exception raised for validation errors.

    Attributes:
        rule: The rule that failed.
        func: The function where the validation failed.
    """

    rule: str
    func: Callable


class ValidatorMeta(type):
    """Metaclass for validators to collect rules."""

    def __init__(cls, name: str, bases: tuple[type, ...], dct: dict[str, Any]) -> None:
        """Initialize the ValidatorMeta class.

        Args:
            cls: The class itself.
            name: The name of the class.
            bases: A tuple of base classes.
            dct: A dictionary of class attributes.
        """
        super().__init__(name, bases, dct)
        rules = defaultdict(list)
        for value in [v for v in dct.values() if callable(v)]:
            for rule in vars(value).pop("rules", []):
                rules[rule].append(value)
        cls._rules = MappingProxyType({k: tuple(v) for k, v in rules.items()})


class MetaAB(ABC, ValidatorMeta):
    """Combined metaclass for abstract base classes and validators."""


class Validator(Generic[T], metaclass=MetaAB):
    """Abstract base class for validators.

    Attributes:
        T: The type of objects to validate.
    """

    _rules: ClassVar[dict[str, list[Callable[..., ValidatorResult | None]]]]

    @abstractmethod
    def validate(self, obj: T) -> ValidatorResult | None:
        """Validate an object.

        Args:
            obj: The object to validate.

        Returns:
            A ValidationResult instance or None if validation passed.
        """

    def accept(
        self, rules: list[str] | None, mode: Mode = Mode.AND, *args: list, **kwargs: dict
    ) -> bool:
        """Accept and apply validation rules.

        Args:
            rules: A list of rule names to apply. If None, all rules are applied.
            mode: The mode to apply the rules (AND/OR).
            *args: Positional arguments to pass to the validation functions.
            **kwargs: Keyword arguments to pass to the validation functions.

        Returns:
            bool: True if validation passes, False otherwise.

        Raises:
            ValidatorError: If an exception occurs during validation.
        """
        selected: dict[str, list[Callable[..., ValidatorResult | None]]] = (
            self.rules
            if rules is None
            else {key: value for key, value in self.rules.items() if key in rules}
        )
        try:
            for _rule, func in [
                (rule, func) for rule, functions in selected.items() for func in functions
            ]:
                result = func(self, *args, **kwargs)
                if result is None:
                    result = ValidatorResult.ok(rule=_rule)
                if result.level >= ValidatorResult.Level.ERROR:
                    logger.error(result)
                    if mode is Mode.AND:
                        return False
                if result.level > ValidatorResult.Level.OK:
                    logger.warning(result)
                if mode == mode.OR and result:
                    break
        except Exception as err:
            raise ValidatorError(_rule, func) from err
        else:
            return True

    def apply(
        self,
        rules: list[str],
        callback: Callable[..., R],
        mode: Mode = Mode.AND,
        *args: list,
        **kwargs: dict,
    ) -> R | None:
        """Apply a validation rule.

        Args:
            rules: The validation rules to apply.
            callback: The validation rule to apply.
            mode: The mode to apply the rules.
            *args: Positional arguments to pass to the rule
            **kwargs: Keyword arguments to pass to the rule

        Returns:
            The result of the callback function or None if validation failed.
        """
        return validate(rules=rules, mode=mode)(callback)(self, *args, **kwargs)

    @property
    def rules(self) -> dict:
        return self.__class__._rules


def register(rules: list[str]) -> Callable:
    """Decorator to register validation rules.

    Args:
        rules: List of validation rules.

    Returns:
        A decorator to register the function as a validation rule.
    """

    def decorateur(func: Callable) -> Callable:
        func.rules = rules  # type:ignore[attr-defined]
        return func

    return decorateur


def validate(rules: list[str] | None = None, mode: Mode = Mode.AND) -> Callable:
    """Decorator to apply validation rules.

    Args:
        rules: List of validation rules.
        validator: Function to get the validator instance.

    Returns:
        A decorator to apply the validation rules.
    """

    def decorateur(function: Callable) -> Callable:
        @functools.wraps(function)
        def inner(self: Validator | Adapter, *args: list, **kwargs: dict) -> object | None:
            """Inner function to apply the validation rules.

            Args:
                *args: Positional arguments.
                **kwargs: Keyword arguments.

            Returns:
                The result of the decorated function or None if validation failed.
            """
            validator = adapt(obj=self, adapter=Validator)  # type:ignore[type-abstract]
            if not validator:
                raise AdapterNotFoundError(adapter=Validator)

            if validator.accept(rules, mode, *args, data=self, **kwargs):  # type:ignore[arg-type]
                return function(self, *args, **kwargs)
            return None

        return inner

    return decorateur


class ValidatorChain(ABC):
    """Abstract base class for creating a chain of validators.

    Attributes:
        _parent: The parent validator in the chain.
        _callback: The callback function to perform validation.
    """

    _parent: "ValidatorChain"
    _callback: Callable[..., bool]
    _message: str | None

    def __init__(self, callback: Callable[..., bool], message: str | None = None) -> None:
        """Initialize the ValidatorChain with a callback function.

        Args:
            callback: The callback function to perform validation.
            message: The message to display if validation fails.
        """
        self._callback = callback
        self._message = message

    def __call__(
        self, callback: Callable[..., bool], message: str | None = None
    ) -> "ValidatorChain":
        """Add a new validator to the chain.

        Args:
            callback: The callback function for the new validator.

        Returns:
            A new ValidatorChain instance with the provided callback.
        """
        return _InnerValidatorChain(parent=self, callback=callback, message=message)

    def validate(self, *args: list) -> ValidatorResult:  # noqa: ARG002
        """Validate the data using the chain of validators.

        Args:
            *args: The arguments to pass to the callback functions.

        Returns:
            bool: True if all validations pass, otherwise False.
        """
        return ok()


class _InnerValidatorChain(ValidatorChain):
    """Inner class to represent a validator chain."""

    def __init__(
        self, parent: "ValidatorChain", callback: Callable[..., bool], message: str | None = None
    ) -> None:
        super().__init__(callback=callback, message=message)
        self._parent = parent

    def validate(self, *args: list) -> ValidatorResult:
        """Validate the data using the chain of validators.

        Args:
            *args: The arguments to pass to the callback functions.

        Returns:
            bool: True if all validations pass, otherwise False.
        """
        result = self._parent.validate(*args)
        if result:
            result = ok() if self._callback(*args) else error(message=self._message or "")
        return result
