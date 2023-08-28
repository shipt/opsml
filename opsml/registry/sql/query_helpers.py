# type: ignore
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import datetime
from functools import wraps
from typing import Any, Dict, Iterable, Optional, Type, Union, cast

from contextlib import contextmanager, _GeneratorContextManager
from sqlalchemy.orm.session import Session
from sqlalchemy import select
from sqlalchemy.sql import FromClause, Select
from sqlalchemy.sql.expression import ColumnElement

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.sql.registry_helpers.semver import get_version_to_search
from opsml.registry.sql.sql_schema import REGISTRY_TABLES, TableSchema
from opsml.registry.sql.settings import settings

logger = ArtifactLogger.get_logger(__name__)

SqlTableType = Optional[Iterable[Union[ColumnElement[Any], FromClause, int]]]
YEAR_MONTH_DATE = "%Y-%m-%d"


class QueryEngine:
    def _get_engine(self):
        return settings.connection_client.get_engine()

    @contextmanager  # type: ignore
    def session(self) -> _GeneratorContextManager[Session]:
        engine = self._get_engine()

        with Session(engine) as sess:  # type: ignore
            yield sess

    def create_version_query(
        self,
        table: Type[REGISTRY_TABLES],
        name: str,
        version: Optional[str] = None,
    ) -> Select:
        """Creates query to get latest card version

        Args:
            table:
                Registry table to query
            name:
                Name of the card
            version:
                Version of the card
        Returns:
            Query to get latest card version
        """
        table_select = select(table).filter(table.name == name)

        if version is not None:
            table_select = table_select.filter(table.version.like(f"{version}%"))

        return table_select.order_by(table.timestamp.desc(), table.version.desc()).limit(20)  # type: ignore

    # TODO: refactor
    def record_from_table_query(
        self,
        table: Type[REGISTRY_TABLES],
        uid: Optional[str] = None,
        name: Optional[str] = None,
        team: Optional[str] = None,
        version: Optional[str] = None,
        max_date: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Select:
        """
        Creates a sql query based on table, uid, name, team and version

        Args:
            table:
                Registry table to query
            uid:
                Optional unique id of Card
            name:
                Optional name of Card
            team:
                Optional team name
            version:
                Optional version of Card
            tags:
                Optional card tags
            max_date:
                Optional max date to search

        Returns
            Sqlalchemy Select statement
        """

        query = self._get_base_select_query(table=table)
        if bool(uid):
            return query.filter(table.uid == uid)

        filters = []
        for field, value in zip(["name", "team", "version"], [name, team, version]):
            if value is not None:
                if field == "version":
                    version = get_version_to_search(version=version)
                    filters.append(getattr(table, field).like(f"{version}%"))

                else:
                    filters.append(getattr(table, field) == value)

        if max_date is not None:
            max_date_ts = self._get_epoch_time_to_search(max_date=max_date)
            filters.append(getattr(table, "timestamp") <= max_date_ts)

        if tags is not None:
            for key, value in tags.items():
                filters.append(table.tags[key].as_string() == value)

        if bool(filters):
            query = query.filter(*filters)

        query = query.order_by(table.version.desc(), table.timestamp.desc())  # type: ignore

        return query

    def _get_epoch_time_to_search(self, max_date: str):
        """
        Creates timestamp that represents the max epoch time to limit records to

        Args:
            max_date:
                max date to search

        Returns:
            time stamp as integer related to `max_date`
        """
        converted_date = datetime.datetime.strptime(max_date, YEAR_MONTH_DATE)
        max_date = converted_date.replace(hour=23, minute=59, second=59)  # provide max values for a date

        # opsml timestamp records are stored as BigInts
        return int(round(max_date.timestamp() * 1_000_000))

    def _get_base_select_query(self, table: Type[REGISTRY_TABLES]) -> Select:
        sql_table = cast(SqlTableType, table)
        return cast(Select, select(sql_table))

    def uid_exists_query(self, uid: str, table_to_check: str) -> Select:
        table = TableSchema.get_table(table_name=table_to_check)
        query = self._get_base_select_query(table=table.uid)  # type: ignore
        query = query.filter(table.uid == uid)

        return cast(Select, query)


def log_card_change(func):
    """Decorator for logging card changes"""

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> None:
        card, state = func(self, *args, **kwargs)
        name = str(card.get("name"))
        version = str(card.get("version"))
        logger.info(
            "%s: %s, version:%s %s", self._table.__tablename__, name, version, state  # pylint: disable=protected-access
        )

    return wrapper
