from validator.dto.user import User
from validator.validation import validate

from . import Service


class UserService(Service[User]):
    """Service class for User operations.

    Attributes:
        _validator: The validator instance for validating User objects.
    """

    @validate(["R002"])
    def bidon(self, user: User) -> None:
        """Additional validation rules for adding a User.

        Args:
            user: The User object to validate.
        """

    @validate()
    def append(self, user: User) -> None:
        """Additional validation rules for adding a User.

        Args:
            user: The User object to validate.
        """
