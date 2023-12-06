# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
from typing import Optional

BASE_LOCAL_SQL = f"sqlite:///{os.getcwd()}/tmp.db"
TRACKING_URI = os.environ.get("OPSML_TRACKING_URI", BASE_LOCAL_SQL)
STORAGE_URI = os.environ.get("OPSML_STORAGE_URI", f"{os.getcwd()}/mlruns")


class OpsmlConfig:
    APP_NAME = "OPSML-API"
    APP_ENV = os.environ.get("APP_ENV", "development")
    STORAGE_URI = STORAGE_URI
    TRACKING_URI = TRACKING_URI
    PROD_TOKEN = os.environ.get("OPSML_PROD_TOKEN", "staging")

    def __init__(self) -> None:
        self._proxy_root = os.environ.get("PROXY_ROOT")
        self._is_proxy = True

    @property
    def proxy_root(self) -> Optional[str]:
        return self._proxy_root

    @proxy_root.setter
    def proxy_root(self, root: str) -> None:
        self._proxy_root = root

    @property
    def is_proxy(self) -> bool:
        return self._is_proxy

    @is_proxy.setter
    def is_proxy(self, proxy: bool) -> None:
        self._is_proxy = proxy


config = OpsmlConfig()
