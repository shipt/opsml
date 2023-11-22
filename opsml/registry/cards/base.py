# pylint: disable=too-many-lines
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd
import polars as pl
from pydantic import BaseModel, ConfigDict, model_validator

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import clean_string, validate_name_team_pattern
from opsml.registry.cards.types import CardInfo, OpsmlCardEnvVars
from opsml.registry.sql.records import RegistryRecord
from opsml.registry.utils.settings import settings

logger = ArtifactLogger.get_logger()
storage_client = settings.storage_client

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
    @classmethod
    def validate_args(cls, card_args: Dict[str, Any]) -> Dict[str, Any]:  # pylint: disable=arguments-renamed
        """Validate base args and Lowercase name and team"""

        card_info = card_args.get("info")
        card_args = cls._check_base_args(card_args, card_info)

        # clean
        for key in ["name", "team"]:
            card_args[key] = clean_string(card_args.get(key))

        if all([card_args.get("name"), card_args.get("team")]):
            # validate name and team for pattern
            validate_name_team_pattern(
                name=card_args["name"],
                team=card_args["team"],
            )

        return card_args

    @staticmethod
    def _check_base_args(card_args: Dict[str, Any], card_info: Optional[CardInfo] = None) -> Dict[str, Any]:
        """Check base args for artifact cards

        Args:
            card_args:
                Dictionary of card args
            card_info:
                Optional CardInfo provided by the user

        Returns:
            Dictionary of card args with updated values
        """

        for key in ["name", "team", "user_email", "version", "uid"]:
            value = card_args.get(key)

            # check vars
            # 1 - user supplied value overrides
            if value is None:
                if card_info is not None:
                    # 2 card_info value overrides
                    # if card info value is none, attempt to load env var
                    card_args[key] = getattr(card_info, key, OpsmlCardEnvVars.get_env_var_value(key))

                else:
                    # 3 - env var overrides
                    card_args[key] = OpsmlCardEnvVars.get_env_var_value(key)

        return card_args

    def create_registry_record(self) -> RegistryRecord:
        """Creates a registry record from self attributes"""
        raise NotImplementedError

    def add_tag(self, key: str, value: str):
        self.tags[key] = str(value)

    @property
    def card_type(self) -> str:
        raise NotImplementedError
