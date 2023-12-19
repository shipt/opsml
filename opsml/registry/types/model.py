# pylint: disable=no-member
# mypy: disable-error-code="attr-defined"

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

"""Base code for Onnx model conversion"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union

import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from pydantic import BaseModel, ConfigDict, Field, field_validator

from opsml.registry.types.huggingface import HuggingFaceORTModel
from opsml.version import __version__

# Dict[str, Any] is used because an input value can be a numpy, torch, or tensorflow tensor
ValidModelInput = Union[pd.DataFrame, np.ndarray, Dict[str, Any], pl.DataFrame, str]  # type: ignore
ValidSavedSample = Union[pa.Table, np.ndarray, Dict[str, np.ndarray]]  # type: ignore


class DataDtypes(str, Enum):
    STRING = "string"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"


class TrainedModelType(str, Enum):
    TRANSFORMERS = "transformers"
    SKLEARN_PIPELINE = "sklearn_pipeline"
    SKLEARN_ESTIMATOR = "sklearn_estimator"
    STACKING_ESTIMATOR = "stackingestimator"
    CALIBRATED_CLASSIFIER = "calibratedclassifiercv"
    LGBM_REGRESSOR = "lgbmregressor"
    LGBM_CLASSIFIER = "lgbmclassifier"
    XGB_REGRESSOR = "xgbregressor"
    XGB_CLASSIFIER = "xgbclassifier"
    LGBM_BOOSTER = "lgbmbooster"
    TF_KERAS = "keras"
    PYTORCH = "pytorch"
    PYTORCH_LIGHTNING = "pytorch_lightning"


SKLEARN_SUPPORTED_MODEL_TYPES = [
    TrainedModelType.SKLEARN_ESTIMATOR,
    TrainedModelType.STACKING_ESTIMATOR,
    TrainedModelType.SKLEARN_PIPELINE,
    TrainedModelType.LGBM_REGRESSOR,
    TrainedModelType.LGBM_CLASSIFIER,
    TrainedModelType.XGB_REGRESSOR,
    TrainedModelType.CALIBRATED_CLASSIFIER,
]

LIGHTGBM_SUPPORTED_MODEL_TYPES = [
    TrainedModelType.LGBM_BOOSTER,
]

UPDATE_REGISTRY_MODELS = [
    TrainedModelType.LGBM_CLASSIFIER,
    TrainedModelType.LGBM_REGRESSOR,
    TrainedModelType.XGB_REGRESSOR,
]

AVAILABLE_MODEL_TYPES = list(TrainedModelType)


class HuggingFaceModuleType(str, Enum):
    PRETRAINED_MODEL = "transformers.modeling_utils.PreTrainedModel"
    TRANSFORMER_MODEL = "transformers.models"
    TRANSFORMER_PIPELINE = "transformers.pipelines"


class OnnxDataProto(Enum):
    """Maps onnx element types to their data types"""

    UNDEFINED = 0
    FLOAT = 1
    UINT8 = 2
    INT8 = 3
    UINT16 = 4
    INT16 = 5
    INT32 = 6
    INT64 = 7
    STRING = 8
    BOOL = 9
    FLOAT16 = 10
    DOUBLE = 11
    UINT32 = 12
    UINT64 = 13
    COMPLEX64 = 14
    COMPLEX128 = 15
    BFLOAT16 = 16


class Feature(BaseModel):
    feature_type: str
    shape: List[Any]


class DataDict(BaseModel):
    """Datamodel for feature info"""

    data_type: Optional[str] = None
    input_features: Dict[str, Feature]
    output_features: Dict[str, Feature]

    model_config = ConfigDict(frozen=False)


class OnnxModelDefinition(BaseModel):
    onnx_version: str = Field(..., description="Version of onnx model used to create proto")
    model_bytes: bytes = Field(..., description="Onnx model as serialized string")

    model_config = ConfigDict(protected_namespaces=("protect_",))


class ApiDataSchemas(BaseModel):
    model_data_schema: DataDict  # expected model inputs and outputs
    input_data_schema: Optional[Dict[str, Feature]] = None  # what the api can be fed

    model_config = ConfigDict(frozen=False, protected_namespaces=("protect_",))


class ModelReturn(BaseModel):
    model_definition: Optional[OnnxModelDefinition] = None
    api_data_schema: ApiDataSchemas
    model_type: str = "placeholder"

    model_config = ConfigDict(frozen=False, protected_namespaces=("protect_",))


class TorchOnnxArgs(BaseModel):
    """
    input_names (List[str]): Optional list containing input names for model inputs.
    This is a PyTorch-specific attribute
    output_names (List[str]): Optional list containing output names for model outputs.
    This is a PyTorch-specific attribute
    dynamic_axes (Dictionary): Optional PyTorch attribute that defines dynamic axes
    constant_folding (bool): Whether to use constant folding optimization. Default is True
    """

    input_names: List[str]
    output_names: List[str]
    dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None
    do_constant_folding: bool = True
    export_params: bool = True
    verbose: bool = False
    options: Optional[Dict[str, Any]] = None


class HuggingFaceOnnxArgs(BaseModel):
    """Optional Args to use with a huggingface model

    Args:
        ort_type:
            Optimum onnx class name
        provider:
            Onnx runtime provider to use
        config:
            Optional optimum config to use
    """

    ort_type: str
    provider: str = "CPUExecutionProvider"
    config: Optional[Any] = None

    @field_validator("ort_type", mode="before")
    @classmethod
    def check_ort_type(cls, ort_type: str) -> str:
        """Validates onnx runtime model type"""
        ort_model = ort_type.lower()
        if ort_model not in list(HuggingFaceORTModel):
            raise ValueError(f"Optimum model type {ort_model} is not supported")
        return ort_model

    @field_validator("config", mode="before")
    @classmethod
    def check_config(cls, config: Optional[Any] = None) -> str:
        """Check that optimum config is valid"""

        if config is None:
            return config

        from optimum.onnxruntime import (
            CalibrationConfig,
            AutoCalibrationConfig,
            QuantizationModel,
            AutoQuantizationConfig,
            OptimizationConfig,
            AutoOptimizationConfig,
            ORTConfig,
            QuantizationConfig,
        )

        assert isinstance(
            config,
            (
                CalibrationConfig,
                AutoCalibrationConfig,
                QuantizationModel,
                AutoQuantizationConfig,
                OptimizationConfig,
                AutoOptimizationConfig,
                ORTConfig,
                QuantizationConfig,
            ),
        ), "config must be a valid optimum config"


class ApiSigTypes(Enum):
    UNDEFINED = Any
    INT = int
    INT32 = int
    INT64 = int
    NUMBER = float
    FLOAT = float
    FLOAT32 = float
    FLOAT64 = float
    DOUBLE = float
    STR = str
    STRING = str
    ARRAY = list


# this is partly a hack to get Seldons metadata to work
# seldon metadata only accepts float, bool, int
class SeldonSigTypes(str, Enum):
    UNDEFINED = "BYTES"
    INT = "INT32"
    INT32 = "INT32"
    INT64 = "INT64"
    NUMBER = "FP32"
    FLOAT = "FP32"
    FLOAT16 = "FP16"
    FLOAT32 = "FP32"
    FLOAT64 = "FP64"
    DOUBLE = "FP64"
    STR = "BYTES"


class PydanticDataTypes(Enum):
    NUMBER = float
    INTEGER = int
    STRING = str
    ANY = Any


@dataclass
class OnnxAttr:
    onnx_path: Optional[str] = None
    onnx_version: Optional[str] = None


class ModelMetadata(BaseModel):
    model_name: str
    model_type: str
    onnx_uri: Optional[str] = None
    onnx_version: Optional[str] = None
    onnx_model_def: Optional[OnnxModelDefinition] = None
    model_uri: str
    model_version: str
    model_team: str
    opsml_version: str = __version__
    sample_data: Dict[str, Any]
    data_schema: ApiDataSchemas

    model_config = ConfigDict(protected_namespaces=("protect_",))


class ModelDownloadInfo(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    team: Optional[str] = None
    uid: Optional[str] = None


# Sklearn protocol stub
class BaseEstimator(Protocol):
    ...


# Onnx protocol stubs
class Graph:
    @property
    def output(self) -> Any:
        ...

    @property
    def input(self) -> Any:
        ...


class ModelProto(Protocol):
    ir_version: int
    producer_name: str
    producer_version: str
    domain: str
    model_version: int
    doc_string: str

    def SerializeToString(self) -> bytes:  # pylint: disable=invalid-name
        ...

    @property
    def graph(self) -> Graph:
        return Graph()


class ModelType:
    @staticmethod
    def get_type() -> str:
        raise NotImplementedError

    @staticmethod
    def validate(model_class_name: str) -> bool:
        raise NotImplementedError


class SklearnPipeline(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.SKLEARN_PIPELINE.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "Pipeline"


class SklearnCalibratedClassifier(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.CALIBRATED_CLASSIFIER.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "CalibratedClassifierCV"


class SklearnStackingEstimator(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.STACKING_ESTIMATOR.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name in ["StackingRegressor", "StackingClassifier"]


class LightGBMRegressor(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.LGBM_REGRESSOR.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "LGBMRegressor"


class LightGBMClassifier(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.LGBM_CLASSIFIER.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "LGBMClassifier"


class XGBRegressor(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.XGB_REGRESSOR.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "XGBRegressor"


class XGBClassifier(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.XGB_CLASSIFIER.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "XGBClassifier"


class LightGBMBooster(ModelType):
    @staticmethod
    def get_type() -> str:
        return TrainedModelType.LGBM_BOOSTER.value

    @staticmethod
    def validate(model_class_name: str) -> bool:
        return model_class_name == "Booster"