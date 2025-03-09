from starterkit.dto.user import User, UserError

from . import Validator, ValidatorResult, error, ok, register


class UserValidator(Validator[User]):
    """Validator for User objects with additional validator rules."""

    def validate(self, obj: User) -> ValidatorResult | None:
        """Validate a User object.

        Args:
            obj: The User object to validate.

        Returns:
            A ValidatorResult instance indicating failure or None if validator passed.
        """
        # Validator supplémentaire: vérifier que l'âge est supérieur à 18 ans
        if obj.age is None or obj.age < 18:  # noqa: PLR2004
            return error(
                rule="RXXX",
                message="Erreur de validator: l'utilisateur doit avoir au moins 18 ans.",
            )

        return ok(rule="RXXX")

    @register(["R001", "R003"])
    def check_email(self, user: User, *args, **kwargs) -> ValidatorResult | None:  # noqa: ANN002, ANN003, ARG002
        """Check the email of the user for specific validator rules.

        Args:
            user: The User object to check.

        Raises:
            UserError: If the user's name is invalid.
        """
        if user.name == "TOTO":
            msg = f"name is invalide: {user.name}"
            raise UserError(msg)
        return None

    @register(["R002"])
    def check_email_r002(self, user: User, *args, **kwargs) -> ValidatorResult | None:  # noqa: ANN002, ANN003, ARG002
        """Check the email of the user for specific validator rules.

        Args:
            user: The User object to check.

        Raises:
            UserError: If the user's name is invalid.
        """
        if user.name == "XXX":
            msg = f"name is invalide R002: {user.name}"
            return error(msg, rule="R002")
        return None
