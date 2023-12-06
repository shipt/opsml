# pylint: disable=too-many-lines
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from typing import Any, Dict

from pydantic import model_validator

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.cards.base import ArtifactCard
from opsml.registry.cards.types import CardType
from opsml.registry.sql.records import ProjectRegistryRecord, RegistryRecord
from opsml.registry.utils.settings import settings

logger = ArtifactLogger.get_logger()
storage_client = settings.storage_client


class ProjectCard(ArtifactCard):
    """
    Card containing project information
    """

    project_id: str

    @model_validator(mode="before")
    @classmethod
    def create_project_id(cls, card_args: Dict[str, Any]) -> Dict[str, Any]:
        card_args["project_id"] = f'{card_args["team"]}:{card_args["name"]}'
        return card_args

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record for a project"""

        return ProjectRegistryRecord(**self.model_dump())

    @property
    def card_type(self) -> str:
        return CardType.PROJECTCARD.value
