# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from functools import cached_property
from typing import Any, Dict, List, Optional, Tuple, cast

import pandas as pd

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.request_helpers import ApiClient, api_routes
from opsml.registry.cards.types import RegistryType
from opsml.registry.sql.base.registry_base import SQLRegistryBase
from opsml.registry.sql.base.utils import log_card_change
from opsml.registry.sql.semver import CardVersion, VersionType
from opsml.registry.utils.settings import settings

logger = ArtifactLogger.get_logger()


class ClientRegistry(SQLRegistryBase):
    """A registry that retrieves data from an opsml server instance."""

    def __init__(self, registry_type: RegistryType):
        super().__init__(registry_type)

        assert isinstance(settings.request_client, ApiClient)
        self._session: ApiClient = settings.request_client

        self._registry_type = registry_type

    @cached_property
    def table_name(self) -> str:
        """Returns the table name for this registry type"""
        data = self._session.get_request(
            route=api_routes.TABLE_NAME,
            params={"registry_type": self.registry_type.value},
        )

        return cast(str, data["table_name"])

    @property
    def unique_teams(self) -> List[str]:
        """Returns a list of unique teams"""
        data = self._session.get_request(
            route=api_routes.TEAM_CARDS,
            params={"registry_type": self.registry_type.value},
        )

        return cast(List[str], data["teams"])

    def get_unique_card_names(self, team: Optional[str] = None) -> List[str]:
        """Returns a list of unique card names

        Args:
            team:
                Team to filter by

        Returns:
            List of unique card names
        """

        params = {"registry_type": self.registry_type.value}

        if team is not None:
            params["team"] = team

        data = self._session.get_request(
            route=api_routes.NAME_CARDS,
            params=params,
        )

        return cast(List[str], data["names"])

    def check_uid(self, uid: str, registry_type: RegistryType) -> bool:
        data = self._session.post_request(
            route=api_routes.CHECK_UID,
            json={"uid": uid, "registry_type": registry_type.value},
        )

        return bool(data.get("uid_exists"))

    def set_version(
        self,
        name: str,
        team: str,
        pre_tag: str,
        build_tag: str,
        version_type: VersionType = VersionType.MINOR,
        supplied_version: Optional[CardVersion] = None,
    ) -> str:
        if supplied_version is not None:
            version_to_send = supplied_version.model_dump()
        else:
            version_to_send = None

        data = self._session.post_request(
            route=api_routes.VERSION,
            json={
                "name": name,
                "team": team,
                "version": version_to_send,
                "version_type": version_type,
                "registry_type": self._registry_type.value,
                "pre_tag": pre_tag,
                "build_tag": build_tag,
            },
        )

        return str(data["version"])

    def list_cards(
        self,
        uid: Optional[str] = None,
        name: Optional[str] = None,
        team: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        max_date: Optional[str] = None,
        limit: Optional[int] = None,
        ignore_release_candidates: bool = False,
        query_terms: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
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
            ignore_release_candidates:
                If True, release candidates will be ignored
            query_terms:
                Dictionary of query terms to filter by

        Returns:
            Dictionary of card records
        """
        data = self._session.post_request(
            route=api_routes.LIST_CARDS,
            json={
                "name": name,
                "team": team,
                "version": version,
                "uid": uid,
                "max_date": max_date,
                "limit": limit,
                "tags": tags,
                "registry_type": self.registry_type.value,
                "ignore_release_candidates": ignore_release_candidates,
                "query_terms": query_terms,
            },
        )

        return data["cards"]

    @log_card_change
    def add_and_commit(self, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=api_routes.CREATE_CARD,
            json={
                "card": card,
                "registry_type": self.registry_type.value,
            },
        )

        if bool(data.get("registered")):
            return card, "registered"
        raise ValueError("Failed to register card")

    @log_card_change
    def update_card_record(self, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=api_routes.UPDATE_CARD,
            json={
                "card": card,
                "registry_type": self.registry_type.value,
            },
        )

        if bool(data.get("updated")):
            return card, "updated"
        raise ValueError("Failed to update card")

    @log_card_change
    def delete_card_record(self, card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self._session.post_request(
            route=api_routes.DELETE_CARD,
            json={
                "card": card,
                "registry_type": self.registry_type.value,
            },
        )

        if bool(data.get("deleted")):
            return card, "deleted"
        raise ValueError("Failed to delete card")

    @staticmethod
    def validate(registry_name: str) -> bool:
        raise NotImplementedError
