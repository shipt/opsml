from typing import Any, cast, Dict, Tuple

import os
import sys

import pandas as pd
from numpy.typing import NDArray
import pytest
from sklearn import pipeline
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import shutil
from opsml.registry import DataCard, ModelCard
from opsml.registry.cards.types import CardInfo
from opsml.projects.mlflow import MlflowProject, ProjectInfo, MlflowActiveRun
from opsml.projects import OpsmlProject, ProjectInfo
from opsml.helpers.logging import ArtifactLogger
from tests import conftest
import matplotlib
import torch

matplotlib.use("Agg")

logger = ArtifactLogger.get_logger(__name__)


@pytest.mark.skipif(sys.platform == "darwin", reason="Not supported on apple silicon")
def test_tf_model(
    mlflow_project: MlflowProject,
    load_multi_input_keras_example: tuple[Any, Dict[str, NDArray]],
):
    # another run (pytorch)
    info = ProjectInfo(name="test-exp", team="test", user_email="user@test.com")
    with mlflow_project.run() as run:
        model, data = load_multi_input_keras_example

        data_card = DataCard(
            data=data["title"],
            name="sample_input",
            team="mlops",
            user_email="mlops.com",
        )
        run.register_card(card=data_card)
        model_card = ModelCard(
            trained_model=model,
            sample_input_data=data,
            name="multi_model",
            team="mlops",
            user_email="mlops.com",
            datacard_uid=data_card.uid,
        )
        run.register_card(card=model_card)
        info.run_id = run.run_id
    proj = conftest.mock_mlflow_project(info)
    loaded_card: ModelCard = proj.load_card(
        registry_name="model",
        info=CardInfo(uid=model_card.uid),
    )
    loaded_card.load_trained_model()
