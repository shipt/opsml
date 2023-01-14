from functools import cached_property
from typing import Any, Dict, List, Optional, Union, cast

import numpy as np

# from onnx.onnx_ml_pb2 import ModelProto  # pylint: disable=no-name-in-module
import pandas as pd
from cryptography.fernet import Fernet
from pyarrow import Table
from pydantic import BaseModel, root_validator, validator
from pyshipt_logging import ShiptLogging

from opsml_artifacts.drift.data_drift import DriftReport
from opsml_artifacts.registry.cards.predictor import OnnxModelPredictor
from opsml_artifacts.registry.cards.storage import save_record_artifact_to_storage
from opsml_artifacts.registry.data.formatter import ArrowTable, DataFormatter
from opsml_artifacts.registry.data.splitter import DataHolder, DataSplitter
from opsml_artifacts.registry.model.types import DataDict, ModelDefinition
from opsml_artifacts.registry.sql.records import (
    DataRegistryRecord,
    ExperimentRegistryRecord,
    ModelRegistryRecord,
    PipelineRegistryRecord,
)

logger = ShiptLogging.get_logger(__name__)


class ArtifactCard(BaseModel):
    """Base pydantic class for artifacts"""

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False

    def create_registry_record(
        self,
        uid: str,
        version: int,
        registry_name: str,
    ) -> Any:
        """Creates a registry record from self attributes

        Args:
            registry_name (str): Name of registry
            uid (str): Unique id associated with artifact
            version (int): Version for artifact
        """


class DataCard(ArtifactCard):
    """Create a DataCard from your data.

    Args:
        data (np.ndarray, pd.DataFrame, pa.Table): Data to use for
        data card.
        name (str): What to name the data
        team (str): Team that this data is associated with
        user_email (str): Email to associate with data card
        drift_report (dictioary of DriftReports): Optional drift report generated by Drifter class
        dependent_vars (List[str]): Optional list of dependent variables in data
        feature_descriptions (Dictionary): Optional dictionary of feature names and their descriptions
        data_splits (List of dictionaries): Optional list containing split logic. Defaults
        to None. Logic for data splits can be defined in the following three ways:

        You can specify as many splits as you'd like

        (1) Split based on column value (works for pd.DataFrame)
            splits = [
                {"label": "train", "column": "DF_COL", "column_value": 0}, -> "val" can also be a string
                {"label": "test",  "column": "DF_COL", "column_value": 1},
                {"label": "eval",  "column": "DF_COL", "column_value": 2},
                ]

        (2) Index slicing by start and stop (works for np.ndarray, pyarrow.Table, and pd.DataFrame)
            splits = [
                {"label": "train", "start": 0, "stop": 10},
                {"label": "test", "start": 11, "stop": 15},
                ]

        (3) Index slicing by list (works for np.ndarray, pyarrow.Table, and pd.DataFrame)
            splits = [
                {"label": "train", "indices": [1,2,3,4]},
                {"label": "test", "indices": [5,6,7,8]},
                ]

        The following are non-required args and are set after registering a DataCard

        data_uri (str): GCS location where converted pyarrow table is stored
        drift_uri (str): GCS location where drift report is stored
        version (int): DataCard version
        feature_map (dictionary): Map of features in data (inferred when converting to pyrarrow table)
        data_type (str): Data type inferred from supplied data
        uid (str): Unique id assigned to the DataCard


    Returns:
        DataCard

    """

    name: str
    team: str
    user_email: str
    data: Union[np.ndarray, pd.DataFrame, Table]
    drift_report: Optional[Dict[str, DriftReport]] = None
    data_splits: List[Dict[str, Any]] = []
    data_uri: Optional[str] = None
    drift_uri: Optional[str] = None
    version: Optional[int] = None
    feature_map: Optional[Dict[str, Union[str, None]]] = None
    data_type: Optional[str] = None
    uid: Optional[str] = None
    dependent_vars: Optional[List[str]] = None
    feature_descriptions: Optional[Dict[str, str]] = None

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False

    @property
    def has_data_splits(self):
        return bool(self.data_splits)

    @validator("data_splits", pre=True, always=True)
    def convert_none(cls, splits):  # pylint: disable=no-self-argument
        if splits is None:
            return []

        for split in splits:
            indices = split.get("indices")
            if indices is not None and isinstance(indices, np.ndarray):
                split["indices"] = indices.tolist()

        return splits

    @validator("feature_descriptions", pre=True, always=True)
    def lower_descriptions(cls, feature_descriptions):  # pylint: disable=no-self-argument

        if feature_descriptions is None:
            return feature_descriptions

        feat_dict = {}
        for feature, description in feature_descriptions.items():
            feat_dict[feature.lower()] = description.lower()

        return feat_dict

    def overwrite_converted_data_attributes(self, converted_data: ArrowTable):
        setattr(self, "data_uri", converted_data.storage_uri)
        setattr(self, "feature_map", converted_data.feature_map)
        setattr(self, "data_type", converted_data.table_type)

    def split_data(self) -> Optional[DataHolder]:

        """Loops through data splits and splits data either by indexing or
        column values

        Returns
            Class containing data splits
        """

        if not self.has_data_splits:
            return None

        data_splits: DataHolder = self._parse_data_splits()
        return data_splits

    def _parse_data_splits(self) -> DataHolder:

        data_holder = DataHolder()
        for split in self.data_splits:
            label, data = DataSplitter(split_attributes=split).split(data=self.data)
            setattr(data_holder, label, data)

        return data_holder

    def _convert_and_save_data(self, blob_path: str, version: int) -> None:

        """Converts data into a pyarrow table or numpy array and saves to gcs.

        Args:
            Data_registry (str): Name of data registry. This attribute is used when saving
            data in gcs.
        """

        converted_data: ArrowTable = DataFormatter.convert_data_to_arrow(data=self.data)
        converted_data.feature_map = DataFormatter.create_table_schema(converted_data.table)
        storage_path = save_record_artifact_to_storage(
            artifact=converted_data.table,
            name=self.name,
            version=version,
            team=self.team,
            blob_path=blob_path,
        )
        converted_data.storage_uri = storage_path.gcs_uri

        # manually overwrite
        self.overwrite_converted_data_attributes(converted_data=converted_data)

    def _save_drift(self, blob_path: str, version: int) -> None:

        """Saves drift report to gcs"""

        if bool(self.drift_report):

            storage_path = save_record_artifact_to_storage(
                artifact=self.drift_report,
                name="drift_report",
                version=version,
                team=self.team,
                blob_path=blob_path,
            )
            setattr(self, "drift_uri", storage_path.gcs_uri)

    def create_registry_record(
        self,
        uid: str,
        version: int,
        registry_name: str,
    ) -> DataRegistryRecord:

        """Creates required metadata for registering the current data card.
        Implemented with a DataRegistry object.

        Args:
            Data_registry (str): Name of data registry. This attribute is used when saving
            data in gcs.

        Returns:
            Regsitry metadata

        """
        setattr(self, "uid", uid)
        setattr(self, "version", version)
        self._convert_and_save_data(blob_path=registry_name, version=version)
        self._save_drift(blob_path=registry_name, version=version)

        return DataRegistryRecord(**self.__dict__)


class ModelCard(ArtifactCard):
    """Create a ModelCard from your trained machine learning model.
    This Card is used in conjunction with the ModelCardCreator class.

    Args:
        data (np.ndarray, pd.DataFrame, pa.Table): Data to use for
        data card.
        name (str): What to name the model
        team (str): Team that this model is associated with
        user_email (str): Email to associate with card
        uid (str): Unique id (assigned if card has been registered)
        version (int): Current version (assigned if card has been registered)
        data_card_uid (str): Uid of the DataCard associated with training the model
        onnx_model_data (DataDict): Pydantic model containing onnx data schema
        onnx_model_def (ModelDefinition): Pydantic model containing OnnxModel definition
        model_uri (str): GCS uri where model is stored
        model_type (str): Type of model
        data_schema (Dictionary): Optional dictionary of the data schema used in model training
    """

    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    data_card_uid: Optional[str] = None
    onnx_model_data: DataDict
    onnx_model_def: ModelDefinition
    model_uri: Optional[str]
    model_type: str
    data_schema: Optional[Dict[str, str]]

    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    def save_modelcard(self, blob_path: str, version: int):

        storage_path = save_record_artifact_to_storage(
            artifact=self.dict(),
            name=self.name,
            version=version,
            team=self.team,
            blob_path=blob_path,
        )
        setattr(self, "model_uri", storage_path.gcs_uri)

    def create_registry_record(
        self,
        uid: str,
        version: int,
        registry_name: str,
    ) -> ModelRegistryRecord:
        """Creates a registry record from the current ModelCard

        registry_name (str): ModelCard Registry table making request
        uid (str): Unique id of ModelCard

        """

        setattr(self, "uid", uid)
        setattr(self, "version", version)
        self.save_modelcard(blob_path=registry_name, version=version)
        return ModelRegistryRecord(**self.__dict__)

    def _decrypt_model_definition(self) -> bytes:
        cipher = Fernet(key=self.onnx_model_def.encrypt_key)
        model_bytes = cipher.decrypt(self.onnx_model_def.model_bytes)

        return model_bytes

    def _set_version_for_predictor(self) -> int:
        if self.version is None:
            logger.warning(
                """ModelCard has no version (not registered).
                Defaulting to 1 (for testing only)
            """
            )
            version = 1
        else:
            version = self.version

        return version

    def model(self) -> OnnxModelPredictor:

        """Loads a model from serialized string

        Returns
            Onnx ModelProto

        """

        model_bytes = self._decrypt_model_definition()
        version = self._set_version_for_predictor()

        return OnnxModelPredictor(
            model_type=self.model_type,
            model_definition=model_bytes,
            data_dict=self.onnx_model_data,
            data_schema=self.data_schema,
            model_version=version,
        )


class PipelineCard(ArtifactCard):
    """Create as PipelineCard from specified arguments

    Args:
        name (str): What to name the model
        team (str): Team that this model is associated with
        user_email (str): Email to associate with card
        uid (str): Unique id (assigned if card has been registered)
        version (int): Current version (assigned if card has been registered)
        pipeline_code_uri (str): Storage uri of pipeline code
        data_card_uids (dictionary): Optional dictionary of DataCard uids to associate with pipeline
        model_card_uids (dictionary): Optional dictionary of ModelCard uids to associate with pipeline
        experiment_card_uids (dictionary): Optional dictionary of ExperimentCard uids to associate with pipeline

    """

    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    pipeline_code_uri: str
    data_card_uids: Optional[Dict[str, str]] = None
    model_card_uids: Optional[Dict[str, str]] = None
    experiment_card_uids: Optional[Dict[str, str]] = None

    @root_validator(pre=True)
    def set_data_uids(cls, values):  # pylint: disable=no-self-argument
        for uid_type in ["data_card_uids", "model_card_uids", "experiment_card_uids"]:
            if values.get(uid_type) is None:
                values[uid_type]: Dict[str, str] = {}
        return values

    def add_card_uid(self, uid: str, card_type: str, name: Optional[str] = None):
        """Adds Card uid to appropriate card type attribute

        Args:
            name (str): Optional name to associate with uid
            uid (str): Card uid
            card_type (str): Card type. Accepted values are "data", "model", "experiment"
        """
        card_type = card_type.lower()
        if card_type.lower() not in ["data", "experiment", "model"]:
            raise ValueError("""Only 'model', 'experiment' and 'data' are allowed values for card_type""")

        current_ids = getattr(self, f"{card_type}_card_uids")
        new_ids = {**current_ids, **{name: uid}}
        setattr(self, f"{card_type}_card_uids", new_ids)

    def load_pipeline_code(self):
        raise NotImplementedError

    def create_registry_record(
        self,
        uid: str,
        version: int,
        registry_name: str,
    ) -> PipelineRegistryRecord:
        """Creates a registry record from the current PipelineCard

        registry_name (str): PipelineCard Registry table making request
        uid (str): Unique id of PipelineCard

        """

        setattr(self, "uid", uid)
        setattr(self, "version", version)
        return PipelineRegistryRecord(**self.__dict__)


class ExperimentCard(ArtifactCard):
    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    data_card_uid: Optional[str] = None
    model_card_uid: Optional[str] = None
    pipeline_card_uid: Optional[str] = None
    metrics: Optional[Dict[str, Union[float, int]]] = None
    artifacts: Optional[Dict[str, Any]] = None
    artifact_uris: Optional[Dict[str, str]] = None

    @validator("metrics", pre=True, always=True)
    def set_metrics(cls, value):  # pylint: disable=no-self-argument
        if not value:
            value = {}
            return value
        return value

    @validator("artifacts", pre=True, always=True)
    def set_artifacts(cls, value):  # pylint: disable=no-self-argument
        if not value:
            value = {}
            return value
        return value

    def add_metric(self, name: str, value: Union[int, float]):
        """Adds metric to the existing ExperimentCard metric dictionary

        name (str): Name of metric
        value (float or int): Value of metric
        """

        curr_metrics = cast(Dict[str, Union[int, float]], self.metrics)
        self.metrics = {**{name: value}, **curr_metrics}

    def add_metrics(self, metrics: Dict[str, Union[float, int]]):
        """Adds metrics to the existing ExperimentCard metric dictionary

        metrics (dictionary): Dictionary containing name (str) and value (float or int) pairs
        to add to the current metric set
        """

        curr_metrics = cast(Dict[str, Union[int, float]], self.metrics)
        self.metrics = {**metrics, **curr_metrics}

    def add_artifact(self, name: str, artifact: Any):
        """Append any artifact associated with your experiment to
        the ExperimentCard. The aritfact will be saved in gcs and the uri
        will be appended to the ExperimentCard. Artifact must be pickleable
        (saved with joblib)

        Args:
            name (str): What to name the arifact
            artifact(Any): Artifact to add
        """

        curr_artifacts = cast(Dict[str, Any], self.artifacts)
        new_artifact = {name: artifact}
        self.artifacts = {**new_artifact, **curr_artifacts}
        setattr(self, "artifacts", {**new_artifact, **self.artifacts})

    def save_artifacts(self, blob_path: str, version: int) -> None:

        artifact_uris: Dict[str, str] = {}

        if self.artifacts is not None:
            for name, artifact in self.artifacts.items():
                storage_path = save_record_artifact_to_storage(
                    artifact=artifact,
                    name=self.name,
                    version=version,
                    team=self.team,
                    blob_path=blob_path,
                )

                artifact_uris[name] = storage_path.gcs_uri
        setattr(self, "artifact_uris", artifact_uris)

    def create_registry_record(
        self,
        uid: str,
        version: int,
        registry_name: str,
    ) -> ExperimentRegistryRecord:
        """Creates a registry record from the current ExperimentCard

        registry_name (str): ExperimentCardRegistry table making request
        uid (str): Unique id of ExperimentCard

        """

        if not any([self.data_card_uid, self.pipeline_card_uid, self.model_card_uid]):
            raise ValueError(
                """One of DataCard, ModelCard, or PipelineCard must be specified
            """
            )

        setattr(self, "uid", uid)
        setattr(self, "version", version)
        self.save_artifacts(blob_path=registry_name, version=version)
        return ExperimentRegistryRecord(**self.__dict__)
