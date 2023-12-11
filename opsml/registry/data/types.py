# pylint: disable=protected-access
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Union

import numpy as np
import pyarrow as pa
from pyarrow import dataset as ds
from pydantic import BaseModel, ConfigDict


def yield_chunks(list_: List[Any], size: int) -> Iterator[Any]:
    """Yield successive n-sized chunks from list.

    Args:
        list_:
            list to chunk
        size:
            size of chunks

    """
    for _, i in enumerate(range(0, len(list_), size)):
        yield list_[i : i + size]


def get_class_name(object_: object) -> str:
    """Parses object to get the fully qualified class name.
    Used during type checking to avoid unnecessary imports.

    Args:
        object_:
            object to parse
    Returns:
        fully qualified class name
    """
    klass = object_.__class__
    module = klass.__module__
    if module == "builtins":
        return klass.__qualname__  # avoid outputs like 'builtins.str'
    return module + "." + klass.__qualname__


# need for old v1 compat
class AllowedTableTypes(str, Enum):
    NDARRAY = "ndarray"
    ARROW_TABLE = "Table"
    PANDAS_DATAFRAME = "PandasDataFrame"
    POLARS_DATAFRAME = "PolarsDataFrame"
    DICTIONARY = "Dictionary"
    IMAGE_DATASET = "ImageDataset"


class AllowedDataType(str, Enum):
    PANDAS = "pandas.core.frame.DataFrame"
    PYARROW = "pyarrow.lib.Table"
    POLARS = "polars.dataframe.frame.DataFrame"
    NUMPY = "numpy.ndarray"
    IMAGE = "ImageDataset"
    DICT = "dict"
    SQL = "sql"
    PROFILE = "profile"


class ArrowTable(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table: Union[pa.Table, np.ndarray]  # type: ignore
    storage_uri: Optional[str] = None
    feature_map: Optional[Dict[str, Any]] = None


class PyArrowDataset:
    @property
    def to_batches(
        self,
        batch_size: int,
        columns=Optional[List[str]],
        filter=Optional[ds.Expression],
    ) -> pa.RecordBatch:
        pass
