import pandas as pd
import numpy as np
import pyarrow as pa
from typing import Union
from opsml_data.helpers.exceptions import NotOfCorrectType
from opsml_data.registry.data_model import ArrowTable
from typing import Dict
from abc import ABC, abstractstaticmethod


class ArrowFormatter(ABC):
    @abstractstaticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]):
        """Converts data to pyarrow"""

    @abstractstaticmethod
    def validate_data(data: Union[pa.Table, np.ndarray]):
        """Validate data to formatter"""


class PandasFormatter(ArrowFormatter):
    @staticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:
        """Convert pandas dataframe to pyarrow table

        Args:
            data (pd.DataFrame): Pandas dataframe to convert

        Returns
            ArrowTable pydantic class containing table and table type
        """

        pa_table = pa.Table.from_pandas(data, preserve_index=False)

        return ArrowTable(
            table=pa_table,
            table_type=data.__class__.__name__,
        )

    @staticmethod
    def validate_data(data: pd.DataFrame):
        if isinstance(data, pd.DataFrame):
            return True
        return False


class NumpyFormatter(ArrowFormatter):
    @staticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:

        """Convert numpy array to pyarrow table

        Args:
            data (np.ndarray): Numpy array to convert.
            Assumes data is in shape (rows, columns).

        Returns
            Numpy array
        """

        return ArrowTable(
            table=data,
            table_type=data.__class__.__name__,
        )

    @staticmethod
    def validate_data(data: np.ndarray):
        if isinstance(data, np.ndarray):
            return True
        return False


class ArrowTableFormatter(ArrowFormatter):
    @staticmethod
    def convert(data: Union[pd.DataFrame, np.ndarray, pa.Table]) -> ArrowTable:

        """Take pyarrow table and returns pyarrow table

        Args:
            data (pyarrow table): Pyarrow table

        Returns
            ArrowTable pydantic class containing table and table type
        """

        return ArrowTable(
            table=data,
            table_type=data.__class__.__name__,
        )

    @staticmethod
    def validate_data(data: pa.Table):
        if isinstance(data, pa.Table):
            return True
        return False


########## Run tests for data formatter
class DataFormatter:
    @staticmethod
    def convert_data_to_arrow(data: Union[pd.DataFrame, np.array, pa.Table]) -> ArrowTable:

        """
        Converts a pandas dataframe or numpy array into a py arrow table.
        Args:
            data: Pandas dataframe or numpy array.
        Returns:
            py arrow table
        """

        converter = next(
            (
                arrow_formatter
                for arrow_formatter in ArrowFormatter.__subclasses__()
                if arrow_formatter.validate_data(data=data)
            ),
            None,
        )

        if not bool(converter):
            raise NotOfCorrectType(
                """Data type was not of Numpy array, pandas dataframe or pyarrow table
            """
            )

        return converter.convert(data=data)

    @staticmethod
    def create_table_schema(data: Union[pa.Table, np.ndarray]) -> Dict[str, str]:
        """
        Generates a schema (column: type) from a py arrow table.
        Args:
            data: py arrow table.
        Returns:
            schema: Dict[str,str]
        """

        if isinstance(data, pa.lib.Table):
            schema = data.schema
            feature_map = {}

            for feature, type_ in zip(schema.names, schema.types):
                feature_map[feature] = str(type_)

            return feature_map

        elif isinstance(data, np.ndarray):
            return {"numpy_dtype": str(data.dtype)}
