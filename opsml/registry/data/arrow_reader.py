from typing import List, Optional, Any, Tuple
import pyarrow.dataset as ds
from concurrent.futures import ProcessPoolExecutor, as_completed
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.data.types import yield_chunks, ALL_IMAGES

logger = ArtifactLogger.get_logger


class PyarrowDatasetReader:
    def __init__(
        self,
        paths: List[str],
        storage_filesystem: Any,
        write_dir: str,
        column_filter: Optional[str] = None,
        batch_size: int = 1000,
    ):
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
        self.paths = paths
        self.filesystem = storage_filesystem
        self.write_dir = write_dir
        self.filter = column_filter
        self.batch_size = batch_size

    def get_filtered_paths(self) -> List[str]:
        """Filter paths by filter. Can be used to load only a subset of data"""
        if self.filter is None:
            return self.paths
        else:
            return [path for path in self.paths if self.filter in path]

    def write_batch_to_file(self, arrow_batch: List[Any]) -> None:
        raise NotImplementedError

    def load_dataset(self) -> None:
        """Loads a pyarrow dataset and writes to file"""
        parquet_paths = self.get_filtered_paths()

        data = ds.dataset(
            source=parquet_paths,
            format="parquet",
            filesystem=self.filesystem,
        )

        for record in data.to_batches(batch_size=self.batch_size):
            file_names = record.column("file_name")
            image_bytes = record.column("bytes")
            split_label = record.column("split_label")
            batch = list(zip(file_names, image_bytes, split_label))
            self.write_batch_to_file(batch)


class ImageDatasetReader(PyarrowDatasetReader):
    def _write_data_to_images(self, files: List[Tuple[str, bytes, str]]) -> None:
        """Writes a list of pyarrow data to image files.

        Args:
            files:
                List of tuples containing file_name, image_bytes, and split_label
        """

        for record in files:
            file_name, image_bytes, split_label = record

            # write path
            if split_label == ALL_IMAGES:
                # all_images is a convention ImageDataset uses when no split_label is provided
                # we don't want to save back to this directory
                write_path = f"{self.write_dir}/{file_name}"
            else:
                write_path = f"{self.write_dir}/{split_label}/{file_name}"

            try:
                with open(write_path, "wb") as f:
                    f.write(image_bytes.as_py())

            except Exception as exc:
                logger.error("Exception occurred while writing to file: {}", exc)

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
