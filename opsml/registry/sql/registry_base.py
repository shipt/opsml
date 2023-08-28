# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import Any, Dict, Iterable, List, Optional, Union
from sqlalchemy.sql.expression import ColumnElement, FromClause
from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.utils import clean_string
from opsml.registry.cards.card_saver import save_card_artifacts
from opsml.registry.cards import (
    ArtifactCard,
    DataCard,
    ModelCard,
    PipelineCard,
    RunCard,
)
from opsml.registry.sql.records import LoadedRecordType, load_record
from opsml.registry.sql.registry_helpers.semver import VersionType
from opsml.registry.sql.registry_helpers.card_registry import registry_helper
from opsml.registry.sql.sql_schema import RegistryTableNames, TableSchema

logger = ArtifactLogger.get_logger(__name__)

# Set up sql
SqlTableType = Optional[Iterable[Union[ColumnElement[Any], FromClause, int]]]

table_name_card_map = {
    RegistryTableNames.DATA.value: DataCard,
    RegistryTableNames.MODEL.value: ModelCard,
    RegistryTableNames.RUN.value: RunCard,
    RegistryTableNames.PIPELINE.value: PipelineCard,
}


###################### Attention ######################
# Registry classes should only expose list, load, register and update methods
# Private methods should ideally be independent classes that are called by these 4 methods
# This is done to decouple code and make a better user experience
########################################################


def load_card_from_record(
    table_name: str,
    record: LoadedRecordType,
) -> ArtifactCard:
    """
    Loads an artifact card given a tablename and the loaded record
    from backend database

    Args:
        table_name:
            Name of table
        record:
            Loaded record from backend database

    Returns:
        `ArtifactCard`
    """

    card = table_name_card_map[table_name]
    return card(**record.model_dump())


class Registry:
    def __init__(self, table_name: str):
        """
        Base class for SQL Registries to inherit from

        Args:
            table_name:
                CardRegistry table name
        """

        self.supported_card = f"{table_name.split('_')[1]}Card"
        self._table = TableSchema.get_table(table_name=table_name)

    @property
    def table_name(self) -> str:
        return self._table.__tablename__

    def register_card(
        self,
        card: ArtifactCard,
        version_type: VersionType = VersionType.MINOR,
        pre_tag: str = "rc",
        build_tag: str = "build",
    ) -> None:
        """
        Adds new record to registry.

        Args:
            card:
                card to register
            version_type:
                Version type for increment. Options are "major", "minor" and
                "patch". Defaults to "minor".
            pre_tag:
                pre-release tag to add to card version
            build_tag:
                build tag to add to card version
        """

        registry_helper.validator.validate_card_type(table_name=self.table_name, card=card)
        registry_helper.card_ver.set_card_version(
            table=self._table,
            card=card,
            version_type=version_type,
            pre_tag=pre_tag,
            build_tag=build_tag,
        )

        registry_helper.validator.set_card_uid(card=card)
        registry_helper.storage.set_artifact_storage_spec(table_name=self.table_name, card=card)
        registry_helper.create_registry_record(
            table=self._table,
            card=card,
            storage_client=registry_helper.storage.storage_client,
        )

    def update_card(self, card: ArtifactCard) -> None:
        """
        Update an artifact card based on current registry

        Args:
            card:
                Card to register
        """
        card = save_card_artifacts(
            card=card,
            storage_client=registry_helper.storage.storage_client,
        )
        record = card.create_registry_record()
        registry_helper.update_card_record(
            table=self._table,
            card=record.model_dump(),
        )

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
    ) -> List[Dict[str, Any]]:
        """Retrieves records from registry

        Args:
            name:
                Card name
            team:
                Team associated with card
            version:
                Optional version number of existing data. If not specified, the
                most recent version will be used
            tags:
                Dictionary of key, value tags to search for
            uid:
                Unique identifier for Card. If present, the uid takes precedence
            max_date:
                Max date to search. (e.g. "2023-05-01" would search for cards up to and including "2023-05-01")
            limit:
                Places a limit on result list. Results are sorted by SemVer
            as_dataframe:
                If True, returns a pandas dataframe. If False, returns a list of records
            info:
                CardInfo object. If present, the info object takes precedence

        Returns:
            pandas dataframe of records or list of dictionaries
        """

        return registry_helper.list_cards(
            table=self._table,
            uid=uid,
            name=name,
            team=team,
            version=version,
            tags=tags,
            max_date=max_date,
            limit=limit,
            ignore_release_candidates=ignore_release_candidates,
        )

    def load_card(
        self,
        name: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        uid: Optional[str] = None,
        ignore_release_candidates: bool = False,
    ) -> ArtifactCard:
        """Loads a specific card

        Args:
            name:
                Optional Card name
            uid:
                Unique identifier for card. If present, the uid takes
                precedence.
            tags:
                Optional tags associated with model.
            version:
                Optional version number of existing data. If not specified, the
                most recent version will be used
            info:
                Optional CardInfo object. If present, the info takes precedence

        Returns
            ArtifactCard
        """
        cleaned_name = clean_string(name)

        record = self.list_cards(
            name=cleaned_name,
            version=version,
            uid=uid,
            limit=1,
            tags=tags,
            ignore_release_candidates=ignore_release_candidates,
        )

        loaded_record = load_record(
            table_name=self.table_name,
            record_data=record[0],
            storage_client=registry_helper.storage.storage_client,
        )

        return load_card_from_record(
            table_name=self.table_name,
            record=loaded_record,
        )

    def query_value_from_card(self, uid: str, columns: List[str]) -> Dict[str, Any]:
        """
        Query column values from a specific Card

        Args:
            uid:
                Uid of Card
            columns:
                List of columns to query

        Returns:
            Dictionary of column, values pairs
        """
        results = registry_helper.list_cards(uid=uid)[0]
        return {col: results[col] for col in columns}

    @staticmethod
    def validate(registry_name: str) -> bool:
        raise NotImplementedError
