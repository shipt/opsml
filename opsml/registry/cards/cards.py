# pylint: disable=too-many-lines

from functools import cached_property
from typing import Any, Dict, List, Optional, Union, cast

import numpy as np
import pandas as pd
import polars as pl
from pyarrow import Table
from pydantic import BaseModel, root_validator, validator

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import (
    FindPath,
    TypeChecker,
    clean_string,
    validate_name_team_pattern,
)
from opsml.model.predictor import OnnxModelPredictor
from opsml.model.types import (
    ApiDataSchemas,
    DataDict,
    Feature,
    ModelMetadata,
    ModelReturn,
    OnnxModelDefinition,
    TorchOnnxArgs,
)
from opsml.profile.profile_data import DataProfiler, ProfileReport
from opsml.registry.cards.types import (
    METRICS,
    PARAMS,
    CardInfo,
    CardType,
    DataCardUris,
    Metric,
    ModelCardUris,
    Param,
)
from opsml.registry.data.splitter import DataHolder, DataSplit, DataSplitter
from opsml.registry.sql.records import (
    ARBITRARY_ARTIFACT_TYPE,
    DataRegistryRecord,
    ModelRegistryRecord,
    PipelineRegistryRecord,
    ProjectRegistryRecord,
    RegistryRecord,
    RunRegistryRecord,
)
from opsml.registry.sql.settings import settings
from opsml.registry.storage.artifact_storage import load_record_artifact_from_storage
from opsml.registry.storage.types import ArtifactStorageSpecs, ArtifactStorageType

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


class PipelineCard(ArtifactCard):
    """Create a PipelineCard from specified arguments

    Args:
        name:
            Pipeline name
        team:
            Team that this card is associated with
        user_email:
            Email to associate with card
        uid:
            Unique id (assigned if card has been registered)
        version:
            Current version (assigned if card has been registered)
        pipeline_code_uri:
            Storage uri of pipeline code
        datacard_uids:
            Optional list of DataCard uids to associate with pipeline
        modelcard_uids:
            Optional list of ModelCard uids to associate with pipeline
        runcard_uids:
            Optional list of RunCard uids to associate with pipeline

    """

    pipeline_code_uri: Optional[str] = None
    datacard_uids: List[Optional[str]] = []
    modelcard_uids: List[Optional[str]] = []
    runcard_uids: List[Optional[str]] = []

    def add_card_uid(self, uid: str, card_type: str):
        """
        Adds Card uid to appropriate card type attribute

        Args:
            uid:
                Card uid
            card_type:
                Card type. Accepted values are "data", "model", "run"
        """
        card_type = card_type.lower()
        if card_type.lower() not in [CardType.DATACARD.value, CardType.RUNCARD.value, CardType.MODELCARD.value]:
            raise ValueError("""Only 'model', 'run' and 'data' are allowed values for card_type""")

        current_ids = getattr(self, f"{card_type}card_uids")
        new_ids = [*current_ids, *[uid]]
        setattr(self, f"{card_type}card_uids", new_ids)

    def load_pipeline_code(self):
        raise NotImplementedError

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record from the current PipelineCard"""
        return PipelineRegistryRecord(**self.dict())

    @property
    def card_type(self) -> str:
        return CardType.PIPELINECARD.value


class ProjectCard(ArtifactCard):
    """
    Card containing project information
    """

    project_id: Optional[str] = None

    @validator("project_id", pre=True, always=True)
    def create_project_id(cls, value, values, **kwargs):
        return f'{values["name"]}:{values["team"]}'

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record for a project"""

        return ProjectRegistryRecord(**self.dict())

    @property
    def card_type(self) -> str:
        return CardType.PROJECTCARD.value
