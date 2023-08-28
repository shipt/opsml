#### Helper class that builds a server or client instance


from typing import Dict, Any, Tuple, cast, Type, Optional, List
from opsml.helpers.utils import clean_string
from opsml.registry.sql.settings import settings
from opsml.registry.sql.registry_helpers.semver import SemVerSymbols, SemVerUtils
from opsml.registry.sql.query_helpers import log_card_change  # type: ignore
from opsml.registry.cards.card_saver import save_card_artifacts
from opsml.helpers.exceptions import VersionError
from opsml.registry.sql.registry_helpers.card_storage import CardStorageClient
from opsml.registry.cards import ArtifactCard
from opsml.registry.sql.registry_helpers.mixins import ClientMixin, ServerMixin
from opsml.registry.sql.sql_schema import REGISTRY_TABLES, RegistryTableNames
from opsml.registry.storage.storage_system import StorageClientType
from semver import VersionInfo

from opsml.registry.sql.registry_helpers.semver import (
    CardVersion,
    VersionType,
    SemVerUtils,
    SemVerRegistryValidator,
)

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


class _RegistryHelper:
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

    def _validate_semver(self, table: type[REGISTRY_TABLES], name: str, team: str, version: CardVersion) -> None:
        """
        Validates version if version is manually passed to Card

        Args:
            name:
                Name of card
            team:
                Team of card
            version:
                Version of card
        Returns:
            `CardVersion`
        """
        if version.is_full_semver:
            records = self.list_cards(table=table, name=name, version=version.valid_version)
            if len(records) > 0:
                if records[0]["team"] != team:
                    raise ValueError("""Model name already exists for a different team. Try a different name.""")

                for record in records:
                    ver = VersionInfo.parse(record["version"])

                    if ver.prerelease is None and SemVerUtils.is_release_candidate(version.version):
                        raise VersionError(
                            "Cannot create a release candidate for an existing official version. %s" % version.version
                        )

                    if record["version"] == version.version:
                        raise VersionError("Version combination already exists. %s" % version.version)

    def set_card_version(
        self,
        table: Type[REGISTRY_TABLES],
        card: ArtifactCard,
        version_type: VersionType,
        pre_tag: str,
        build_tag: str,
    ):
        """Sets a given card's version and uid

        Args:
            card:
                Card to set
            version_type:
                Type of version increment
        """

        card_version = None

        # validate pre-release and/or build tag
        if version_type in [VersionType.PRE, VersionType.BUILD, VersionType.PRE_BUILD]:
            card_version = self.card_ver.validate_pre_build_version(version=card.version)

        # if DS specifies version and not release candidate
        if card.version is not None and version_type not in [VersionType.PRE, VersionType.PRE_BUILD]:
            # build tags are allowed with "official" versions
            if version_type == VersionType.BUILD:
                # check whether DS-supplied version has a build tag already
                if VersionInfo.parse(card.version).build is None:
                    card.version = self.card_ver.set_version(
                        name=card.name,
                        supplied_version=card_version,
                        team=card.team,
                        version_type=version_type,
                        pre_tag=pre_tag,
                        build_tag=build_tag,
                    )

            card_version = CardVersion(version=card.version)
            if card_version.is_full_semver:
                self._validate_semver(name=card.name, team=card.team, version=card_version)
                return None

        version = self.set_version(
            table=table,
            name=card.name,
            supplied_version=card_version,
            team=card.team,
            version_type=version_type,
            pre_tag=pre_tag,
            build_tag=build_tag,
        )

        # for instances where tag is explicitly provided for major, minor, patch
        if version_type in [VersionType.MAJOR, VersionType.MINOR, VersionType.PATCH]:
            if len(pre_tag.split(".")) == 2:
                version = f"{version}-{pre_tag}"

            if len(build_tag.split(".")) == 2:
                version = f"{version}+{build_tag}"

        card.version = version

        return None


class _RegistryHelperServer(ServerMixin, _RegistryHelper):
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

        query = self.query_engine.record_from_table_query(
            table=table,
            name=cleaned_name,
            team=cleaned_team,
            version=version,
            uid=uid,
            max_date=max_date,
            tags=tags,
        )

        records = self.query_engine.get_sql_records(query=query)
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


class _RegistryHelperClient(ClientMixin, _RegistryHelper):
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


def get_registry_helper() -> _RegistryHelper:
    if USE_CLIENT_CLASS:
        return _RegistryHelperClient()
    return _RegistryHelperServer()


registry_helper = get_registry_helper()
