#### Helper class that builds a server or client instance


from typing import Dict, Any, Tuple, Type, Optional, List
from semver import VersionInfo
import uuid
from opsml.registry.sql.settings import settings
from opsml.registry.sql.registry_helpers.semver import SemVerUtils, CardVersion, VersionType
from opsml.registry.cards.card_saver import save_card_artifacts
from opsml.helpers.exceptions import VersionError
from opsml.registry.cards import ArtifactCard
from opsml.registry.sql.sql_schema import REGISTRY_TABLES
from opsml.registry.storage.types import ArtifactStorageSpecs
from opsml.registry.storage.storage_system import StorageClientType


class _RegistryHelper:
    def __init__(self):
        self.storage_client = settings.storage_client

    ##### Storage helpers
    def set_artifact_storage_spec(self, table_name: str, card: ArtifactCard) -> None:
        """Creates artifact storage info to associate with artifacts"""

        save_path = f"{table_name}/{card.team}/{card.name}/v{card.version}"

        artifact_storage_spec = ArtifactStorageSpecs(save_path=save_path)
        self.update_storage_client_metadata(storage_specdata=artifact_storage_spec)

    def update_storage_client_metadata(self, storage_specdata: ArtifactStorageSpecs):
        """Updates storage metadata"""
        self.storage_client.storage_spec = storage_specdata

    ##### Card validation helpers
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

    ##### Card version helpers
    def set_version(
        self,
        table: Type[REGISTRY_TABLES],
        name: str,
        team: str,
        pre_tag: str,
        build_tag: str,
        version_type: VersionType,
        supplied_version: Optional[CardVersion] = None,
    ) -> str:
        raise NotImplementedError

    def sort_by_version(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        versions = [record["version"] for record in records]
        sorted_versions = SemVerUtils.sort_semvers(versions)

        sorted_records = []
        for version in sorted_versions:
            for record in records:
                if record["version"] == version:
                    sorted_records.append(record)

        return sorted_records

    def validate_pre_build_version(self, version: Optional[str] = None) -> CardVersion:
        if version is None:
            raise ValueError("Cannot set pre-release or build tag without a version")
        card_version = CardVersion(version=version)

        if not card_version.is_full_semver:
            raise ValueError("Cannot set pre-release or build tag without a full major.minor.patch specified")

        return card_version

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
                self._validate_semver(
                    table=table,
                    name=card.name,
                    team=card.team,
                    version=card_version,
                )
                return None

        version = self.card_ver.set_version(
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
