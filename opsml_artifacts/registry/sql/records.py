from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import pyarrow as pa
from pydantic import BaseModel, root_validator, validator

from opsml_artifacts.drift.models import DriftReport
from opsml_artifacts.registry.cards.storage import load_record_artifact_from_storage


class DataRegistryRecord(BaseModel):
    data_uri: str
    drift_uri: Optional[str] = None
    data_splits: Optional[Dict[str, List[Dict[str, Any]]]] = None
    version: int
    data_type: str
    name: str
    team: str
    feature_map: Dict[str, str]
    feature_descriptions: Optional[Dict[str, str]]
    user_email: str
    uid: Optional[str] = None
    dependent_vars: Optional[List[str]] = None

    @validator("data_splits", pre=True)
    def convert_to_dict(cls, splits):  # pylint: disable=no-self-argument
        if bool(splits):
            return {"splits": splits}

        return splits


class ModelRegistryRecord(BaseModel):
    uid: str
    version: int
    team: str
    user_email: str
    name: str
    model_uri: str
    model_type: str


class ExperimentRegistryRecord(BaseModel):
    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    data_card_uid: Optional[str] = None
    model_card_uid: Optional[str] = None
    pipeline_card_uid: Optional[str] = None
    artifact_uris: Optional[Dict[str, str]]
    metrics: Optional[Dict[str, Union[float, int]]]


class PipelineRegistryRecord(BaseModel):
    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    pipeline_code_uri: str
    data_card_uids: Optional[Dict[str, str]] = None
    model_card_uids: Optional[Dict[str, str]] = None
    experiment_card_uids: Optional[Dict[str, str]] = None


class LoadedDataRecord(BaseModel):
    data_uri: str
    drift_uri: Optional[str] = None
    data_splits: Optional[List[Dict[str, Any]]] = None
    version: int
    data_type: str
    name: str
    team: str
    feature_map: Dict[str, str]
    feature_descriptions: Optional[Dict[str, str]]
    user_email: str
    uid: Optional[str] = None
    dependent_vars: Optional[List[str]] = None
    data: Union[np.ndarray, pd.DataFrame, pa.Table]
    drift_report: Optional[Dict[str, DriftReport]] = None

    class Config:
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    def load_attributes(cls, values):  # pylint: disable=no-self-argument
        values["data_splits"] = LoadedDataRecord.get_splits(splits=values["data_splits"])
        values["data"] = LoadedDataRecord.load_data(values=values)
        values["drift_report"] = LoadedDataRecord.load_drift_report(values=values)

        return values

    @staticmethod
    def get_splits(splits):
        if bool(splits):
            return splits.get("splits")
        return splits

    @staticmethod
    def load_data(values):

        return load_record_artifact_from_storage(
            storage_uri=values["data_uri"],
            artifact_type=values["data_type"],
        )

    @staticmethod
    def load_drift_report(values):

        if bool(values.get("drift_uri")):
            return load_record_artifact_from_storage(
                storage_uri=values["drift_uri"],
                artifact_type="dict",
            )
        return None


class LoadedModelRecord(BaseModel):
    uid: str
    version: int
    team: str
    user_email: str
    name: str
    model_uri: str
    model_type: str

    def load_model_card_definition(self) -> Dict[str, Any]:

        """Loads a model card definition from current attributes

        Returns:
            Dictionary to be parsed by ModelCard.parse_obj()
        """

        model_card_definition = load_record_artifact_from_storage(
            storage_uri=self.model_uri,
            artifact_type="dict",
        )
        model_card_definition["model_uri"] = self.model_uri
        return model_card_definition


class LoadedExperimentRecord(BaseModel):
    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    data_card_uid: Optional[str] = None
    model_card_uid: Optional[str] = None
    pipeline_card_uid: Optional[str] = None
    artifact_uris: Dict[str, str]
    artifacts: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Union[int, float]]]

    # @staticmethod
    def load_artifacts(self) -> None:
        """Loads experiment artifacts to pydantic model"""

        loaded_artifacts: Dict[str, Any] = {}
        if not bool(self.artifact_uris):
            setattr(self, "artifacts", loaded_artifacts)

        for name, uri in self.artifact_uris.items():
            loaded_artifacts[name] = load_record_artifact_from_storage(
                storage_uri=uri,
                artifact_type="artifact",
            )
        setattr(self, "artifacts", loaded_artifacts)


# same as piplelineregistry (duplicating to stay with theme of separate records)
class LoadedPipelineRecord(BaseModel):
    name: str
    team: str
    user_email: str
    uid: Optional[str] = None
    version: Optional[int] = None
    pipeline_code_uri: str
    data_card_uids: Optional[Dict[str, str]] = None
    model_card_uids: Optional[Dict[str, str]] = None
    experiment_card_uids: Optional[Dict[str, str]] = None
