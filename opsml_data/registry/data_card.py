from typing import Dict, List, Optional, Union, Any

import numpy as np
import pandas as pd
import pyarrow as pa
from numpy.typing import NDArray
from pandas import DataFrame
from pyarrow import Table
from pydantic import BaseModel
from pyshipt_logging import ShiptLogging

from opsml_data.registry.formatter import ArrowTable, DataFormatter
from opsml_data.registry.models import RegistryRecord
from opsml_data.registry.storage import save_record_data_to_storage
from opsml_data.registry.splitter import DataSplitter, DataHolder

logger = ShiptLogging.get_logger(__name__)


class DataCard(BaseModel):
    """Create a data card class from data.

    Args:
        data (np.ndarray, pd.DataFrame, pa.Table): Data to use for
        data card.
        data_name (str): What to name the data
        team (str): Team that this data is associated with
        user_email (str): Email to associate with data card
        drift_report (pandas dataframe): Optional drift report generated by Drifter class
        data_splits (List of dictionaries): Optional list containing split logic. Defaults
        to None. Logic for data splits can be defined in the following two ways:

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

    Returns:
        Data card

    """

    data_name: str
    team: str
    user_email: str
    data: Union[NDArray, DataFrame, Table]
    drift_report: Optional[DataFrame] = None
    data_splits: Optional[List[Dict[str, Any]]] = None
    data_uri: Optional[str] = None
    drift_uri: Optional[str] = None
    version: Optional[int] = None
    feature_map: Optional[Dict[str, Union[str, None]]] = None
    data_type: Optional[str] = None
    uid: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = False

    @property
    def has_data_splits(self):
        return bool(self.data_splits)

    def split_data(self) -> Union[DataHolder, None]:

        """Loops through data splits and splits data either by indexing or
        column values

        Returns
            Class containing data splits
        """

        if not self.has_data_splits:
            return None

        else:
            data_splits: DataHolder = self.parse_data_splits()
            return data_splits

    def parse_data_splits(self) -> DataHolder:

        data_holder = DataHolder()
        for split in self.data_splits:
            label, data = DataSplitter(split_attributes=split).split(data=self.data)
            setattr(data_holder, label, data)

        return data_holder

    def __convert_and_save(
        self,
        data: Union[pd.DataFrame, pa.Table, np.ndarray],
        data_name: str,
        version: int,
        team: str,
    ) -> ArrowTable:

        """Converts data into a pyarrow table or numpy array and saves to gcs.

        Args:
            data (pd.DataFrame, pa.Table, np.array): Data to convert
            data_name (str): Name for data
            version (int): version of the data
            team (str): Name of team

        Returns:
            ArrowTable containing metadata
        """

        converted_data: ArrowTable = DataFormatter.convert_data_to_arrow(data=data)
        converted_data.feature_map = DataFormatter.create_table_schema(converted_data.table)
        storage_path = save_record_data_to_storage(
            data=converted_data.table,
            data_name=data_name,
            version=version,
            team=team,
        )
        converted_data.storage_uri = storage_path.gcs_uri

        return converted_data

    def create_registry_record(self, version: int) -> RegistryRecord:

        """Creates required metadata for registering the current data card.
        Implemented with a DataRegistry object.

        Args:
            Version (int): Version number for the current data card

        Returns:
            Regsitry metadata

        """

        data_artifact = self.__convert_and_save(
            data=self.data, data_name=self.data_name, version=version, team=self.team
        )

        if bool(self.drift_report):

            drift_artifact: ArrowTable = self.__convert_and_save(
                data=self.drift_report,
                data_name="drift_report",
                version=version,
                team=self.team,
            )
            drift_uri = drift_artifact.storage_uri
        else:
            drift_uri = None

        self.data_uri = data_artifact.storage_uri
        self.drift_uri = drift_uri
        self.data_type = data_artifact.table_type
        self.feature_map = data_artifact.feature_map
        self.version = version

        return RegistryRecord(
            data_name=self.data_name,
            team=self.team,
            data_uri=data_artifact.storage_uri,
            drift_uri=drift_uri,
            feature_map=data_artifact.feature_map,
            data_type=data_artifact.table_type,
            data_splits=self.data_splits,
            version=version,
            user_email=self.user_email,
        )
