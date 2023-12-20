from typing import Tuple

import pandas as pd
import pytest
from sklearn.base import BaseEstimator

from opsml.registry.cards import ModelCard
from opsml.registry.model.creator import ModelCreator, create_model
from opsml.registry.model.interfaces import SklearnModel
from opsml.registry.types import AllowedDataType


def _test_model_create_no_onnx(random_forest_classifier: Tuple[BaseEstimator, pd.DataFrame]):
    model: SklearnModel = random_forest_classifier
    modelcard = ModelCard(
        model=model,
        name="test_model",
        team="mlops",
        user_email="test_email",
        datacard_uids=["test_uid"],
    )

    model_return = create_model(modelcard=modelcard)


def test_onnx_model_to_onnx(random_forest_classifier: Tuple[BaseEstimator, pd.DataFrame]):
    model: SklearnModel = random_forest_classifier
    modelcard = ModelCard(
        model=model,
        name="test_model",
        team="mlops",
        user_email="test_email",
        datacard_uids=["test_uid"],
        to_onnx=True,
    )

    create_model(modelcard=modelcard)


def _test_model_creator(random_forest_classifier: Tuple[BaseEstimator, pd.DataFrame]):
    model, data = random_forest_classifier
    modelcard = ModelCard(
        trained_model=model,
        sample_input_data=data,
        name="test_model",
        team="mlops",
        user_email="test_email",
        datacard_uids=["test_uid"],
        to_onnx=True,
    )
    modelcard.trained_model = "Fail"
    modelcard.metadata.sample_data_type = AllowedDataType.PANDAS

    with pytest.raises(NotImplementedError):
        ModelCreator(modelcard=modelcard).create_model()

    with pytest.raises(NotImplementedError):
        ModelCreator.validate(True)
