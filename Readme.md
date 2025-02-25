# Validator Library

This library provides a flexible and extensible framework for validating objects using various rules and validators. It leverages several design patterns to ensure maintainability, scalability, and ease of use.

## Design Patterns Used

1. **Abstract Base Class (ABC) Pattern**:
    - Used to define abstract base classes for validators (`Validator`, `ValidatorChain`) and services (`Service`).
    - Ensures that concrete implementations provide specific methods, promoting a consistent interface.

2. **Decorator Pattern**:
    - Used to apply validation rules to functions and methods (`register`, `validate`).
    - Allows for dynamic addition of behavior to functions without modifying their code.

3. **Factory Method Pattern**:
    - Used in the `ValidatorResult` class to create different types of validation results (`ok`, `warning`, `error`).
    - Provides a way to instantiate objects based on specific conditions.

4. **Chain of Responsibility Pattern**:
    - Implemented in the `ValidatorChain` class to create a chain of validators.
    - Allows multiple validators to process a request in sequence, promoting separation of concerns.

5. **Adapter Pattern**:
    - Used to adapt objects to the `Validator` interface (`adapt` function, `Adapter` class).
    - Enables integration of different types of objects into the validation framework.

6. **Singleton Pattern**:
    - Used in the `ValidatorMeta` metaclass to ensure a single instance of validation rules is maintained.
    - Promotes efficient management of shared resources.

## Advantages of the Code

1. **Extensibility**:
    - The use of abstract base classes and decorators allows for easy extension of the validation framework.
    - New validators and validation rules can be added without modifying existing code.

2. **Reusability**:
    - The framework promotes reusability of validation logic through the use of decorators and the chain of responsibility pattern.
    - Common validation rules can be defined once and reused across different validators.

3. **Maintainability**:
    - The clear separation of concerns and use of design patterns make the codebase easier to maintain.
    - Each component has a well-defined responsibility, reducing the risk of introducing bugs when making changes.

4. **Scalability**:
    - The framework can handle complex validation scenarios by chaining multiple validators and applying different rules dynamically.
    - The use of metaclasses and mapping proxies ensures efficient management of validation rules.

5. **Flexibility**:
    - The decorator pattern allows for flexible application of validation rules to functions and methods.
    - The adapter pattern enables integration with various types of objects, making the framework adaptable to different use cases.

## Installation

To install the Validator Library, you can use pip:

```sh
pip install validator
```

## Getting Started

To use this library, you need to define your own validators by extending the `Validator` class and implementing the `validate` method. You can then register validation rules using the `register` decorator and apply them using the `validate` decorator.

```python
from validator.validation import Validator, ValidatorResult, register, validate

class MyValidator(Validator[MyObject]):
    @register(["rule1"])
    def rule1(self, obj: MyObject) -> ValidatorResult:
        # Implement your validation logic here
        return ValidatorResult.ok()

    def validate(self, obj: MyObject) -> ValidatorResult:
        # Implement your validation logic here
        return self.rule1(obj)

@validate(rules=["rule1"])
def my_function(obj: MyObject) -> None:
    # Function logic here
    pass
```

## Additional Examples

### Example 1: Using ValidatorChain

```python
from validator.validation import ValidatorChain, ValidatorResult

class MyValidatorChain(ValidatorChain):
    def validate(self, obj: MyObject) -> ValidatorResult:
        result = super().validate(obj)
        if result:
            # Additional validation logic
            pass
        return result

chain = MyValidatorChain(callback=lambda obj: obj.is_valid())
result = chain.validate(my_object)
```

### Example 2: Adapting Objects

```python
from validator.adapter import Adapter, adapt

class MyAdapter(Adapter):
    def adapt(self, adapter: type) -> object | None:
        if adapter is MyValidator:
            return MyValidator()
        return None

my_adapter = MyAdapter()
validator = adapt(my_adapter, MyValidator)
if validator:
    result = validator.validate(my_object)
```

## License

This project is licensed under the MIT License.