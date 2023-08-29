# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import Any, Dict, List
from contextlib import _GeneratorContextManager
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import Select
from opsml.registry.sql.settings import settings
from opsml.registry.sql.query_helpers import QueryEngine  # type: ignore
from opsml.helpers.request_helpers import api_routes, ApiRoutes


class ClientMixin:
    @property
    def session(self):
        return settings.request_client

    @property
    def routes(self) -> ApiRoutes:
        return api_routes


class ServerMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query_engine = QueryEngine()

    def session(self) -> _GeneratorContextManager[Session]:
        return self.query_engine.session()

    def _create_table_if_not_exists(self):
        engine = self.query_engine._get_engine()
        self._table.__table__.create(bind=engine, checkfirst=True)

    def _parse_sql_results(self, results: Any) -> List[Dict[str, Any]]:
        """
        Helper for parsing sql results

        Args:
            results:
                Returned object sql query

        Returns:
            List of dictionaries
        """
        records: List[Dict[str, Any]] = []

        for row in results:
            result_dict = row[0].__dict__
            result_dict.pop("_sa_instance_state")
            records.append(result_dict)

        return records

    def get_sql_records(self, query: Select) -> List[Dict[str, Any]]:
        """
        Gets sql records from database given a query

        Args:
            query:
                sql query
        Returns:
            List of records
        """

        with self.session() as sess:
            results = sess.execute(query).all()

        records = self._parse_sql_results(results=results)

        return records
