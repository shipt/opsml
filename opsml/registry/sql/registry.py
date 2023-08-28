# pylint: disable=protected-access
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from typing import Any, Iterable, Optional, Union, cast

from sqlalchemy.sql.expression import ColumnElement, FromClause

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.cards import ArtifactCard, ModelCard
from opsml.registry.cards.types import CardType
from opsml.registry.sql.registry_base import VersionType, Registry
from opsml.registry.sql.registry_helpers.card_registry import registry_helper
from opsml.registry.sql.sql_schema import RegistryTableNames
from opsml.registry.storage.storage_system import StorageClientType

logger = ArtifactLogger.get_logger(__name__)


SqlTableType = Optional[Iterable[Union[ColumnElement[Any], FromClause, int]]]


class DataCardRegistry(Registry):
    @staticmethod
    def validate(registry_name: str) -> bool:
        return registry_name in RegistryTableNames.DATA.value


class ModelCardRegistry(Registry):
    def _get_data_table_name(self) -> str:
        return RegistryTableNames.DATA.value

    def _validate_datacard_uid(self, uid: str) -> None:
        table_to_check = self._get_data_table_name()
        exists = registry_helper.validator.check_uid_exists(uid=uid, table_to_check=table_to_check)
        if not exists:
            raise ValueError("ModelCard must be associated with a valid DataCard uid")

    def _has_datacard_uid(self, uid: Optional[str]) -> bool:
        return bool(uid)

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

        if not self._has_datacard_uid(uid=model_card.datacard_uid):
            raise ValueError("""ModelCard must be associated with a valid DataCard uid""")

        if model_card.datacard_uid is not None:
            self._validate_datacard_uid(uid=model_card.datacard_uid)

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

        self._registry = self._set_registry(registry_name=registry_name)
        self.table_name = self._registry._table.__tablename__

    def __new__(cls, registry_name: str) -> Registry:
        return set_registry(registry_name=registry_name)


class CardRegistries:
    def __init__(self):
        """Instantiates class that contains all registries"""
        self.data = CardRegistry(registry_name=CardType.DATACARD.value)
        self.model = CardRegistry(registry_name=CardType.MODELCARD.value)
        self.run = CardRegistry(registry_name=CardType.RUNCARD.value)
        self.pipeline = CardRegistry(registry_name=CardType.PIPELINECARD.value)
        self.project = CardRegistry(registry_name=CardType.PROJECTCARD.value)

    def set_storage_client(self, storage_client: StorageClientType):
        for attr in ["data", "model", "run", "project", "pipeline"]:
            registry: CardRegistry = getattr(self, attr)
            registry._registry.storage_client = storage_client
