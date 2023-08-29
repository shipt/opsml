# pylint: disable=protected-access
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from typing import Any, Iterable, Optional, Union, cast, Dict, List

from sqlalchemy.sql.expression import ColumnElement, FromClause
import pandas as pd
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.cards import ArtifactCard, ModelCard
from opsml.registry.cards.types import CardType, CardInfo
from opsml.registry.sql.registry_base import VersionType, Registry
from opsml.registry.sql.registry_helpers import registry_helper
from opsml.registry.sql.sql_schema import RegistryTableNames, TableSchema
from opsml.registry.storage.storage_system import StorageClientType

logger = ArtifactLogger.get_logger(__name__)


SqlTableType = Optional[Iterable[Union[ColumnElement[Any], FromClause, int]]]


class DataCardRegistry(Registry):
    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name in RegistryTableNames.DATA.value


class ModelCardRegistry(Registry):
    def register_card(
        self,
        card: ArtifactCard,
        version_type: VersionType = VersionType.MINOR,
        pre_tag: str = "rc",
        build_tag: str = "build",
    ) -> None:
        """
        Adds new record to registry.

        Args:
            card:
                Card to register
            version_type:
                Version type for increment. Options are "major", "minor" and
                "patch". Defaults to "minor"
            pre_tag:
                pre-release tag
            build_tag:
                build tag
        """

        model_card = cast(ModelCard, card)

        if model_card.datacard_uid is None:
            raise ValueError("""ModelCard must be associated with a valid DataCard uid""")

        if model_card.datacard_uid is not None:
            if not registry_helper.check_uid_exists(
                uid=model_card.datacard_uid,
                table=TableSchema.get_table(RegistryTableNames.DATA.value),
            ):
                raise ValueError("""ModelCard must be associated with a valid DataCard uid""")

        return super().register_card(
            card=card,
            version_type=version_type,
            pre_tag=pre_tag,
            build_tag=build_tag,
        )

    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name in RegistryTableNames.MODEL.value


class RunCardRegistry(Registry):
    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name in RegistryTableNames.RUN.value


class PipelineCardRegistry(Registry):
    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name in RegistryTableNames.PIPELINE.value


class ProjectCardRegistry(Registry):
    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name in RegistryTableNames.PROJECT.value


def set_registry(registry_name: str) -> Registry:
    """Returns a SQL registry to be used to register Cards

    Args:
        registry_name: Name of the registry (pipeline, model, data, experiment)

    Returns:
        SQL Registry
    """

    registry_name = RegistryTableNames[registry_name.upper()].value
    registry = next(
        registry
        for registry in Registry.__subclasses__()
        if registry.validate(
            registry_name=registry_name,
        )
    )

    return registry(table_name=registry_name)


class CardRegistry:
    def __init__(self, registry_name: str):
        """
        Interface for connecting to any of the ArtifactCard registries

        Args:
            registry_name:
                Name of the registry to connect to. Options are "pipeline",
                "model", "data" and "experiment".

        Returns:
            Instantiated connection to specific Card registry

        Example:
            # With connection type cloud_sql = CloudSQLConnection(...)
            data_registry = CardRegistry(registry_name="data",
            connection_client=cloud_sql)

            # With connection client data_registry =
            CardRegistry(registry_name="data", connection_type="gcp")
        """

        self._registry = set_registry(registry_name=registry_name)

    def register_card(
        self,
        card: ArtifactCard,
        version_type: VersionType = VersionType.MINOR,
        pre_tag: str = "rc",
        build_tag: str = "build",
    ) -> None:
        """
        Adds new record to registry.

        Args:
            card:
                card to register
            version_type:
                Version type for increment. Options are "major", "minor" and
                "patch". Defaults to "minor".
            pre_tag:
                pre-release tag to add to card version
            build_tag:
                build tag to add to card version
        """

        self._registry.register_card(
            card=card,
            version_type=version_type,
            pre_tag=pre_tag,
            build_tag=build_tag,
        )

    def list_cards(
        self,
        uid: Optional[str] = None,
        name: Optional[str] = None,
        team: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        info: Optional[CardInfo] = None,
        max_date: Optional[str] = None,
        limit: Optional[int] = None,
        as_dataframe: bool = False,
        ignore_release_candidates: bool = False,
    ) -> Union[List[Dict[str, Any]], pd.DataFrame]:
        """Retrieves records from registry

        Args:
            name:
                Card name
            team:
                Team associated with card
            version:
                Optional version number of existing data. If not specified, the
                most recent version will be used
            tags:
                Dictionary of key, value tags to search for
            uid:
                Unique identifier for Card. If present, the uid takes precedence
            max_date:
                Max date to search. (e.g. "2023-05-01" would search for cards up to and including "2023-05-01")
            limit:
                Places a limit on result list. Results are sorted by SemVer
            as_dataframe:
                If True, returns a pandas dataframe. If False, returns a list of records
            info:
                CardInfo object. If present, the info object takes precedence

        Returns:
            pandas dataframe of records or list of dictionaries
        """

        if info is not None:
            name = name or info.name
            team = team or info.team
            uid = uid or info.uid
            version = version or info.version
            tags = tags or info.tags

        if name is not None:
            name = name.lower()

        if team is not None:
            team = team.lower()

        card_list = self._registry.list_cards(
            uid=uid,
            name=name,
            team=team,
            version=version,
            max_date=max_date,
            limit=limit,
            tags=tags,
            ignore_release_candidates=ignore_release_candidates,
        )

        if as_dataframe:
            return pd.DataFrame(card_list)

        return card_list

    def load_card(
        self,
        name: Optional[str] = None,
        uid: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        version: Optional[str] = None,
        info: Optional[CardInfo] = None,
        ignore_release_candidates: bool = False,
    ) -> ArtifactCard:
        """Loads a specific card

        Args:
            name:
                Optional Card name
            uid:
                Unique identifier for card. If present, the uid takes
                precedence.
            tags:
                Optional tags associated with model.
            version:
                Optional version number of existing data. If not specified, the
                most recent version will be used
            info:
                Optional CardInfo object. If present, the info takes precedence

        Returns
            ArtifactCard
        """

        # find better way to do this later
        if info is not None:
            name = name or info.name
            uid = uid or info.uid
            version = version or info.version
            tags = tags or info.tags

        return self._registry.load_card(
            uid=uid,
            name=name,
            version=version,
            tags=tags,
            ignore_release_candidates=ignore_release_candidates,
        )

    def update_card(self, card: ArtifactCard) -> None:
        """
        Update an artifact card based on current registry

        Args:
            card:
                Card to register
        """
        return self._registry.update_card(card=card)

    def query_value_from_card(self, uid: str, columns: List[str]) -> Dict[str, Any]:
        """
        Query column values from a specific Card

        Args:
            uid:
                Uid of Card
            columns:
                List of columns to query

        Returns:
            Dictionary of column, values pairs
        """
        results = self._registry.list_cards(uid=uid)[0]
        return {col: results[col] for col in columns}


class CardRegistries:
    def __init__(self):
        """Instantiates class that contains all registries"""
        self.data = CardRegistry(registry_name=CardType.DATACARD.value)
        self.model = CardRegistry(registry_name=CardType.MODELCARD.value)
        self.run = CardRegistry(registry_name=CardType.RUNCARD.value)
        self.pipeline = CardRegistry(registry_name=CardType.PIPELINECARD.value)
        self.project = CardRegistry(registry_name=CardType.PROJECTCARD.value)

    def set_storage_client(self, storage_client: StorageClientType):
        for registry in ["data", "model", "run", "pipeline", "project"]:
            _registry: CardRegistry = getattr(self, registry)
            _registry._registry._helper.storage_client = storage_client
