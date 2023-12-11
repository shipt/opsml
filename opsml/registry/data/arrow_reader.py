from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union, Dict

import pyarrow.dataset as ds
from pyarrow.fs import LocalFileSystem
from pydantic import BaseModel, ConfigDict

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.data.types import yield_chunks

logger = ArtifactLogger.get_logger()


class DatasetReadInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    paths: Union[List[str], str]
    storage_filesystem: LocalFileSystem
    write_dir: str
    split_labels: List[str]
    column_filter: Optional[str] = None
    batch_size: int = 1000


class PyarrowDatasetReader:
    def __init__(self, info: DatasetReadInfo):
        """Instantiates a PyarrowReaderBase object

        Args:
            info:
                DatasetReadInfo object
        """
        self.info = info
        self.filtered_paths = self.get_filtered_paths()

    @property
    def dataset(self) -> ds.Dataset:
        """Returns a pyarrow dataset"""
        return ds.dataset(
            source=self.filtered_paths,
            format="parquet",
            filesystem=self.info.storage_filesystem,
        )

    def get_filtered_paths(self) -> Union[str, List[str]]:
        """Filter paths by filter. Can be used to load only a subset of data"""
        if self.info.column_filter is None:
            return self.info.paths

        return [path for path in self.info.paths if self.info.column_filter in path]

    def check_write_paths_exist(self) -> None:
        """Checks if local path for writing exists and creates if it doesn't"""
        path = Path(self.info.write_dir)
        splits = list(self.info.column_filter or self.info.split_labels)

        if bool(splits):
            for split in splits:
                dir_path = path / split
                dir_path.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)

    def write_batch_to_file(self, arrow_batch: List[Dict[str, Any]]) -> None:
        raise NotImplementedError

    def steam_batches(self) -> List[Dict[str, Any]]:
        """Streams batches from dataset"""

        for record_batch in self.dataset.to_batches(
            batch_size=self.info.batch_size,
        ):
            yield record_batch.to_pylist()

    def load_dataset(self) -> None:
        """Loads a pyarrow dataset and writes to file"""
        self.check_write_paths_exist()

        for record_batch in self.dataset.to_batches(
            batch_size=self.info.batch_size,
        ):
            self.write_batch_to_file(record_batch.to_pylist())


class ImageDatasetReader(PyarrowDatasetReader):
    def _write_data_to_images(self, files: List[Dict[str, Any]]) -> None:
        """Writes a list of pyarrow data to image files.

        Args:
            files:
                List of tuples containing filename, image_bytes, and split_label
        """

        for record in files:
            write_path = f"{self.info.write_dir}/{record['path']}"

            try:
                with open(write_path, "wb") as file_:
                    file_.write(record["bytes"])  # type: ignore

            except Exception as exc:
                logger.error("Exception occurred while writing to file: {}", exc)
                raise exc

    def write_batch_to_file(self, arrow_batch: List[Dict[str, Any]]) -> None:
        """Write image data to file

        Args:
            arrow_batch:
                List of pyarrow file data
        """

        # get chunks
        chunks = list(yield_chunks(arrow_batch, 100))

        # don't want overhead of instantiating a process pool if we don't need to
        if len(chunks) == 1:
            self._write_data_to_images(chunks[0])

        else:
            with ProcessPoolExecutor() as executor:
                future_to_table = {executor.submit(self._write_data_to_images, chunk): chunk for chunk in chunks}
                for future in as_completed(future_to_table):
                    try:
                        _ = future.result()
                    except Exception as exc:
                        logger.error("Exception occurred while writing to file: {}", exc)
                        raise exc
