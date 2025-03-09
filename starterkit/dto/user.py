from pydantic import BaseModel, field_validator


class UserError(Exception):
    """Exception raised for errors in the user input.

    Attributes:
        message: explanation of the error
    """


class User(BaseModel):
    """Schema for User with custom validator.

    Attributes:
        id: The unique identifier for the user.
        name: The name of the user.
        email: The email address of the user.
        age: The age of the user (optional).
        address: The address of the user (optional).
    """

    id: int
    name: str
    email: str
    age: int | None = None
    address: str | None = None
    # state: ObservableProperty = Field(default_factory=ObservableProperty, init=False)

    @field_validator("email")
    def validate_email(cls, v: str) -> str:  # noqa: N805
        """Validate the email to ensure it ends with @example.com.

        Args:
            v: The email address to validate.

        Raises:
            UserError: If the email does not end with @example.com.

        Returns:
            The validated email address.
        """
        if not v.endswith("@example.com"):
            msg = "L'adresse email doit se terminer par @example.com"
            raise UserError(msg)
        return v

    class Config:
        """Pydantic configuration for the User model.

        Attributes:
            extra: Allows extra fields in the input data.
            validate_assignment: Validates data when assigning to attributes.
        """

        extra = "allow"
        validate_assignment = True
