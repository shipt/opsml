from typing import Dict, Any, Tuple, cast, Type, Optional, List
from opsml.registry.sql.registry_helpers.semver import (
    SemVerSymbols,
    SemVerUtils,
    SemVerRegistryValidator,
    CardVersion,
    VersionType,
)
from opsml.helpers.utils import clean_string
from opsml.registry.sql.registry_helpers.base import _RegistryHelper
from opsml.registry.sql.registry_helpers.mixins import ServerMixin
from opsml.registry.sql.sql_schema import REGISTRY_TABLES
from opsml.registry.sql.query_helpers import log_card_change  # type: ignore


class _ServerRegistryHelper(ServerMixin, _RegistryHelper):
    def __init__(self):
        super().__init__()

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
    ) -> List[Dict[str, Any]]:
        """
        Retrieves records from registry

        Args:
            name:
                Artifact record name
            team:
                Team data is assigned to
            version:
                Optional version number of existing data. If not specified,
                the most recent version will be used. Version can also include tilde (~), caret (^) and * characters.
            tags:
                Dictionary of key, value tags to search for
            uid:
                Unique identifier for DataCard. If present, the uid takes precedence.
            max_date:
                Max date to search. (e.g. "2023-05-01" would search for cards up to and including "2023-05-01")
            limit:
                Places a limit on result list. Results are sorted by SemVer


        Returns:
            Dictionary of records
        """

        cleaned_name = clean_string(name)
        cleaned_team = clean_string(team)

        query = self.query_engine.record_from_table_query(
            table=table,
            name=cleaned_name,
            team=cleaned_team,
            version=version,
            uid=uid,
            max_date=max_date,
            tags=tags,
        )

        records = self.get_sql_records(query=query)
        sorted_records = self.sort_by_version(records=records)

        if version is not None:
            if ignore_release_candidates:
                sorted_records = [
                    record for record in sorted_records if not SemVerUtils.is_release_candidate(record["version"])
                ]
            if any(symbol in version for symbol in [SemVerSymbols.CARET, SemVerSymbols.TILDE]):
                # return top version
                return sorted_records[:1]

        if version is None and ignore_release_candidates:
            sorted_records = [
                record for record in sorted_records if not SemVerUtils.is_release_candidate(record["version"])
            ]

        return sorted_records[:limit]

    @log_card_change
    def _add_and_commit(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        sql_record = table(**card)

        with self.session() as sess:
            sess.add(sql_record)
            sess.commit()

        return card, "registered"

    @log_card_change
    def update_card_record(self, table: Type[REGISTRY_TABLES], card: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        record_uid = cast(str, card.get("uid"))

        with self.session() as sess:
            query = sess.query(table).filter(table.uid == record_uid)
            query.update(card)
            sess.commit()

        return card, "updated"

    def check_uid_exists(self, uid: str, table: Type[REGISTRY_TABLES]) -> bool:
        query = self.query_engine.uid_exists_query(uid=uid, table=table)

        with self.session() as sess:
            result = sess.scalars(query).first()  # type: ignore[attr-defined]
        return bool(result)

    def _get_versions_from_db(
        self,
        table: Type[REGISTRY_TABLES],
        name: str,
        team: str,
        version_to_search: Optional[str] = None,
    ) -> List[str]:
        """Query versions from Card Database

        Args:
            name:
                Card name
            team:
                Card team
            version_to_search:
                Version to search for
        Returns:
            List of versions
        """

        query = self.query_engine.create_version_query(
            table=table,
            name=name,
            version=version_to_search,
        )

        with self.session() as sess:
            results = sess.scalars(query).all()  # type: ignore[attr-defined]

        if bool(results):
            if results[0].team != team:
                raise ValueError("""Model name already exists for a different team. Try a different name.""")

            versions = [result.version for result in results]
            return SemVerUtils.sort_semvers(versions=versions)
        return []

    def set_version(
        self,
        table: Type[REGISTRY_TABLES],
        name: str,
        team: str,
        pre_tag: str,
        build_tag: str,
        version_type: VersionType,
        supplied_version: Optional[CardVersion] = None,
    ) -> str:
        """
        Sets a version following semantic version standards

        Args:
            name:
                Card name
            partial_version:
                Validated partial version to set. If None, will increment the latest version
            version_type:
                Type of version increment. Values are "major", "minor" and "patch

        Returns:
            Version string
        """

        ver_validator = SemVerRegistryValidator(
            version_type=version_type,
            version=supplied_version,
            name=name,
            pre_tag=pre_tag,
            build_tag=build_tag,
        )

        versions = self._get_versions_from_db(
            table=table,
            name=name,
            team=team,
            version_to_search=ver_validator.version_to_search,
        )

        return ver_validator.set_version(versions=versions)
