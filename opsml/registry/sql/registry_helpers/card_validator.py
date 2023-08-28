import uuid
from typing import Type
from opsml.registry.cards import ArtifactCard
from opsml.registry.sql.registry_helpers.mixins import ClientMixin, ServerMixin
from opsml.registry.sql.sql_schema import REGISTRY_TABLES


class CardValidator:
    """Helper class for validating cards before registering them in the registry"""

    def _is_correct_card_type(
        self,
        table: Type[REGISTRY_TABLES],
        card: ArtifactCard,
    ) -> bool:
        """Checks wether the current card is associated with the correct registry type"""
        supported_card = f"{table.__tablename__.split('_')[1]}Card"
        return supported_card.lower() == card.__class__.__name__.lower()

    def check_uid_exists(self, uid: str, table: Type[REGISTRY_TABLES]) -> bool:
        raise NotImplementedError

    def validate_card_type(
        self,
        table: Type[REGISTRY_TABLES],
        card: ArtifactCard,
    ):
        if not self._is_correct_card_type(table=table, card=card):
            raise ValueError(
                f"""Card of type {card.__class__.__name__} is not supported by {table.__tablename__} registry"""
            )

        if self.check_uid_exists(uid=str(card.uid), table=table):
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


class CardValidatorServer(ServerMixin, CardValidator):
    """Card validator for server side validation"""

    def check_uid_exists(self, uid: str, table: Type[REGISTRY_TABLES]) -> bool:
        query = self.query_engine.uid_exists_query(uid=uid, table=table)

        with self.session() as sess:
            result = sess.scalars(query).first()  # type: ignore[attr-defined]
        return bool(result)


class CardValidatorClient(ClientMixin, CardValidator):
    """Card validator for client side validation"""

    def check_uid_exists(self, uid: str, table: Type[REGISTRY_TABLES]) -> bool:
        data = self._session.post_request(
            route=self.routes.CHECK_UID,
            json={"uid": uid, "table_name": table.__tablename__},
        )

        return bool(data.get("uid_exists"))
