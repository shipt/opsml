from typing import Optional, List, Dict, Any
from semver import VersionInfo
from opsml.registry.cards import ArtifactCard
from opsml.helpers.exceptions import VersionError
from opsml.registry.sql.semver import SemVerSymbols, CardVersion, VersionType, SemVerUtils, SemVerRegistryValidator
from opsml.registry.sql.mixins import ServerMixin, ClientMixin


class CardVersionSetter:
    def set_version(
        self,
        name: str,
        team: str,
        pre_tag: str,
        build_tag: str,
        version_type: VersionType,
        supplied_version: Optional[CardVersion] = None,
    ) -> str:
        raise NotImplementedError

    def _validate_pre_build_version(self, version: Optional[str] = None) -> CardVersion:
        if version is None:
            raise ValueError("Cannot set pre-release or build tag without a version")
        card_version = CardVersion(version=version)

        if not card_version.is_full_semver:
            raise ValueError("Cannot set pre-release or build tag without a full major.minor.patch specified")

        return card_version

    def _validate_semver(self, name: str, team: str, version: CardVersion) -> None:
        """
        Validates version if version is manually passed to Card

        Args:
            name:
                Name of card
            team:
                Team of card
            version:
                Version of card
        Returns:
            `CardVersion`
        """
        if version.is_full_semver:
            records = self.list_cards(name=name, version=version.valid_version)
            if len(records) > 0:
                if records[0]["team"] != team:
                    raise ValueError("""Model name already exists for a different team. Try a different name.""")

                for record in records:
                    ver = VersionInfo.parse(record["version"])

                    if ver.prerelease is None and SemVerUtils.is_release_candidate(version.version):
                        raise VersionError(
                            "Cannot create a release candidate for an existing official version. %s" % version.version
                        )

                    if record["version"] == version.version:
                        raise VersionError("Version combination already exists. %s" % version.version)

    def set_card_version(
        self,
        card: ArtifactCard,
        version_type: VersionType,
        pre_tag: str,
        build_tag: str,
    ):
        """Sets a given card's version and uid

        Args:
            card:
                Card to set
            version_type:
                Type of version increment
        """

        card_version = None

        # validate pre-release and/or build tag
        if version_type in [VersionType.PRE, VersionType.BUILD, VersionType.PRE_BUILD]:
            card_version = self._validate_pre_build_version(version=card.version)

        # if DS specifies version and not release candidate
        if card.version is not None and version_type not in [VersionType.PRE, VersionType.PRE_BUILD]:
            # build tags are allowed with "official" versions
            if version_type == VersionType.BUILD:
                # check whether DS-supplied version has a build tag already
                if VersionInfo.parse(card.version).build is None:
                    card.version = self.set_version(
                        name=card.name,
                        supplied_version=card_version,
                        team=card.team,
                        version_type=version_type,
                        pre_tag=pre_tag,
                        build_tag=build_tag,
                    )

            card_version = CardVersion(version=card.version)
            if card_version.is_full_semver:
                self._validate_semver(name=card.name, team=card.team, version=card_version)
                return None

        version = self.set_version(
            name=card.name,
            supplied_version=card_version,
            team=card.team,
            version_type=version_type,
            pre_tag=pre_tag,
            build_tag=build_tag,
        )

        # for instances where tag is explicitly provided for major, minor, patch
        if version_type in [VersionType.MAJOR, VersionType.MINOR, VersionType.PATCH]:
            if len(pre_tag.split(".")) == 2:
                version = f"{version}-{pre_tag}"

            if len(build_tag.split(".")) == 2:
                version = f"{version}+{build_tag}"

        card.version = version

        return None

    @staticmethod
    def sort_by_version(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        versions = [record["version"] for record in records]
        sorted_versions = SemVerUtils.sort_semvers(versions)

        sorted_records = []
        for version in sorted_versions:
            for record in records:
                if record["version"] == version:
                    sorted_records.append(record)

        return sorted_records


class CardVersionSetterServer(ServerMixin, CardVersionSetter):
    def _get_versions_from_db(self, name: str, team: str, version_to_search: Optional[str] = None) -> List[str]:
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
            table=self._table,
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
            name=name,
            team=team,
            version_to_search=ver_validator.version_to_search,
        )

        return ver_validator.set_version(versions=versions)


class CardVersionSetterClient(ClientMixin, CardVersionSetter):
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
            route=self.routes.VERSION,
            json={
                "name": name,
                "team": team,
                "version": version_to_send,
                "version_type": version_type,
                "table_name": self.table_name,
                "pre_tag": pre_tag,
                "build_tag": build_tag,
            },
        )

        return data.get("version")
