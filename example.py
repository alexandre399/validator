from collections.abc import Iterator
from pathlib import Path

import ijson
from dependency_injector import containers, providers
from pydantic import ValidationError

from validator.dto.user import User
from validator.service.user import UserService
from validator.validation.user import UserValidator
from validator.validation import validate, ValidatorChain


# Définir la classe de conteneur pour IoC
# https://python-dependency-injector.ets-labs.org/
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    user_validator = providers.Factory(UserValidator)  # , schema=json_schema)
    user_service = providers.Singleton(UserService, validator=user_validator)
    user_factory = providers.Factory(User)


# Créer une instance du conteneur
container = Container()
user_service = container.user_service()


# Fonction pour lire le fichier JSON par morceaux (lazy loading)
def lazy_load_users(file_path: str) -> Iterator[User]:
    with Path(file_path).open() as file:
        users = ijson.items(file, "item")
        for user_dict in users:
            try:
                user = container.user_factory(**user_dict)
                yield user
            except ValidationError:
                pass


file_path = str(Path(__file__).parent / "tests/assets/users.json")

for user in lazy_load_users(file_path=file_path):
    try:
        user_service.append(user,"args", kwargs="kwargs")
    except Exception as err:
        print(err)


user = User(id=5, name="TOTO", email="test@example.com", age="19")

try:
    user_service.validator.validate(user)
except Exception as err:
    print(err)

print(user_service.bidon(User(id=5, name="XXX", email="test@example.com", age="19")))

try:
    user_service.validator.rules["R001"][0](user_service, user)
except Exception as err:
    print(err)

try:
    validate(rules=["R002"])(UserService.append)(user_service, user)
except Exception as err:
    print(err)


validator_chain = ValidatorChain(lambda data: bool(data))(lambda data: data > 0)(
        lambda data: data < 10, "error: value>10")

print(validator_chain.validate(15))
