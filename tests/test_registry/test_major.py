from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import polars as pl
from numpy.typing import NDArray
import pyarrow as pa
from os import path
from unittest.mock import patch
import pytest
from pytest_lazyfixture import lazy_fixture
from opsml.registry.cards.cards import DataCard, RunCard, PipelineCard, ModelCard, DataSplit
from opsml.registry.cards.pipeline_loader import PipelineLoader
from opsml.registry.sql.registry import CardRegistry
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from sklearn.pipeline import Pipeline
import uuid
from pydantic import ValidationError
from tests.conftest import FOURTEEN_DAYS_TS, FOURTEEN_DAYS_STR


def test_datacard_major_minor_version(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        sql_logic={"test": "select * from test_table"},
        version="3.1.1",
    )

    registry.register_card(card=data_card)
    print(data_card.version)

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.1",
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="patch")
