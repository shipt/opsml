from typing import Dict, Any, Tuple, cast, Type
from opsml.registry.sql.query_helpers import log_card_change  # type: ignore
from opsml.registry.cards.card_saver import save_card_artifacts
from opsml.registry.cards import ArtifactCard
from opsml.registry.sql.registry_helpers.mixins import ClientMixin, ServerMixin
from opsml.registry.sql.sql_schema import REGISTRY_TABLES
from opsml.registry.storage.storage_system import StorageClientType


class CardRegistryHelper:
    def _add_and_commit(self, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        raise NotImplementedError

    def update_card_record(self, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        raise NotImplementedError

    def _create_registry_record(
        self,
        card: ArtifactCard,
        storage_client: StorageClientType,
    ) -> None:
        """
        Creates a registry record from a given ArtifactCard.
        Saves artifacts prior to creating record

        Args:
            card:
                Card to create a registry record from
        """

        card = save_card_artifacts(card=card, storage_client=storage_client)
        record = card.create_registry_record()

        self._add_and_commit(card=record.model_dump())


class CardRegistryHelperServer(ServerMixin, CardRegistryHelper):
    @log_card_change
    def _add_and_commit(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        sql_record = table(**card)

        with self.session() as sess:
            sess.add(sql_record)
            sess.commit()

        return card, "registered"

    @log_card_change
    def update_card_record(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        record_uid = cast(str, card.get("uid"))

        with self.session() as sess:
            query = sess.query(table).filter(table.uid == record_uid)
            query.update(card)
            sess.commit()

        return card, "updated"


class CardRegistryHelperClient(ClientMixin, CardRegistryHelper):
    @log_card_change
    def _add_and_commit(self, table_name: str, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=self.routes.CREATE_CARD,
            json={
                "card": card,
                "table_name": table_name,
            },
        )

        if bool(data.get("registered")):
            return card, "registered"
        raise ValueError("Failed to register card")

    @log_card_change
    def update_card_record(self, table_name: str, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=self.routes.UPDATE_CARD,
            json={
                "card": card,
                "table_name": table_name,
            },
        )

        if bool(data.get("updated")):
            return card, "updated"
        raise ValueError("Failed to update card")
