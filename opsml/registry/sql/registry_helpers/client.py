from typing import Dict, Any, Tuple, Type, Optional, List
from opsml.registry.sql.registry_helpers.base import _RegistryHelper
from opsml.registry.sql.registry_helpers.semver import CardVersion, VersionType
from opsml.registry.sql.registry_helpers.mixins import ClientMixin
from opsml.registry.sql.sql_schema import REGISTRY_TABLES
from opsml.registry.sql.query_helpers import log_card_change  # type: ignore


class _ClientRegistryHelper(ClientMixin, _RegistryHelper):
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

        Returns:
            Dictionary of card records
        """
        data = self.session.post_request(
            route=self.routes.LIST_CARDS,
            json={
                "name": name,
                "team": team,
                "version": version,
                "uid": uid,
                "max_date": max_date,
                "limit": limit,
                "tags": tags,
                "table_name": table.__tablename__,
                "ignore_release_candidates": ignore_release_candidates,
            },
        )

        return data["cards"]

    @log_card_change
    def _add_and_commit(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self.session.post_request(
            route=self.routes.CREATE_CARD,
            json={
                "card": card,
                "table_name": table.__tablename__,
            },
        )

        if bool(data.get("registered")):
            return card, "registered"
        raise ValueError("Failed to register card")

    @log_card_change
    def update_card_record(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        data = self.session.post_request(
            route=self.routes.UPDATE_CARD,
            json={
                "card": card,
                "table_name": table.__tablename__,
            },
        )

        if bool(data.get("updated")):
            return card, "updated"
        raise ValueError("Failed to update card")

    def check_uid_exists(self, uid: str, table: Type[REGISTRY_TABLES]) -> bool:
        data = self.session.post_request(
            route=self.routes.CHECK_UID,
            json={"uid": uid, "table_name": table.__tablename__},
        )

        return bool(data.get("uid_exists"))

    def set_version(
        self,
        table: Type[REGISTRY_TABLES],
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

        data = self.session.post_request(
            route=self.routes.VERSION,
            json={
                "name": name,
                "team": team,
                "version": version_to_send,
                "version_type": version_type,
                "table_name": table.__tablename__,
                "pre_tag": pre_tag,
                "build_tag": build_tag,
            },
        )

        return data.get("version")
