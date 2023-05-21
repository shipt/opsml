import pytest
from pytest_lazyfixture import lazy_fixture
from unittest.mock import patch, MagicMock
import pandas as pd
from pydantic import ValidationError
from opsml.registry import DataCard, ModelCard, RunCard, PipelineCard
from opsml.pipelines.runner import PipelineRunner
import uuid
import tenacity
import json


def test_client(test_app):
    """Test settings"""

    response = test_app.get("/opsml/settings")

    assert response.status_code == 200
    assert response.json()["proxy"] == True


def test_debug(test_app):
    """Test debug path"""

    response = test_app.get("/opsml/debug")

    assert "tmp.db" in response.json()["url"]
    assert "mlruns" in response.json()["storage"]
    assert response.status_code == 200


def test_error(test_app):
    """Test error path"""

    response = test_app.get("/opsml/error")

    assert response.status_code == 500


@pytest.mark.parametrize(
    "data_splits, test_data",
    [
        (lazy_fixture("test_split_array"), lazy_fixture("test_df")),
    ],
)
def _test_register_data(api_registries, test_data, data_splits):
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

    df = registry.list_cards(name=data_card.name, team=data_card.team)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards(name=data_card.name)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards()
    assert isinstance(df, pd.DataFrame)

    with pytest.raises(tenacity.RetryError):
        registry._registry.table_name = "no_table"
        registry.list_cards()


def _test_semver_registry_list(api_registries, test_array):
    # create data card
    registry = api_registries.data

    data_card = DataCard(
        data=test_array,
        name="test_array",
        team="mlops",
        user_email="mlops.com",
    )

    registry.register_card(card=data_card)

    # version 2
    data_card = DataCard(
        data=test_array,
        name="test_array",
        team="mlops",
        user_email="mlops.com",
    )
    registry.register_card(card=data_card, version_type="major")

    for i in range(0, 12):
        data_card = DataCard(
            data=test_array,
            name="test_array",
            team="mlops",
            user_email="mlops.com",
        )
        registry.register_card(card=data_card)

    # should return 13 versions
    df = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="2.*.*",
    )
    assert df.shape[0] == 13

    df = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="^2.3.0",
    )
    assert df.shape[0] == 1

    df = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="~2.3.0",
    )
    assert df.shape[0] == 1


def _test_register_large_data(api_registries):
    import numpy as np

    # create a numpy 1d-array
    x = np.random.rand(500000, 100)
    size = (x.size * x.itemsize) / 1_000_000_000

    # create data card
    registry = api_registries.data

    data_card = DataCard(
        data=x,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
    )
    registry.register_card(card=data_card)

    loaded_card = registry.load_card(uid=data_card.uid)
    loaded_card.load_data()

    assert (loaded_card.data == x).all()
    assert loaded_card.data.shape == x.shape


def _test_run_card(linear_regression, api_registries):
    registry = api_registries.run

    run = RunCard(
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        datacard_uids=["test_uid"],
    )
    run.log_metric("test_metric", 10)
    run.log_metrics({"test_metric2": 20})
    assert run.get_metric("test_metric").value == 10
    assert run.get_metric("test_metric2").value == 20
    # save artifacts
    model, _ = linear_regression
    run.log_artifact("reg_model", artifact=model)
    assert run.artifacts.get("reg_model").__class__.__name__ == "LinearRegression"
    registry.register_card(card=run)

    loaded_card = registry.load_card(uid=run.uid)
    assert loaded_card.uid == run.uid


def _test_register_model(api_registries, sklearn_pipeline):
    model, data = sklearn_pipeline
    # create data card
    data_registry = api_registries.data

    data_card = DataCard(
        data=data,
        name="pipeline_data",
        team="mlops",
        user_email="mlops.com",
    )
    data_registry.register_card(card=data_card)

    model_card1 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
    )

    model_registry = api_registries.model
    model_registry.register_card(model_card1)

    loaded_card = model_registry.load_card(uid=model_card1.uid)
    loaded_card.load_trained_model()
    loaded_card.trained_model = model
    loaded_card.sample_input_data = data[0:1]

    assert getattr(loaded_card, "trained_model") is not None
    assert getattr(loaded_card, "sample_input_data") is not None

    model_card_custom = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
    )

    model_registry.register_card(card=model_card_custom, save_path="steven-test/models")
    assert "steven-test/models" in model_card_custom.uris.trained_model_uri

    model_card2 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=None,
    )

    with pytest.raises(ValueError):
        model_registry.register_card(card=model_card2)

    model_card3 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid="test_uid",
    )

    with pytest.raises(ValueError):
        model_registry.register_card(card=model_card3)

    with pytest.raises(ValidationError):
        model_card3 = ModelCard(
            trained_model=model,
            sample_input_data=None,
            name="pipeline_model",
            team="mlops",
            user_email="mlops.com",
            datacard_uid="test_uid",
        )


@pytest.mark.parametrize("test_data", [lazy_fixture("test_df")])
def _test_load_data_card(api_registries, test_data):
    data_name = "test_df"
    team = "mlops"
    user_email = "mlops.com"

    registry = api_registries.data

    data_split = [
        {"label": "train", "column": "year", "column_value": 2020},
        {"label": "test", "column": "year", "column_value": 2021},
    ]

    data_card = DataCard(
        data=test_data,
        name=data_name,
        team=team,
        user_email=user_email,
        data_splits=data_split,
        additional_info={"input_metadata": 20},
        dependent_vars=[200, "test"],
    )

    data_card.add_info(info={"added_metadata": 10})
    registry.register_card(card=data_card)
    loaded_data: DataCard = registry.load_card(name=data_name, team=team, version=data_card.version)

    loaded_data.load_data()

    assert int(loaded_data.additional_info["input_metadata"]) == 20
    assert int(loaded_data.additional_info["added_metadata"]) == 10
    assert isinstance(loaded_data.dependent_vars[0], int)
    assert isinstance(loaded_data.dependent_vars[1], str)
    assert bool(loaded_data)

    # update
    loaded_data.version = "1.2.0"
    registry.update_card(card=loaded_data)

    record = registry.query_value_from_card(uid=loaded_data.uid, columns=["version", "timestamp"])
    assert record["version"] == "1.2.0"

    # test assertion error
    with pytest.raises(ValueError):
        data_card = DataCard(
            name=data_name,
            team=team,
            user_email=user_email,
            data_splits=data_split,
            additional_info={"input_metadata": 20},
            dependent_vars=[200, "test"],
        )

    # load card again
    loaded_data: DataCard = registry.load_card(name=data_name, team=team, version="1.2.0")
    loaded_data.data_uri = "fail"

    with pytest.raises(tenacity.RetryError):
        loaded_data.load_data()


def _test_pipeline_registry(api_registries):
    pipeline_card = PipelineCard(
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        pipeline_code_uri="test_pipe_uri",
    )
    for card_type in ["data", "run", "model"]:
        pipeline_card.add_card_uid(uid=uuid.uuid4().hex, card_type=card_type)

    # register
    registry = api_registries.pipeline
    registry.register_card(card=pipeline_card)
    loaded_card: PipelineCard = registry.load_card(uid=pipeline_card.uid)
    loaded_card.add_card_uid(uid="updated_uid", card_type="data")
    registry.update_card(card=loaded_card)
    df = registry.list_cards(uid=loaded_card.uid)
    values = registry.query_value_from_card(
        uid=loaded_card.uid,
        columns=["datacard_uids"],
    )
    assert bool(values["datacard_uids"])


def _test_full_pipeline_with_loading(api_registries, linear_regression):
    from opsml.registry.cards.pipeline_loader import PipelineLoader

    team = "mlops"
    user_email = "mlops.com"
    pipeline_code_uri = "test_pipe_uri"
    data_registry = api_registries.data
    model_registry = api_registries.model
    run_registry = api_registries.run
    pipeline_registry = api_registries.pipeline
    model, data = linear_regression

    #### Create DataCard
    data_card = DataCard(
        data=data,
        name="test_data",
        team=team,
        user_email=user_email,
    )

    data_registry.register_card(card=data_card)
    ###### ModelCard
    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[:1],
        name="test_model",
        team=team,
        user_email=user_email,
        datacard_uid=data_card.uid,
    )

    model_registry.register_card(model_card)

    ##### RunCard
    run = RunCard(
        name="test_experiment",
        team=team,
        user_email=user_email,
        datacard_uids=[data_card.uid],
        modelcard_uids=[model_card.uid],
    )
    run.log_metric("test_metric", 10)
    run_registry.register_card(card=run)
    #### PipelineCard
    pipeline_card = PipelineCard(
        name="test_pipeline",
        team=team,
        user_email=user_email,
        pipeline_code_uri=pipeline_code_uri,
        datacard_uids=[data_card.uid],
        modelcard_uids=[model_card.uid],
        runcard_uids=[run.uid],
    )
    pipeline_registry.register_card(card=pipeline_card)

    loader = PipelineLoader(pipelinecard_uid=pipeline_card.uid)
    uids = loader.card_uids

    assert uids["data"][0] == data_card.uid
    assert uids["run"][0] == run.uid
    assert uids["model"][0] == model_card.uid


def _test_download_model(test_app, api_registries, linear_regression):
    team = "mlops"
    user_email = "mlops.com"

    model, data = linear_regression

    data_registry = api_registries.data
    model_registry = api_registries.model

    #### Create DataCard
    data_card = DataCard(
        data=data,
        name="test_data",
        team=team,
        user_email=user_email,
    )

    data_registry.register_card(card=data_card)
    ###### ModelCard
    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[:1],
        name="test_model",
        team=team,
        user_email=user_email,
        datacard_uid=data_card.uid,
    )

    model_registry.register_card(model_card)

    result = ""
    with test_app.stream(method="POST", url="opsml/download_model_metadata", json={"uid": model_card.uid}) as response:
        for data in response.iter_bytes():
            result += data.decode("utf-8")

    model_def = json.loads(result)

    assert model_def["model_name"] == model_card.name
    assert model_def["model_version"] == model_card.version
    assert response.status_code == 200


def test_download_model_failure(test_app):
    response = test_app.post(url="opsml/download_model_metadata", json={"name": "pip"})

    # should fail
    assert response.status_code == 500
    assert response.json()["detail"] == "No model found"


def test_submit_pipeline(
    test_app,
    mock_gcp_storage_settings,
    mock_packager,
    mock_gcp_pipelinejob,
    mock_gcp_scheduler,
):
    runner = PipelineRunner(spec_filename="vertex-example-spec.yaml")

    response = test_app.post(
        url="opsml/submit_pipeline",
        json={
            "specs": runner.specs.dict(),
            "tasks": runner.task_dict,
            "schedule": True,
        },
    )

    assert response.status_code == 200
