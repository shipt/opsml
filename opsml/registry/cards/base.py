# pylint: disable=too-many-lines


from typing import Dict, Optional

from pydantic import BaseModel, root_validator

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import clean_string, validate_name_team_pattern
from opsml.registry.cards.types import CardInfo
from opsml.registry.sql.records import RegistryRecord
from opsml.registry.sql.settings import settings

logger = ArtifactLogger.get_logger(__name__)
storage_client = settings.storage_client


class ArtifactCard(BaseModel):
    """Base pydantic class for artifact cards"""

    name: str
    team: str
    user_email: str
    version: Optional[str] = None
    uid: Optional[str] = None
    info: Optional[CardInfo] = None
    tags: Dict[str, str] = {}

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False
        smart_union = True

    @root_validator(pre=True)
    def validate(cls, env_vars):
        """Validate base args and Lowercase name and team"""

        card_info = env_vars.get("info")

        for key in ["name", "team", "user_email", "version", "uid"]:
            val = env_vars.get(key)

            if card_info is not None:
                val = val or getattr(card_info, key)

            if key in ["name", "team"]:
                if val is not None:
                    val = clean_string(val)

            env_vars[key] = val

        # validate name and team for pattern
        validate_name_team_pattern(
            name=env_vars["name"],
            team=env_vars["team"],
        )

        return env_vars

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record from self attributes"""
        raise NotImplementedError

    def add_tag(self, key: str, value: str):
        self.tags[key] = str(value)

    @property
    def card_type(self) -> str:
        raise NotImplementedError
