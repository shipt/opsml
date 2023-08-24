from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import polars as pl
from numpy.typing import NDArray
import pyarrow as pa
from os import path
import pytest
from pytest_lazyfixture import lazy_fixture
from opsml.registry.cards import DataCard, RunCard, PipelineCard, ModelCard, DataSplit
from opsml.registry.cards.pipeline_loader import PipelineLoader
from opsml.registry.sql.registry import CardRegistry
from opsml.registry.sql.semver import SemVerUtils
from opsml.helpers.exceptions import VersionError
from sklearn import linear_model
from sklearn.pipeline import Pipeline
import uuid
from pydantic import ValidationError
from tests.conftest import FOURTEEN_DAYS_TS, FOURTEEN_DAYS_STR


@pytest.mark.parametrize(
    "data_splits, test_data",
    [
        (lazy_fixture("test_split_array"), lazy_fixture("test_array")),
        (lazy_fixture("test_split_array"), lazy_fixture("test_df")),
        (lazy_fixture("test_split_array"), lazy_fixture("test_arrow_table")),
        (lazy_fixture("test_polars_split"), lazy_fixture("test_polars_dataframe")),
    ],
)
def test_register_data(
    db_registries: Dict[str, CardRegistry],
    test_data: tuple[pd.DataFrame, NDArray, pa.Table],
    data_splits: List[Dict[str, str]],
):
    # create data card
    registry = db_registries["data"]

    data_card = DataCard(
        data=test_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_splits=data_splits,
    )

    splits = data_card.split_data()

    registry.register_card(card=data_card)

    df = registry.list_cards(name=data_card.name, team=data_card.team, as_dataframe=True)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards(name=data_card.name, as_dataframe=True)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards(as_dataframe=True)
    assert isinstance(df, pd.DataFrame)

    df = registry.list_cards(name=data_card.name, team=data_card.team, version="1.0.0", as_dataframe=True)
    assert df.shape[0] == 1

    data_card = DataCard(
        data=test_data,
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        data_splits=data_splits,
    )
    registry.register_card(card=data_card)

    cards = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="^1",
        as_dataframe=False,
    )
    assert len(cards) == 1


def test_list_teams(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    teams = registry.list_teams()
    assert len(teams) == 1
    assert teams[0] == "mlops"


def test_list_card_names(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    names = registry.list_card_names(team="mlops")
    assert len(names) == 1
    assert names[0] == "test-df"

    names = registry.list_card_names()
    assert len(names) == 1
    assert names[0] == "test-df"


def test_datacard_sql_register(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    data_card = DataCard(
        name="test_sql",
        team="mlops",
        user_email="mlops.com",
        sql_logic={"test": "select * from test_table"},
        feature_descriptions={"test": "test_description"},
    )

    registry.register_card(card=data_card)
    loaded_card: DataCard = registry.load_card(uid=data_card.uid)
    assert loaded_card.sql_logic.get("test") is not None
    assert data_card.version == "1.0.0"


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

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.1",  # specifying major minor version
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="patch")

    assert data_card.version == "3.1.2"

    # test initial partial registration
    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="4.1",  # specifying major minor version
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="patch")
    assert data_card.version == "4.1.0"


def test_datacard_tags(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    data_card = DataCard(
        name="test_tags",
        team="mlops",
        user_email="mlops.com",
        feature_descriptions={"test": "test_description"},
        sql_logic={"test": "select * from test_table"},
    )
    data_card.add_tag("test", "hello")

    registry.register_card(card=data_card)

    cards = registry.list_cards(
        name="test_tags",
        team="mlops",
        tags={"test": "hello"},
        as_dataframe=False,
    )

    assert cards[0]["tags"] == {"test": "hello"}

    data_card = registry.load_card(
        name="test_tags",
        tags={"test": "hello"},
    )

    assert data_card.tags == {"test": "hello"}


def test_datacard_sql_register_date(db_registries: Dict[str, CardRegistry]):
    # create data card at current time
    registry = db_registries["data"]
    data_card = DataCard(
        name="test_date",
        team="mlops",
        user_email="mlops.com",
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card)
    record = data_card.create_registry_record()

    # add card with a timestamp from 14 days ago
    record.timestamp = FOURTEEN_DAYS_TS
    registry._registry.update_card_record(record.model_dump())

    cards = registry.list_cards()
    assert len(cards) >= 1

    cards = registry.list_cards(max_date=FOURTEEN_DAYS_STR)
    assert len(cards) == 1


def test_datacard_sql_register_file(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    data_card = DataCard(
        name="test_file",
        team="mlops",
        user_email="mlops.com",
        sql_logic={"test": "test_sql.sql"},
    )

    registry.register_card(card=data_card)
    loaded_card = registry.load_card(uid=data_card.uid)
    assert loaded_card.sql_logic.get("test") == "SELECT ORDER_ID FROM TEST_TABLE limit 100"


def test_unique_name_fail(db_registries: Dict[str, CardRegistry]):
    # create data card
    registry = db_registries["data"]
    data_card = DataCard(
        name="test_name_fail",
        team="mlops",
        user_email="mlops.com",
        sql_logic={"test": "test_sql.sql"},
    )

    registry.register_card(card=data_card)

    # test registering card with same name and different team
    with pytest.raises(ValueError):
        data_card = DataCard(
            name="test_name_fail",
            team="fail_teams",
            user_email="mlops.com",
            sql_logic={"test": "test_sql.sql"},
        )

        registry.register_card(card=data_card)


def test_datacard_sql(db_registries: Dict[str, CardRegistry], test_array: NDArray):
    # create data card
    registry = db_registries["data"]
    data_card = DataCard(
        data=test_array,
        name="test_sql",
        team="mlops",
        user_email="mlops.com",
    )

    name = "test"
    query = "select * from test_table"
    data_card.add_sql(name=name, query=query)

    assert data_card.sql_logic[name] == query

    name = "test"
    filename = "test_sql.sql"
    data_card.add_sql(name=name, filename=filename)

    assert data_card.sql_logic[name] == "SELECT ORDER_ID FROM TEST_TABLE limit 100"

    ### Test add failure
    with pytest.raises(ValueError):
        data_card.add_sql(name="fail", filename="fail.sql")

    with pytest.raises(ValueError):
        data_card.add_sql(name="fail")

    ## Test instantiation
    data_card = DataCard(data=test_array, name="test_df", team="mlops", user_email="mlops.com", sql_logic={name: query})
    assert data_card.sql_logic[name] == query

    data_card = DataCard(
        data=test_array,
        name="test_sql",
        team="mlops",
        user_email="mlops.com",
        sql_logic={name: filename},
    )
    assert data_card.sql_logic[name] == "SELECT ORDER_ID FROM TEST_TABLE limit 100"

    ## Test instantiation failure
    with pytest.raises(ValueError):
        data_card = DataCard(
            data=test_array,
            name="test_sql",
            team="mlops",
            user_email="mlops.com",
            sql_logic={"fail": "fail.sql"},
        )


def test_semver_registry_list(db_registries: Dict[str, CardRegistry], test_array: NDArray):
    # create data card
    registry = db_registries["data"]

    # version 1
    for i in range(0, 5):
        data_card = DataCard(
            data=test_array,
            name="test_semver",
            team="mlops",
            user_email="mlops.com",
        )
        registry.register_card(card=data_card, version_type="patch")

    cards = registry.list_cards(
        name="test_semver",
        team="mlops",
        version="^1.0.0",
        as_dataframe=False,
    )

    assert len(cards) == 1
    assert cards[0]["version"] == "1.0.4"

    # version 2
    data_card = DataCard(
        data=test_array,
        name="test_semver",
        team="mlops",
        user_email="mlops.com",
    )
    registry.register_card(card=data_card, version_type="major")

    for i in range(0, 12):
        data_card = DataCard(
            data=test_array,
            name="test_semver",
            team="mlops",
            user_email="mlops.com",
        )
        registry.register_card(card=data_card)

    # should return 13 versions
    cards = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="2.*.*",
        as_dataframe=False,
    )
    assert len(cards) == 13

    cards = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="^2.0.0",
        as_dataframe=False,
    )
    cards[0]["version"] == "2.12.0"
    assert len(cards) == 1

    # pre-release
    data_card_pre = DataCard(
        data=test_array,
        name="test_semver",
        team="mlops",
        user_email="mlops.com",
        version="3.0.0-rc.1",
    )
    registry.register_card(card=data_card_pre)

    records = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="3.*.*",
        as_dataframe=False,
    )

    assert len(records) == 1

    data_card_pre.version = "3.0.0"
    registry.update_card(card=data_card_pre)

    # check update works
    records = registry.list_cards(
        name=data_card.name,
        team=data_card.team,
        version="3.*.*",
        as_dataframe=False,
    )

    assert records[0]["version"] == "3.0.0"

    with pytest.raises(VersionError):
        # try registering card where version already exists
        data_card = DataCard(
            data=test_array,
            name="test_semver",
            team="mlops",
            user_email="mlops.com",
            version="3.0.0-rc.1",  # cant create a release for a minor version that already exists
        )
        registry.register_card(card=data_card)

    with pytest.raises(ValueError):
        # try invalid semver
        data_card = DataCard(
            data=test_array,
            name="test_semver",
            team="mlops",
            user_email="mlops.com",
            version="3.0.0blah",
        )
        registry.register_card(card=data_card)

    # pre-release
    data_card_pre = DataCard(
        data=test_array,
        name="test_semver",
        team="mlops",
        user_email="mlops.com",
        version="3.0.1-rc.1",
    )
    registry.register_card(card=data_card_pre)

    # test patch semver sort
    for i in range(0, 5):
        data_card = DataCard(
            data=test_array,
            name="patch",
            team="mlops",
            user_email="mlops.com",
        )
        registry.register_card(card=data_card, version_type="patch")

    cards = registry.list_cards(
        name="patch",
        team="mlops",
        version="^1.0.0",
        as_dataframe=False,
    )

    assert cards[0]["version"] == "1.0.4"


def test_runcard(
    linear_regression: linear_model.LinearRegression,
    db_registries: Dict[str, CardRegistry],
):
    registry: CardRegistry = db_registries["run"]
    run = RunCard(
        name="test_run",
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
    assert loaded_card.get_metric("test_metric").value == 10
    assert loaded_card.get_metric("test_metric2").value == 20

    with pytest.raises(ValueError):
        loaded_card.get_metric("test")

    with pytest.raises(ValueError):
        loaded_card.get_parameter("test")

    # metrics take floats, ints
    with pytest.raises(ValueError):
        loaded_card.log_metric("test_fail", "10")

    # params take floats, ints, str
    with pytest.raises(ValueError):
        loaded_card.log_parameter("test_fail", model)

    # test updating
    loaded_card.log_metric("updated_metric", 20)
    registry.update_card(card=loaded_card)

    # should be same runid
    loaded_card = registry.load_card(uid=run.uid)
    assert loaded_card.get_metric("updated_metric").value == 20
    assert loaded_card.runcard_uri == run.runcard_uri


def test_local_model_registry_to_onnx(
    db_registries: Dict[str, CardRegistry],
    sklearn_pipeline: Pipeline,
):
    # create data card
    data_registry: CardRegistry = db_registries["data"]
    model, data = sklearn_pipeline
    data_card = DataCard(
        data=data,
        name="pipeline_data",
        team="mlops",
        user_email="mlops.com",
    )
    data_registry.register_card(card=data_card)

    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
        to_onnx=True,
    )

    model_registry: CardRegistry = db_registries["model"]
    model_registry.register_card(card=model_card)

    loaded_card = model_registry.load_card(uid=model_card.uid)
    assert loaded_card.uris.model_metadata_uri is not None


def test_local_model_registry_no_onnx(
    db_registries: Dict[str, CardRegistry],
    sklearn_pipeline: Pipeline,
):
    # create data card
    data_registry: CardRegistry = db_registries["data"]
    model, data = sklearn_pipeline
    data_card = DataCard(
        data=data,
        name="pipeline_data",
        team="mlops",
        user_email="mlops.com",
    )
    data_registry.register_card(card=data_card)

    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
        to_onnx=False,
    )

    model_registry: CardRegistry = db_registries["model"]
    model_registry.register_card(card=model_card)

    loaded_card = model_registry.load_card(uid=model_card.uid)
    assert loaded_card.uris.model_metadata_uri is not None


def test_local_model_registry(
    db_registries: Dict[str, CardRegistry],
    sklearn_pipeline: Pipeline,
):
    # create data card
    data_registry: CardRegistry = db_registries["data"]
    model, data = sklearn_pipeline
    data_card = DataCard(
        data=data,
        name="pipeline_data",
        team="mlops",
        user_email="mlops.com",
    )
    data_registry.register_card(card=data_card)

    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
    )

    with pytest.raises(ValueError):
        model_card.model_data_schema

    with pytest.raises(ValueError):
        model_card.input_data_schema

    with pytest.raises(ValueError):
        model_card.load_onnx_model_definition()

    with pytest.raises(ValueError):
        model_card.load_trained_model()

    model_registry: CardRegistry = db_registries["model"]
    model_registry.register_card(model_card)

    assert path.exists(model_card.uris.model_metadata_uri)
    assert path.exists(model_card.uris.trained_model_uri)
    assert path.exists(model_card.uris.sample_data_uri)

    loaded_card = model_registry.load_card(uid=model_card.uid)

    assert loaded_card != model_card
    assert loaded_card.onnx_model_def is None
    assert loaded_card.trained_model is None
    assert loaded_card.sample_input_data is None

    loaded_card.load_onnx_model_definition()
    loaded_card.load_trained_model()

    assert loaded_card.trained_model is not None
    assert loaded_card.sample_input_data is not None
    assert loaded_card.onnx_model_def is not None


def test_register_model(
    db_registries: Dict[str, CardRegistry],
    sklearn_pipeline: Pipeline,
):
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

    model_card1 = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
    )

    model_registry: CardRegistry = db_registries["model"]
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

    # test pre-release model
    model_card_pre = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="pipeline_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
        version="3.1.0-rc.1",
    )

    model_registry.register_card(card=model_card_pre)
    cards = model_registry.list_cards(uid=model_card_pre.uid, as_dataframe=False)

    assert cards[0]["version"] == "3.1.0-rc.1"

    model_card_pre.version = "3.1.0"
    model_registry.update_card(card=model_card_pre)
    cards = model_registry.list_cards(uid=model_card_pre.uid, as_dataframe=False)

    assert cards[0]["version"] == "3.1.0"


@pytest.mark.parametrize("test_data", [lazy_fixture("test_df")])
def test_load_data_card(db_registries: Dict[str, CardRegistry], test_data: pd.DataFrame):
    data_name = "test_df"
    team = "mlops"
    user_email = "mlops.com"

    registry: CardRegistry = db_registries["data"]

    data_split = [
        DataSplit(label="train", column_name="year", column_value=2020),
        DataSplit(label="train", column_name="year", column_value=2021),
    ]

    data_card = DataCard(
        data=test_data,
        name=data_name,
        team=team,
        user_email=user_email,
        data_splits=data_split,
        additional_info={"input_metadata": 20},
        dependent_vars=[200, "test"],
        sql_logic={"test": "SELECT * FROM TEST_TABLE"},
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
    assert loaded_data.sql_logic["test"] == "SELECT * FROM TEST_TABLE"

    assert loaded_data.data_splits == data_split

    # update
    loaded_data.version = "1.2.0"
    registry.update_card(card=loaded_data)

    record = registry.query_value_from_card(uid=loaded_data.uid, columns=["version", "timestamp"])
    assert record["version"] == "1.2.0"


def test_datacard_failure():
    data_name = "test_df"
    team = "mlops"
    user_email = "mlops.com"

    data_split = [
        DataSplit(label="train", column_name="year", column_value=2020),
        DataSplit(label="train", column_name="year", column_value=2021),
    ]

    # should fail: data nor sql are provided
    with pytest.raises(ValueError) as ve:
        data_card = DataCard(
            name=data_name,
            team=team,
            user_email=user_email,
            data_splits=data_split,
            additional_info={"input_metadata": 20},
            dependent_vars=[200, "test"],
        )
    assert ve.match("Data or sql logic must be supplied when no data_uri")


def test_pipeline_registry(db_registries: Dict[str, CardRegistry]):
    pipeline_card = PipelineCard(
        name="test_df",
        team="mlops",
        user_email="mlops.com",
        pipeline_code_uri="test_pipe_uri",
    )
    for card_type in ["data", "run", "model"]:
        pipeline_card.add_card_uid(uid=uuid.uuid4().hex, card_type=card_type)

    # register
    registry: CardRegistry = db_registries["pipeline"]
    registry.register_card(card=pipeline_card)
    loaded_card: PipelineCard = registry.load_card(uid=pipeline_card.uid)
    loaded_card.add_card_uid(uid="updated_uid", card_type="data")
    registry.update_card(card=loaded_card)
    cards = registry.list_cards(uid=loaded_card.uid)
    values = registry.query_value_from_card(
        uid=loaded_card.uid,
        columns=["datacard_uids"],
    )
    assert bool(values["datacard_uids"])


def test_full_pipeline_with_loading(
    db_registries: Dict[str, CardRegistry],
    linear_regression: linear_model.LinearRegression,
):
    team = "mlops"
    user_email = "mlops.com"
    pipeline_code_uri = "test_pipe_uri"
    data_registry: CardRegistry = db_registries["data"]
    model_registry: CardRegistry = db_registries["model"]
    experiment_registry: CardRegistry = db_registries["run"]
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
        sample_input_data=data[:1],
        name="test_model",
        team=team,
        user_email=user_email,
        datacard_uid=data_card.uid,
    )

    model_registry.register_card(model_card)

    ##### RunCard
    exp_card = RunCard(
        name="test_experiment",
        team=team,
        user_email=user_email,
        datacard_uids=[data_card.uid],
        modelcard_uids=[model_card.uid],
    )
    exp_card.log_metric("test_metric", 10)
    experiment_registry.register_card(card=exp_card)

    #### PipelineCard
    pipeline_card = PipelineCard(
        name="test_pipeline",
        team=team,
        user_email=user_email,
        pipeline_code_uri=pipeline_code_uri,
        datacard_uids=[data_card.uid],
        modelcard_uids=[model_card.uid],
        runcard_uids=[exp_card.uid],
    )
    pipeline_registry.register_card(card=pipeline_card)

    loader = PipelineLoader(pipelinecard_uid=pipeline_card.uid)
    uids = loader.card_uids

    assert uids["data"][0] == data_card.uid
    assert uids["run"][0] == exp_card.uid
    assert uids["model"][0] == model_card.uid


def test_model_registry_with_polars(
    db_registries: Dict[str, CardRegistry],
    linear_regression_polars: Tuple[pl.DataFrame, linear_model.LinearRegression],
):
    # create data card
    data_registry: CardRegistry = db_registries["data"]
    model, data = linear_regression_polars
    data_card = DataCard(
        data=data,
        name="polars_data",
        team="mlops",
        user_email="mlops.com",
    )
    data_registry.register_card(card=data_card)

    model_card = ModelCard(
        trained_model=model,
        sample_input_data=data[0:1],
        name="polars_model",
        team="mlops",
        user_email="mlops.com",
        datacard_uid=data_card.uid,
        to_onnx=True,
    )

    model_registry: CardRegistry = db_registries["model"]
    model_registry.register_card(card=model_card)

    loaded_card = model_registry.load_card(uid=model_card.uid)
    assert loaded_card.uris.model_metadata_uri is not None


def test_pandas_dtypes(db_registries: Dict[str, CardRegistry], drift_dataframe):
    registry = db_registries["data"]
    data, y, _, _ = drift_dataframe

    data["col_11"] = y
    data["eval_flg"] = np.where(data["col_11"] <= 5, 1, 0)
    data["col_11"] = data["col_11"].astype("category")

    datacard = DataCard(
        name="pandas_dtype",
        team="mlops",
        user_email="mlops.com",
        data=data,
        data_splits=[
            DataSplit(label="train", column_value=0, column_name="eval_flg"),
            DataSplit(label="test", column_value=1, column_name="eval_flg"),
        ],
    )
    registry.register_card(card=datacard, version_type="patch")
    datacard = registry.load_card(uid=datacard.uid)
    datacard.load_data()

    splits = datacard.split_data()
    assert splits.train.X.dtypes["col_11"] == "category"
    assert splits.test.X.dtypes["col_11"] == "category"


def test_polars_dtypes(db_registries: Dict[str, CardRegistry], iris_data_polars):
    registry = db_registries["data"]
    data = iris_data_polars

    data = data.with_columns(
        [
            pl.when(pl.col("target") <= 1).then(pl.lit(1)).otherwise(pl.lit(0)).alias("eval_flg"),
            pl.when(pl.col("target") <= 1).then(pl.lit("a")).otherwise(pl.lit("b")).alias("test_cat"),
        ]
    )
    data = data.with_columns(pl.col("test_cat").cast(pl.Categorical))
    orig_schema = data.schema

    datacard = DataCard(
        name="pandas_dtype",
        team="mlops",
        user_email="mlops.com",
        data=data,
        data_splits=[
            DataSplit(label="train", column_value=0, column_name="eval_flg"),
            DataSplit(label="test", column_value=1, column_name="eval_flg"),
        ],
    )
    registry.register_card(card=datacard, version_type="patch")
    datacard = registry.load_card(uid=datacard.uid)
    datacard.load_data()

    splits = datacard.split_data()
    assert splits.train.X.schema["test_cat"] == orig_schema["test_cat"]
    assert splits.test.X.schema["test_cat"] == orig_schema["test_cat"]


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

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.1",  # specifying major minor version
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="patch")
    assert data_card.version == "3.1.2"

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3",  # specifying major with minor bump
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="minor")
    assert data_card.version == "3.2.0"

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3",  # specifying major with patch bump
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="patch")
    assert data_card.version == "3.2.1"

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.2",  # specifying major minor with minor bump.
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="minor")
    assert data_card.version == "3.3.0"

    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="3.2",  # specifying major minor with minor bump.
        sql_logic={"test": "select * from test_table"},
    )

    # This should rarely happen, but should work (3.3.0 already exists, should increment to 3.4.0)
    registry.register_card(card=data_card, version_type="minor")
    assert data_card.version == "3.4.0"

    # test initial partial registration
    data_card = DataCard(
        name="major_minor",
        team="mlops",
        user_email="mlops.com",
        version="4.1",  # specifying major minor version
        sql_logic={"test": "select * from test_table"},
    )

    registry.register_card(card=data_card, version_type="patch")
    assert data_card.version == "4.1.0"
