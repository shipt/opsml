from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, List, Optional, Tuple
from pydantic import BaseModel
import pyarrow.dataset as ds
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.data.types import ALL_IMAGES, yield_chunks
from pyarrow.fs import LocalFileSystem
from pathlib import Path

logger = ArtifactLogger.get_logger()


class ReadDatasetInfo(BaseModel):
    paths: List[str]
    storage_filesystem: LocalFileSystem
    write_dir: str
    splits: List[str]
    column_filter: Optional[str] = None
    batch_size: int = 1000


class PyarrowDatasetReader:
    def __init__(self, info: ReadDatasetInfo):
        """Instantiates a PyarrowReaderBase object

        Args:
            paths:
                `List[str]` paths to read from
            storage_client:
                `StorageClientType` storage client to use
            write_dir:
                `str` directory to write to
            column_filter:
                Optional filter to use when loading data
        """
        self.info = info

    def get_filtered_paths(self) -> List[str]:
        """Filter paths by filter. Can be used to load only a subset of data"""
        if self.info.column_filter is None:
            return self.info.paths
        else:
            return [path for path in self.info.paths if self.info.column_filter in path]

    def check_write_paths_exist(self) -> None:
        """Checks if local path for writing exists and creates if it doesn't"""
        path = Path(self.info.write_dir)
        splits = list(self.info.column_filter or self.info.splits)

        for split in splits:
            if split != ALL_IMAGES:
                path = path / split
            path.mkdir(parents=True, exist_ok=True)

    def write_batch_to_file(self, arrow_batch: List[Any]) -> None:
        raise NotImplementedError

    def load_dataset(self) -> None:
        """Loads a pyarrow dataset and writes to file"""
        parquet_paths = self.get_filtered_paths()

        data = ds.dataset(
            source=parquet_paths,
            format="parquet",
            filesystem=self.info.filesystem,
        )

        for record in data.to_batches(batch_size=self.info.batch_size):
            filenames = record.column("filename")
            image_bytes = record.column("bytes")
            split_label = record.column("split_label")
            batch = list(zip(filenames, image_bytes, split_label))
            self.write_batch_to_file(batch)


class ImageDatasetReader(PyarrowDatasetReader):
    def _write_data_to_images(self, files: List[Tuple[str, bytes, str]]) -> None:
        """Writes a list of pyarrow data to image files.

        Args:
            files:
                List of tuples containing filename, image_bytes, and split_label
        """

        for record in files:
            filename, image_bytes, split_label = record

            # write path
            if split_label == ALL_IMAGES:
                # all_images is a convention ImageDataset uses when no split_label is provided
                # we don't want to save back to this directory
                write_path = f"{self.info.write_dir}/{filename}"
            else:
                write_path = f"{self.info.write_dir}/{split_label}/{filename}"

            try:
                with open(write_path, "wb") as f:
                    f.write(image_bytes.as_py())

            except Exception as exc:
                logger.error("Exception occurred while writing to file: {}", exc)
                raise exc

    def write_batch_to_file(self, arrow_batch: List[Any]) -> None:
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
