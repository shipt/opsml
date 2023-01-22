import pandas as pd
import pytest
from pytest_lazyfixture import lazy_fixture
from opsml_artifacts.registry.cards.cards import DataCard, ExperimentCard, PipelineCard, ModelCard
from opsml_artifacts.registry.cards.pipeline_loader import PipelineLoader
from opsml_artifacts.registry.sql.registry import CardRegistry
import uuid
import random
from pydantic import ValidationError


@pytest.mark.parametrize(
    "data_splits, test_data",
    [
        (lazy_fixture("test_split_array"), lazy_fixture("test_array")),
        (lazy_fixture("test_split_array"), lazy_fixture("test_df")),
        (lazy_fixture("test_split_array"), lazy_fixture("test_arrow_table")),
    ],
)
def test_register_data(db_registries, test_data, storage_client, data_splits):

    # create data card
    registry = db_registries["data"]
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

    storage_client.delete_object_from_url(gcs_uri=data_card.data_uri)


def test_experiment_card(linear_regression, db_registries):

    registry: CardRegistry = db_registries["experiment"]

    experiment = ExperimentCard(
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_card_uid="test_uid",
    )

    experiment.add_metric("test_metric", 10)
    experiment.add_metrics({"test_metric2": 20})
    assert experiment.metrics.get("test_metric") == 10
    assert experiment.metrics.get("test_metric2") == 20

    # save artifacts
    model, _ = linear_regression

    experiment.add_artifact("reg_model", artifact=model)
    assert experiment.artifacts.get("reg_model").__class__.__name__ == "LinearRegression"

    registry.register_card(card=experiment)
    loaded_card = registry.load_card(uid=experiment.uid)
    assert loaded_card.uid == experiment.uid


def test_register_pipeline_model(db_registries, sklearn_pipeline, storage_client):

    model, data = sklearn_pipeline

    # create data card
    data_registry: CardRegistry = db_registries["data"]
    data_card = DataCard(
        data=data,
        name="pipeline_data",
        team="mlops",
        user_email="mlops.com",
    )
    data_registry.register_card(card=data_card)

    model_registry: CardRegistry = db_registries["model"]
    # for data_card_id in [data_card.uid, None, "test_uid"]:

    model_card1 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        data_card_uid=data_card.uid,
    )

    model_registry.register_card(card=model_card1)

    loaded_card = model_registry.load_card(uid=model_card1.uid)

    # test loading trained model
    loaded_card.load_trained_model()
    assert getattr(loaded_card, "trained_model") is not None
    assert getattr(loaded_card, "sample_input_data") is not None
    storage_client.delete_object_from_url(gcs_uri=model_card1.model_card_uri)

    model_card2 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        data_card_uid=None,
    )

    with pytest.raises(ValueError):
        model_registry.register_card(card=model_card2)

    model_card3 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        data_card_uid="test_uid",
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
            data_card_uid="test_uid",
        )


@pytest.mark.parametrize("test_data", [lazy_fixture("test_df")])
def test_data_card_splits(test_data):

    data_split = [
        {"label": "train", "column": "year", "column_value": 2020},
        {"label": "test", "column": "year", "column_value": 2021},
    ]

    data_card = DataCard(
        data=test_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_splits=data_split,
    )

    assert data_card.data_splits[0]["column"] == "year"
    assert data_card.data_splits[0]["column_value"] == 2020

    data_split = [
        {"label": "train", "start": 0, "stop": 2},
        {"label": "test", "start": 3, "stop": 4},
    ]

    data_card = DataCard(
        data=test_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_splits=data_split,
    )

    assert data_card.data_splits[0]["start"] == 0
    assert data_card.data_splits[0]["stop"] == 2


@pytest.mark.parametrize("test_data", [lazy_fixture("test_df")])
def test_load_data_card(db_registries, test_data, storage_client):
    data_name = "test_df"
    team = "mlops"
    user_email = "mlops.com"

    registry: CardRegistry = db_registries["data"]

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
    )

    registry.register_card(card=data_card)
    loaded_data = registry.load_card(name=data_name, team=team, version=data_card.version)

    # update
    loaded_data.version = 100
    registry.update_card(card=loaded_data)
    storage_client.delete_object_from_url(gcs_uri=loaded_data.data_uri)

    record = registry.query_value_from_card(uid=loaded_data.uid, columns=["version", "timestamp"])
    assert record["version"] == 100


def test_pipeline_registry(db_registries):

    pipeline_card = PipelineCard(
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        pipeline_code_uri="test_pipe_uri",
    )

    for card_type in ["data", "data", "model", "experiment"]:
        pipeline_card.add_card_uid(
            uid=uuid.uuid4().hex,
            card_type=card_type,
            name=f"{card_type}_{random.randint(0,100)}",
        )

    # register
    registry: CardRegistry = db_registries["pipeline"]
    registry.register_card(card=pipeline_card)

    loaded_card: PipelineCard = registry.load_card(uid=pipeline_card.uid)
    loaded_card.add_card_uid(uid="updated_uid", card_type="data", name="update")

    registry.update_card(card=loaded_card)
    df = registry.list_cards(uid=loaded_card.uid)
    values = registry.query_value_from_card(
        uid=loaded_card.uid,
        columns=["data_card_uids"],
    )

    assert values["data_card_uids"].get("update") == "updated_uid"

    # test1 = timeit.Timer(lambda: predictor.predict(record)).timeit(1000)
    # test2 = timeit.Timer(lambda: predictor.predict_with_model(model, record)).timeit(1000)
    # print(f"onnx: {test1}, sklearn: {test2}")
    # a


def test_full_pipeline_with_loading(db_registries, linear_regression):
    team = "mlops"
    user_email = "mlops.com"
    pipeline_code_uri = "test_pipe_uri"

    data_registry: CardRegistry = db_registries["data"]
    model_registry: CardRegistry = db_registries["model"]
    experiment_registry: CardRegistry = db_registries["experiment"]
    pipeline_registry: CardRegistry = db_registries["pipeline"]

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
        sample_input_data=data[:10],
        name="test_model",
        team=team,
        user_email=user_email,
        data_card_uid=data_card.uid,
    )

    model_registry.register_card(model_card)

    ##### ExperimentCard
    exp_card = ExperimentCard(
        name="test_experiment",
        team=team,
        user_email=user_email,
        data_card_uid=data_card.uid,
        model_card_uid=model_card.uid,
    )
    exp_card.add_metric("test_metric", 10)
    experiment_registry.register_card(card=exp_card)

    #### PipelineCard
    pipeline_card = PipelineCard(
        name="test_pipeline",
        team=team,
        user_email=user_email,
        pipeline_code_uri=pipeline_code_uri,
        data_card_uids={"data1": data_card.uid},
        model_card_uids={"model1": model_card.uid},
        experiment_card_uids={"exp1": exp_card.uid},
    )
    pipeline_registry.register_card(card=pipeline_card)

    loader = PipelineLoader(pipeline_card_uid=pipeline_card.uid)
    deck = loader.load_cards()
    assert all(name in deck.keys() for name in ["data1", "exp1", "model1"])
