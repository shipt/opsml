# pylint: disable=too-many-lines

from typing import Optional

from pydantic import validator

from opsml.registry.cards.base import ArtifactCard
from opsml.registry.cards.types import CardType
from opsml.registry.sql.records import ProjectRegistryCard, RegistryCard


class ProjectCard(ArtifactCard):
    """
    Card containing project information
    """

    project_id: Optional[str] = None

    @validator("project_id", pre=True, always=True)
    def create_project_id(cls, value, values, **kwargs):
        return f'{values["name"]}:{values["team"]}'

    def create_registry_record(self) -> RegistryCard:
        """Creates a registry record for a project"""

        return ProjectRegistryCard(**self.dict())

    @property
    def card_type(self) -> str:
        return CardType.PROJECTCARD.value
