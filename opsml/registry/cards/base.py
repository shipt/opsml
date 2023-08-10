# pylint: disable=too-many-lines

from pydantic import BaseModel, root_validator

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import clean_string, validate_name_team_pattern
from opsml.registry.cards.types import CardInfo, CardType
from opsml.registry.sql.records import RegistryCard

from typing import Dict, Optional, Union

import numpy as np
import pandas as pd
import polars as pl
from pydantic import BaseModel, model_validator, ConfigDict


from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import (
    clean_string,
    validate_name_team_pattern,
)

from opsml.registry.cards.types import (
    CardInfo,
)
from opsml.registry.sql.records import (
    RegistryRecord,
)
from opsml.registry.sql.settings import settings

logger = ArtifactLogger.get_logger(__name__)
storage_client = settings.storage_client


class AuditCard(Protocol):
    @property
    def uid(self):
        ...

    def add_card_uid(self, card_type: str, uid: str) -> None:
        ...


SampleModelData = Optional[Union[pd.DataFrame, np.ndarray, Dict[str, np.ndarray], pl.DataFrame]]


class ArtifactCard(BaseModel):
    """Base pydantic class for artifact cards"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=False,
        validate_default=True,
    )

    name: str
    team: str
    user_email: str
    version: Optional[str] = None
    uid: Optional[str] = None
    info: Optional[CardInfo] = None
    tags: Dict[str, str] = {}

    @model_validator(mode="before")
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

    def create_registry_record(self) -> RegistryCard:
        """Creates a registry record from self attributes"""
        raise NotImplementedError

    def add_tag(self, key: str, value: str):
        self.tags[key] = str(value)

    def add_to_auditcard(self, auditcard: Optional[AuditCard] = None, auditcard_uid: Optional[str] = None) -> None:
        """Add card uid to auditcard

        Args:
            auditcard:
                Optional AuditCard to add card uid to
            auditcard_uid:
                Optional uid of AuditCard to add card uid to

        """

        if self.card_type == CardType.AUDITCARD:
            raise ValueError("add_to_auditcard is not implemented for AuditCard")

        if self.uid is None:
            raise ValueError("Card must be registered before adding to auditcard")

        if auditcard_uid is not None:
            from opsml.registry.sql.registry import (  # pylint: disable=cyclic-import
                CardRegistry,
            )

            audit_registry = CardRegistry(registry_name="audit")
            card = audit_registry.load_card(uid=auditcard_uid)
            card.add_card_uid(card_type=self.card_type, uid=self.uid)  # type: ignore
            return audit_registry.update_card(card=card)

        if auditcard is not None:
            return auditcard.add_card_uid(card_type=self.card_type, uid=self.uid)

        raise ValueError("Either auditcard or uid must be specified")

    @property
    def card_type(self) -> str:
        raise NotImplementedError
