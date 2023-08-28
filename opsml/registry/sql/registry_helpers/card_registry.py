#### Helper class that builds a server or client instance


from typing import Dict, Any, Tuple, cast, Type, Optional, List
from opsml.helpers.utils import clean_string
from opsml.registry.sql.settings import settings
from opsml.registry.sql.registry_helpers.semver import SemVerSymbols, SemVerUtils
from opsml.registry.sql.query_helpers import log_card_change  # type: ignore
from opsml.registry.cards.card_saver import save_card_artifacts
from opsml.registry.sql.registry_helpers.card_storage import CardStorageClient
from opsml.registry.cards import ArtifactCard
from opsml.registry.sql.registry_helpers.mixins import ClientMixin, ServerMixin
from opsml.registry.sql.sql_schema import REGISTRY_TABLES, RegistryTableNames
from opsml.registry.storage.storage_system import StorageClientType


USE_CLIENT_CLASS = bool(settings.request_client)


# Set up client and server classes
if USE_CLIENT_CLASS:
    from opsml.registry.sql.registry_helpers.card_validator import CardValidatorClient as CardValidator
    from opsml.registry.sql.registry_helpers.card_version import CardVersionSetterClient as CardVersionSetter

else:
    from opsml.registry.sql.registry_helpers.card_validator import CardValidatorServer as CardValidator
    from opsml.registry.sql.registry_helpers.card_version import CardVersionSetterServer as CardVersionSetter
    from opsml.registry.sql.db_initializer import DBInitializer

    initializer = DBInitializer(
        engine=settings.connection_client.get_engine(),
        registry_tables=list(RegistryTableNames),
    )
    initializer.initialize()


card_validator = CardValidator()
card_version = CardVersionSetter()
card_storage = CardStorageClient()


class CardRegistryHelper:
    def __init__(self):
        self.validator = card_validator
        self.card_ver = card_version
        self.storage = card_storage

    def list_cards(
        self,
        table: Type[REGISTRY_TABLES],
        uid: Optional[str] = None,
        name: Optional[str] = None,
        team: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        max_date: Optional[str] = None,
        limit: Optional[int] = None,
        ignore_release_candidates: bool = False,
    ) -> List[Dict[str, str]]:
        raise NotImplementedError

    def _add_and_commit(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        raise NotImplementedError

    def update_card_record(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        raise NotImplementedError

    def create_registry_record(
        self,
        table: Type[REGISTRY_TABLES],
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

        card = save_card_artifacts(card=card, storage_client=self.storage)
        record = card.create_registry_record()
        self._add_and_commit(table=table, card=record.model_dump())


class CardRegistryHelperServer(ServerMixin, CardRegistryHelper):
    def list_cards(
        self,
        table: Type[REGISTRY_TABLES],
        uid: Optional[str] = None,
        name: Optional[str] = None,
        team: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        max_date: Optional[str] = None,
        limit: Optional[int] = None,
        ignore_release_candidates: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves records from registry

        Args:
            name:
                Artifact record name
            team:
                Team data is assigned to
            version:
                Optional version number of existing data. If not specified,
                the most recent version will be used. Version can also include tilde (~), caret (^) and * characters.
            tags:
                Dictionary of key, value tags to search for
            uid:
                Unique identifier for DataCard. If present, the uid takes precedence.
            max_date:
                Max date to search. (e.g. "2023-05-01" would search for cards up to and including "2023-05-01")
            limit:
                Places a limit on result list. Results are sorted by SemVer


        Returns:
            Dictionary of records
        """

        cleaned_name = clean_string(name)
        cleaned_team = clean_string(team)

        query = card_validator.query_engine.record_from_table_query(
            table=table,
            name=cleaned_name,
            team=cleaned_team,
            version=version,
            uid=uid,
            max_date=max_date,
            tags=tags,
        )

        records = self.validator.get_sql_records(query=query)
        sorted_records = self.card_ver.sort_by_version(records=records)

        if version is not None:
            if ignore_release_candidates:
                sorted_records = [
                    record for record in sorted_records if not SemVerUtils.is_release_candidate(record["version"])
                ]
            if any(symbol in version for symbol in [SemVerSymbols.CARET, SemVerSymbols.TILDE]):
                # return top version
                return sorted_records[:1]

        if version is None and ignore_release_candidates:
            sorted_records = [
                record for record in sorted_records if not SemVerUtils.is_release_candidate(record["version"])
            ]

        return sorted_records[:limit]

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
    def list_cards(
        self,
        table: Type[REGISTRY_TABLES],
        uid: Optional[str] = None,
        name: Optional[str] = None,
        team: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        max_date: Optional[str] = None,
        limit: Optional[int] = None,
        ignore_release_candidates: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Retrieves records from registry

        Args:
            name:
                Card Name
            team:
                Team Card
            version:
                Version. If not specified, the most recent version will be used.
            uid:
                Unique identifier for an ArtifactCard. If present, the uid takes precedence.
            tags:
                Tags associated with a given ArtifactCard
            max_date:
                Max date to search. (e.g. "2023-05-01" would search for cards up to and including "2023-05-01")
            limit:
                Places a limit on result list. Results are sorted by SemVer

        Returns:
            Dictionary of card records
        """
        data = card_validator.session.post_request(
            route=card_validator.routes.LIST_CARDS,
            json={
                "name": name,
                "team": team,
                "version": version,
                "uid": uid,
                "max_date": max_date,
                "limit": limit,
                "tags": tags,
                "table_name": table.__tablename__,
                "ignore_release_candidates": ignore_release_candidates,
            },
        )

        return data["cards"]

    @log_card_change
    def _add_and_commit(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=self.routes.CREATE_CARD,
            json={
                "card": card,
                "table_name": table.__tablename__,
            },
        )

        if bool(data.get("registered")):
            return card, "registered"
        raise ValueError("Failed to register card")

    @log_card_change
    def update_card_record(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=self.routes.UPDATE_CARD,
            json={
                "card": card,
                "table_name": table.__tablename__,
            },
        )

        if bool(data.get("updated")):
            return card, "updated"
        raise ValueError("Failed to update card")


def get_registry_helper() -> CardRegistryHelper:
    if USE_CLIENT_CLASS:
        return CardRegistryHelperClient()
    return CardRegistryHelperServer()


registry_helper = get_registry_helper()
