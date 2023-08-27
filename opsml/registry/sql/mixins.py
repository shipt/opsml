# type: ignore
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import Iterator
from sqlalchemy.orm.session import Session
from opsml.registry.sql.settings import settings
from opsml.registry.sql.query_helpers import QueryEngine
from opsml.helpers.request_helpers import api_routes


class ClientMixin:
    def __init__(self):
        self.routes = api_routes

    @property
    def _session(self):
        return settings.request_client


class ServerMixin:
    def __init__(self):
        self.query_engine = QueryEngine()

    def session(self) -> Iterator[Session]:
        return self.query_engine.session()
