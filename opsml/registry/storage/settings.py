# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from functools import cached_property
from typing import Any, Optional, Type, cast

import httpx

from opsml.helpers.logging import ArtifactLogger
from opsml.helpers.request_helpers import ApiClient, api_routes
from opsml.helpers.utils import OpsmlImportExceptions
from opsml.registry.sql.connectors.base import BaseSQLConnection
from opsml.registry.sql.connectors.connector import SQLConnector
from opsml.registry.storage.storage_system import StorageSystem, get_storage_client
from opsml.registry.storage.types import (
    ApiStorageClientSettings,
    GcsStorageClientSettings,
    S3StorageClientSettings,
    StorageClientSettings,
    StorageSettings,
)
from opsml.settings.config import OpsmlConfig, config

logger = ArtifactLogger.get_logger()


class StorageSettingsGetter:
    def __init__(
        self,
        storage_uri: Optional[str] = None,
        storage_type: str = StorageSystem.LOCAL.value,
        api_client: Optional[ApiClient] = None,
    ):
        self.storage_uri = storage_uri
        self.storage_type = storage_type
        self.api_client = api_client

    def _get_gcs_settings(self) -> GcsStorageClientSettings:
        from opsml.helpers.gcp_utils import (  # pylint: disable=import-outside-toplevel
            GcpCredsSetter,
        )

        gcp_creds = GcpCredsSetter().get_creds()

        return GcsStorageClientSettings(
            storage_type=self.storage_type,
            storage_uri=self.storage_uri,
            gcp_project=gcp_creds.project,
            credentials=gcp_creds.creds,
        )

    def _get_api_storage_settings(self) -> ApiStorageClientSettings:
        """Returns storage settings for using Api storage class"""
        assert self.api_client is not None
        return ApiStorageClientSettings(
            storage_type=self.storage_type,
            storage_uri=self.storage_uri,
            api_client=self.api_client,
        )

    def _get_s3_settings(self) -> S3StorageClientSettings:
        return S3StorageClientSettings(
            storage_type=self.storage_type,
            storage_uri=self.storage_uri,
        )

    def _get_default_settings(self) -> StorageClientSettings:
        return StorageClientSettings(
            storage_uri=self.storage_uri,
            storage_type=self.storage_type,
        )

    def get_storage_settings(self) -> StorageSettings:
        if self.storage_type == StorageSystem.GCS:
            return self._get_gcs_settings()

        if self.storage_type == StorageSystem.API:
            return self._get_api_storage_settings()

        if self.storage_type == StorageSystem.S3:
            return self._get_s3_settings()

        if self.storage_uri is not None:
            return self._get_default_settings()

        return StorageClientSettings()


class _DefaultAttrCreator:
    @staticmethod
    def get_request_client(cfg: OpsmlConfig) -> Optional[ApiClient]:
        if cfg.is_tracking_local:
            # Needs the [server] extra installed
            OpsmlImportExceptions.try_sql_import()
            logger.info("""No tracking url set. Defaulting to Sqlite""")
            return None

        username = cfg.opsml_username
        password = cfg.OPSML_PASSWORD

        request_client = ApiClient(cfg=cfg, base_url=cfg.opsml_tracking_uri.strip("/"))
        if all(bool(cred) for cred in [username, password]):
            request_client.client.auth = httpx.BasicAuth(
                username=str(username),
                password=str(password),
            )
        return request_client

    @staticmethod
    def get_storage_settings(cfg: OpsmlConfig, client: Optional[ApiClient]) -> StorageSettings:
        if client is not None:
            storage_settings = client.get_request(route=api_routes.SETTINGS)
            storage_uri = cast(str, storage_settings.get("storage_uri"))
            storage_type = cast(str, storage_settings.get("storage_type"))
        else:
            storage_uri = cfg.opsml_storage_uri
            storage_type = _DefaultAttrCreator._get_storage_type(storage_uri)

        storage_settings = StorageSettingsGetter(
            storage_uri=storage_uri,
            storage_type=storage_type,
            api_client=client,
        ).get_storage_settings()

        return storage_settings

    @staticmethod
    def _get_storage_type(storage_uri: str) -> str:
        if "gs://" in storage_uri:
            return StorageSystem.GCS.value
        if "s3://" in storage_uri:
            return StorageSystem.S3.value
        return StorageSystem.LOCAL.value


class DefaultConnector:
    def __init__(
        self,
        tracking_uri: str,
        credentials: Optional[Any] = None,
    ):
        self.tracking_uri = tracking_uri
        self.credentials = credentials

    def _get_connector_type(self) -> str:
        """Gets the sql connection type when running opsml locally (without api proxy)"""

        connector_type = "local"
        for db_type in ["postgresql", "mysql"]:
            if db_type in self.tracking_uri:
                connector_type = db_type

        if "cloudsql" in self.tracking_uri:
            connector_type = f"cloudsql_{connector_type}"

        return connector_type

    def _get_sql_connector(self, connector_type: str) -> Type[BaseSQLConnection]:
        """Gets the sql connection given a connector type"""
        return SQLConnector.get_connector(connector_type=connector_type)

    def get_connector(self) -> Type[BaseSQLConnection]:
        """Gets the sql connector to use when running opsml locally (without api proxy)"""
        connector_type = self._get_connector_type()
        connector = self._get_sql_connector(connector_type=connector_type)

        return cast(
            Type[BaseSQLConnection],
            connector(
                tracking_uri=self.tracking_uri,
                credentials=self.credentials,
            ),
        )


class DefaultSettings:
    """Opsml settings"""

    def __init__(self, cfg: OpsmlConfig) -> None:
        self.cfg = cfg

        self.request_client = _DefaultAttrCreator.get_request_client(self.cfg)
        self.storage_settings = _DefaultAttrCreator.get_storage_settings(self.cfg, self.request_client)

    @property
    def storage_settings(self) -> StorageSettings:
        return self._storage_settings

    @storage_settings.setter
    def storage_settings(self, storage_settings: StorageSettings) -> None:
        self._storage_settings = storage_settings
        self.storage_client = get_storage_client(self._storage_settings)

    @cached_property
    def connection_client(self) -> Type[BaseSQLConnection]:
        """Retrieve sql connection client.
        Connection client is only used in the Registry class.
        """
        return DefaultConnector(
            tracking_uri=self.cfg.opsml_tracking_uri,
            credentials=None,
        ).get_connector()


settings = DefaultSettings(cfg=config)
