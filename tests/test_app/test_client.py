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
from opsml.app.routes.utils import list_team_name_info
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

    df = registry.list_cards(name=data_card.name, team=data_card.team, max_date=TODAY_YMD, as_dataframe=True)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards(name=data_card.name, as_dataframe=True)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards(as_dataframe=True)
    assert isinstance(df, pd.DataFrame)

    with pytest.raises(AttributeError):
        registry._registry.table_name = "no_table"


def test_list_teams(
    api_registries: CardRegistries,
):
    registry = api_registries.data
    teams = registry.list_teams()
    assert len(teams) == 1
    assert teams[0] == "mlops"


def test_list_card_names(
    api_registries: CardRegistries,
):
    # create data card
    registry = api_registries.data
    names = registry.list_card_names(team="mlops")
    assert len(names) == 1
    assert names[0] == "test-df"

    names = registry.list_card_names()
    assert len(names) == 1
    assert names[0] == "test-df"


def test_list_team_info(
    api_registries: CardRegistries,
):
    registry = api_registries.data
    info = list_team_name_info(registry=registry, team="mlops")
    assert info.names[0] == "test-df"
    assert info.teams[0] == "mlops"

    info = list_team_name_info(registry=registry)
    assert info.names[0] == "test-df"


def test_register_major_minor(api_registries: CardRegistries, test_array: NDArray):
    # create data card
    registry = api_registries.data

    data_card = DataCard(
        data=test_array,
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.1.1",
    )

    registry.register_card(card=data_card)

    data_card = DataCard(
        data=test_array,
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.1",
    )

    registry.register_card(card=data_card, version_type="patch")
    assert data_card.version == "3.1.2"

    data_card = DataCard(
        data=test_array,
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.1",
    )

    registry.register_card(card=data_card, version_type="minor")
    assert data_card.version == "3.2.0"


def test_semver_registry_list(api_registries: CardRegistries, test_array: NDArray):
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
    cards = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="2.*.*",
    )
    assert len(cards) == 13

    cards = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="^2.3.0",
    )
    assert len(cards) == 1

    cards = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="~2.3.0",
    )
    assert len(cards) == 1


def test_run_card(
    linear_regression: Tuple[linear_model.LinearRegression, pd.DataFrame],
    api_registries: CardRegistries,
):
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


def test_register_model(
    api_registries: CardRegistries,
    sklearn_pipeline: Tuple[pipeline.Pipeline, pd.DataFrame],
):
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
        tags={"id": "model1"},
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

    model_registry.register_card(card=model_card_custom)
    assert "pipeline-model" in model_card_custom.uris.trained_model_uri

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

    # test card tags
    cards = model_registry.list_cards(
        name=model_card1.name,
        team=model_card1.team,
        tags=model_card1.tags,
    )

    assert cards[0]["tags"] == {"id": "model1"}


@pytest.mark.parametrize("test_data", [lazy_fixture("test_df")])
def test_load_data_card(api_registries: CardRegistries, test_data: pd.DataFrame):
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
    loaded_data: DataCard = registry.load_card(name=data_name, version=data_card.version)

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
    datacardv12: DataCard = registry.load_card(name=data_name, version="1.2.0")
    datacardv12.uris.data_uri = "fail"

    with pytest.raises(FileNotFoundError):
        datacardv12.load_data()


def test_pipeline_registry(api_registries: CardRegistry):
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


def test_full_pipeline_with_loading(
    api_registries: CardRegistries,
    linear_regression: Tuple[linear_model.LinearRegression, pd.DataFrame],
):
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


def test_metadata_download_and_registration(
    test_app: TestClient,
    api_registries: CardRegistries,
    linear_regression: Tuple[linear_model.LinearRegression, pd.DataFrame],
):
    team = "mlops"
    user_email = "test@mlops.com"

    model, data = linear_regression

    data_registry = api_registries.data
    model_registry = api_registries.model

    data_card = DataCard(
        data=data,
        name="test_data",
        team=team,
        user_email=user_email,
    )

    data_registry.register_card(card=data_card)

    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[:1],
        name="test_model",
        team=team,
        user_email=user_email,
        datacard_uid=data_card.uid,
    )

    model_registry.register_card(model_card)

    response = test_app.post(
        url=f"opsml/{ApiRoutes.MODEL_METADATA}",
        json={"uid": model_card.uid},
    )
    assert response.status_code == 200

    model_def = response.json()

    assert model_def["model_name"] == model_card.name
    assert model_def["model_version"] == model_card.version

    # test register model (onnx)
    response = test_app.post(
        url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
        json={"name": model_card.name, "version": model_card.version},
    )
    # NOTE: the *exact* model version sent must be returned in the URL.
    # Otherwise the hosting infrastructure will not know where to find the URL
    # as they do *not* use the response text, rather they assume the URL is in
    # the correct format.
    uri = response.json()
    assert re.search(rf"/model_registry/test-model/v{model_card.version}$", uri, re.IGNORECASE) is not None

    # test register model (native)
    response = test_app.post(
        url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
        json={
            "name": model_card.name,
            "version": model_card.version,
            "onnx": "false",
        },
    )
    uri = response.json()
    assert re.search(rf"/model_registry/test-model/v{model_card.version}$", uri, re.IGNORECASE) is not None

    # test register model - latest patch given latest major.minor
    minor = model_card.version[0 : model_card.version.rindex(".")]
    response = test_app.post(
        url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
        json={
            "name": model_card.name,
            "version": minor,
        },
    )

    uri = response.json()
    assert re.search(rf"/model_registry/test-model/v{minor}$", uri, re.IGNORECASE) is not None

    # test register model - latest minor / patch given major only
    major = model_card.version[0 : model_card.version.index(".")]
    response = test_app.post(
        url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
        json={
            "name": model_card.name,
            "version": major,
        },
    )
    uri = response.json()
    assert re.search(rf"/model_registry/test-model/v{major}$", uri, re.IGNORECASE) is not None

    # test version fail - invalid name
    response = test_app.post(
        url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
        json={
            "name": "non-exist",
            "version": model_card.version,
        },
    )

    msg = response.json()["detail"]
    assert response.status_code == 404
    assert "Model not found" == msg

    # test version fail (does not match regex)
    response = test_app.post(
        url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
        json={
            "name": "non-exist",
            "version": "v1.0.0",  # version should *not* contain "v" - it must match the n.n.n pattern
        },
    )

    loc = response.json()["detail"][0]["loc"]  # "location" of pydantic failure
    assert response.status_code == 422
    assert "version" in loc

    # test model copy failure. This should result in a 500 - internal server
    # error. The model exists and is valid, but the internal copy failed.
    # Returning a 4xx (i.e., 404) is not the correct response.
    with patch(
        "opsml.registry.model.registrar.ModelRegistrar.is_registered",
        new_callable=MagicMock,
    ) as mock_registrar:
        mock_registrar.return_value = False
        response = test_app.post(
            url=f"opsml/{ApiRoutes.REGISTER_MODEL}",
            json={
                "name": model_card.name,
                "version": model_card.version,
            },
        )

        msg = response.json()["detail"]
        assert response.status_code == 500


def test_download_model_metadata_failure(test_app: TestClient):
    response = test_app.post(url=f"opsml/{ApiRoutes.MODEL_METADATA}", json={"name": "pip"})

    # should fail
    assert response.status_code == 404
    assert response.json()["detail"] == "Model not found"


def test_app_with_login(test_app_login: TestClient):
    """Test healthcheck with login"""

    response = test_app_login.get(
        "/opsml/healthcheck",
        auth=HTTPBasicAuth("test-user", "test-pass"),
    )

    assert response.status_code == 200


def test_model_metrics(
    test_app: TestClient,
    api_registries: CardRegistries,
    sklearn_pipeline: tuple[pipeline.Pipeline, pd.DataFrame],
) -> None:
    """ify that we can read artifacts / metrics / cards without making a run
    active."""

    model, data = sklearn_pipeline
    card_info = CardInfo(
        name="test_run",
        team="mlops",
        user_email="mlops.com",
    )

    runcard = RunCard(info=card_info)

    runcard.log_metric(key="m1", value=1.1)
    runcard.log_metric(key="mape", value=2, step=1)
    runcard.log_metric(key="mape", value=2, step=2)
    runcard.log_parameter(key="m1", value="apple")
    api_registries.run.register_card(runcard)

    #### Create DataCard
    datacard = DataCard(data=data, info=card_info)
    api_registries.data.register_card(datacard)

    #### Create ModelCard
    modelcard = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        info=card_info,
        datacard_uid=datacard.uid,
        runcard_uid=runcard.uid,
    )
    api_registries.model.register_card(modelcard)

    ### create second ModelCard
    #### Create ModelCard
    modelcard_2 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        info=card_info,
        datacard_uid=datacard.uid,
        runcard_uid=runcard.uid,
    )
    api_registries.model.register_card(modelcard_2)

    response = test_app.post(url=f"/opsml/{ApiRoutes.MODEL_METRICS}", json={"uid": modelcard.uid})

    metrics = response.json()

    assert metrics["metrics"]["m1"][0]["value"] == 1.1

    response = test_app.post(
        url=f"/opsml/{ApiRoutes.MODEL_METRICS}",
        json={
            "name": modelcard.name,
            "team": modelcard.team,
        },
    )

    assert response.status_code == 500


def test_model_metric_failure(
    test_app: TestClient,
    api_registries: CardRegistries,
    sklearn_pipeline: Tuple[pipeline.Pipeline, pd.DataFrame],
):
    model, data = sklearn_pipeline
    card_info = CardInfo(
        name="test_run",
        team="mlops",
        user_email="mlops.com",
    )

    #### Create DataCard
    datacard = DataCard(data=data, info=card_info)
    api_registries.data.register_card(datacard)

    #### Create ModelCard
    modelcard = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        info=card_info,
        datacard_uid=datacard.uid,
    )
    api_registries.model.register_card(modelcard)

    response = test_app.post(url=f"/opsml/{ApiRoutes.MODEL_METRICS}", json={"uid": modelcard.uid})
    assert response.status_code == 500


def test_token_fail(
    api_registries: CardRegistries,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(config.config, "PROD_TOKEN", "fail")

    run = RunCard(
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        datacard_uids=["test_uid"],
    )

    with pytest.raises(
        ValueError,
        match="Cannot perform write operation on prod resource without token",
    ):
        api_registries.run.register_card(card=run)
