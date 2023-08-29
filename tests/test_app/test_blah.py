from typing import Dict, List, Tuple

import re
import uuid

import pandas as pd
import pytest
from pytest_lazyfixture import lazy_fixture
from starlette.testclient import TestClient
from sklearn import linear_model, pipeline
from numpy.typing import NDArray
from pydantic import ValidationError
from requests.auth import HTTPBasicAuth

from opsml.registry import DataCard, ModelCard, RunCard, PipelineCard, CardRegistry, CardRegistries, CardInfo
from opsml.helpers.request_helpers import ApiRoutes
from opsml.app.core import config
from tests.conftest import TODAY_YMD
from unittest.mock import patch, MagicMock


def test_app_settings(test_app: TestClient):
    """Test settings"""

    response = test_app.get(f"/opsml/{ApiRoutes.SETTINGS}")

    assert response.status_code == 200
    assert response.json()["proxy"] == True


def test_debug(test_app: TestClient):
    """Test debug path"""

    response = test_app.get("/opsml/debug")

    assert "tmp.db" in response.json()["url"]
    assert "mlruns" in response.json()["storage"]
    assert response.status_code == 200


def test_error(test_app: TestClient):
    """Test error path"""

    response = test_app.get("/opsml/error")

    assert response.status_code == 500


@pytest.mark.parametrize(
    "data_splits, test_data",
    [
        (lazy_fixture("test_split_array"), lazy_fixture("test_df")),
    ],
)
def test_register_data(
    api_registries: CardRegistries,
    test_data: Tuple[pd.DataFrame, NDArray],
    data_splits: List[Dict[str, str]],
):
    # create data card
    registry = api_registries.data

    data_card = DataCard(
        data=test_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_splits=data_splits,
    )

    registry.register_card(card=data_card)
