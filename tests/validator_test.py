import pytest

from validator.validation import (
    Mode,
    Validator,
    ValidatorChainBuilder,
    ValidatorError,
    ValidatorResult,
    register,
    validate,
)


class MockValidator(Validator):
    def validate(self, obj):
        pass

    @register(["success", "success2"])
    def success(self, *args, **kwargs):
        return ValidatorResult.ok()

    @register(["error"])
    def error(self, *args, **kwargs):
        return ValidatorResult.error(message="error")

    @register(["exception"])
    def exception(self, *args, **kwargs):
        raise Exception  # noqa: TRY002


def test_inner_success():
    mock_validator = MockValidator()

    @validate(["success"])
    def sample_function(self):
        return "success"

    result = sample_function(mock_validator)
    assert result == "success"


def test_inner_validation_failure():
    mock_validator = MockValidator()

    @validate(["error"])
    def sample_function(self):
        return "error"

    result = sample_function(mock_validator)
    assert result is None


def test_and():
    mock_validator = MockValidator()

    @validate(["success", "error"])
    def sample_function(self):
        pass

    result = sample_function(mock_validator)
    assert result is None


def test_or():
    mock_validator = MockValidator()

    @validate(["success", "error"], mode=Mode.OR)
    def sample_function(self):
        return "success"

    result = sample_function(mock_validator)
    assert result == "success"


def test_inner_exception_handling():
    mock_validator = MockValidator()

    @validate(["exception"])
    def sample_function(self):
        pass

    with pytest.raises(ValidatorError):
        sample_function(mock_validator)


def test_validator_chain():
    assert ValidatorChainBuilder(lambda data: bool(data)).build()(5)

    # Create a chain of validators
    validator_chain = ValidatorChainBuilder(lambda data: bool(data), "valule not bool")(
        lambda data: data > 0, "value <= 0"
    )(lambda data: data < 10, "value >= 10").build()

    # Test cases
    assert validator_chain(5)  # Passes all validations
    assert not validator_chain(0)  # Fails is_not_empty and is_positive
    assert not validator_chain(15)  # Fails is_less_than_ten
    assert not validator_chain(-5)  # Fails is_positive


def mock_callback(*args, **kwargs):
    return "callback result"


def test_apply_single_rule_and_mode():
    validator = MockValidator()

    result = validator.apply(rules=["success"], callback=mock_callback)
    assert result == "callback result"


def test_apply_multiple_rules_and_mode():
    validator = MockValidator()
    result = validator.apply(rules=["success", "success2"], callback=mock_callback)
    assert result == "callback result"


def test_apply_multiple_rules_or_mode():
    validator = MockValidator()
    result = validator.apply(rules=["success", "error"], callback=mock_callback, mode=Mode.OR)
    assert result == "callback result"


def test_apply_validation_failure():
    validator = MockValidator()
    result = validator.apply(rules=["error"], callback=mock_callback)
    assert result is None
