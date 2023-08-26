from typing import Iterator
from sqlalchemy.orm.session import Session
import uuid
from opsml.registry.sql.settings import settings
from opsml.registry.cards import ArtifactCard
from opsml.registry.sql.query_helpers import QueryEngine
from opsml.helpers.request_helpers import api_routes


class ApiMixin:
    @property
    def _session(self):
        return settings.request_client


class CardValidator:
    """Helper class for validating cards before registering them in the registry"""

    def _is_correct_card_type(
        self,
        table_name: str,
        card: ArtifactCard,
    ) -> bool:
        """Checks wether the current card is associated with the correct registry type"""
        supported_card = f"{table_name.split('_')[1]}Card"
        return supported_card.lower() == card.__class__.__name__.lower()

    def check_uid_exists(self, uid: str, table_to_check: str) -> bool:
        raise NotImplementedError

    def validate_card_type(
        self,
        table_name: str,
        card: ArtifactCard,
    ):
        if not self._is_correct_card_type(table_name=table_name, card=card):
            raise ValueError(f"""Card of type {card.__class__.__name__} is not supported by {table_name} registry""")

        if self.check_uid_exists(uid=str(card.uid), table_to_check=table_name):
            raise ValueError(
                """This Card has already been registered.
                If the card has been modified try updating the Card in the registry.
                If registering a new Card, create a new Card of the correct type.
                """
            )

    def set_card_uid(self, card: ArtifactCard) -> None:
        """Sets a given card's uid

        Args:
            card:
                Card to set
        """
        if card.uid is None:
            card.uid = uuid.uuid4().hex


class CardValidatorServer(CardValidator):
    """Card validator for server side validation"""
create a sql mixin
    def __init__(self):
        self.query_engine = QueryEngine()

    def session(self) -> Iterator[Session]:
        return self.query_engine.session()

    def check_uid_exists(self, uid: str, table_to_check: str) -> bool:
        query = self.query_engine.uid_exists_query(
            uid=uid,
            table_to_check=table_to_check,
        )

        with self.session() as sess:
            result = sess.scalars(query).first()  # type: ignore[attr-defined]
        return bool(result)


class CardValidatorClient(ApiMixin, CardValidator):
    """Card validator for client side validation"""

    def check_uid_exists(self, uid: str, table_to_check: str) -> bool:
        data = self._session.post_request(
            route=api_routes.CHECK_UID,
            json={"uid": uid, "table_name": table_to_check},
        )

        return bool(data.get("uid_exists"))


# mypy not happy with dynamic classes
def get_card_validator():
    if settings.request_client is not None:
        return CardValidatorClient()
    return CardValidatorServer()


card_validator = get_card_validator()
