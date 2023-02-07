from typing import Any, Dict, Union, cast

import numpy as np
import pandas as pd

from opsml_artifacts.registry.model.model_converters import OnnxModelConverter
from opsml_artifacts.registry.model.model_types import ModelType, OnnxModelType
from opsml_artifacts.registry.model.types import InputDataType, OnnxModelReturn


class OnnxModelCreator:
    def __init__(
        self,
        model: Any,
        input_data: Union[pd.DataFrame, np.ndarray, Dict[str, np.ndarray]],
    ):

        """Instantiates OnnxModelCreator that is used for converting models to Onnx

        Args:
            Model (BaseEstimator, Pipeline, StackingRegressor, Booster): Model to convert
            input_data (pd.DataFrame, np.ndarray): Sample of data used to train model
        """
        self.model = model
        self.input_data = self._get_one_sample(input_data)
        self.model_class = self._get_model_class_name()
        self.model_type = self.get_onnx_model_type()
        self.data_type = self.get_input_data_type(input_data=input_data)

    def _get_one_sample(
        self,
        input_data: Union[
            pd.DataFrame,
            np.ndarray,
            Dict[str, np.ndarray],
        ],
    ) -> Union[pd.DataFrame, np.ndarray, Dict[str, np.ndarray]]:

        """Parses input data and returns a single record to be used during ONNX conversion and validation"""

        data_type = type(input_data)
        if data_type in [
            InputDataType.PANDAS_DATAFRAME.value,
            InputDataType.NUMPY_ARRAY.value,
        ]:
            return cast(Union[pd.DataFrame, np.ndarray], input_data)[0:1]

        sample_dict = cast(Dict[str, np.ndarray], {})
        for key in cast(Dict[str, np.ndarray], input_data).keys():
            sample_dict[key] = input_data[key][0:1]
        return sample_dict

    def get_input_data_type(
        self,
        input_data: Union[
            pd.DataFrame,
            np.ndarray,
            Dict[str, np.ndarray],
        ],
    ) -> str:

        """Gets the current data type base on model type.
        Currently only sklearn pipeline supports pandas dataframes.
        All others support numpy arrays. This is needed for API signature
        creation when loading model predictors.

        Args:
            input_data (pd.DataFrame, np.ndarray): Sample of data used to train model

        Returns:
            data type (str)
        """

        # Onnx supports dataframe schemas for pipelines
        if self.model_type in [OnnxModelType.SKLEARN_PIPELINE, OnnxModelType.TF_KERAS]:
            return InputDataType(type(input_data)).name

        return InputDataType.NUMPY_ARRAY.name

    def _get_model_class_name(self):
        if "keras.engine" in str(self.model):
            return "keras"
        return self.model.__class__.__name__

    def get_onnx_model_type(self) -> str:

        model_type = next(
            (
                model_type
                for model_type in ModelType.__subclasses__()
                if model_type.validate(model_class_name=self.model_class)
            )
        )

        return model_type.get_type()

    def create_onnx_model(self) -> OnnxModelReturn:
        """Create model card from current model and sample data

        Returns
            OnnxModelReturn
        """
        onnx_model_return = OnnxModelConverter(
            model=self.model,
            input_data=self.input_data,
            model_type=self.model_type,
        ).convert_model()

        onnx_model_return.model_type = self.model_type
        onnx_model_return.data_type = self.data_type

        # add onnx version
        return onnx_model_return
