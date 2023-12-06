from typing import List, Protocol, Dict, Any, Optional
import pyarrow as pa
from enum import Enum
from pathlib import Path
from opsml.registry.image.dataset import ImageDataset, ImageRecord
from concurrent.futures import ProcessPoolExecutor, as_completed
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.storage.storage_system import StorageClientType
import pyarrow.parquet as pq
from pyarrow.fs import LocalFileSystem
import re
import uuid
from opsml.registry.data.types import yield_chunks

logger = ArtifactLogger.get_logger()

VALID_DATA = ImageDataset


class ShardSize(Enum):
    KB = 1e3
    MB = 1e6
    GB = 1e9


class FileSystem(Protocol):
    ...


class PyarrowDatasetWriter:
    """Client side writer for pyarrow datasets"""

    def __init__(
        self,
        data: ImageDataset,
        storage_filesystem: LocalFileSystem,
        write_path: str,
    ):
        self.data = data
        self.storage_filesystem = storage_filesystem
        self.write_path = Path(write_path)
        self.shard_size = self._set_shard_size(data.shard_size)
        self.parquet_paths = []

    def _set_shard_size(self, shard_size: str) -> int:
        """
        Sets the shard size for the dataset. Defaults to 512MB if invalid shard size is provided

        Args:
            shard_size:
                `str` shard size in the format of <number><unit> e.g. 512MB, 1GB, 2KB

        Returns:
            int
        """
        shard_num = re.findall("\d+", shard_size)
        shard_size = re.findall("[a-zA-Z]+", shard_size)

        try:
            return int(shard_num[0]) * ShardSize[shard_size[0].upper()].value

        # can be index or keyerror
        except Exception as exc:
            logger.error("Invalid shard size: {}, error: {}", shard_size, exc)
            logger.info("Defaulting to 512MB")
            return 512 * ShardSize.MB.value

    def _create_record(self, record: ImageRecord) -> Dict[str, Any]:
        """Create record for pyarrow table

        Returns:
            Record dictionary and buffer size
        """
        raise NotImplementedError

    def _write_buffer(self, records: List[Dict[str, Any]], split_name: str) -> str:
        try:
            temp_table = pa.Table.from_pylist(records)
            write_path = self.write_path / split_name / f"shard-{uuid.uuid4().hex}.parquet"

            pq.write_table(
                table=temp_table,
                where=write_path,
                filesystem=self.storage_filesystem,
            )

            return str(write_path)

        except Exception as exc:
            logger.error("Exception occurred while writing to table: {}", exc)
            raise exc

    def create_path(self, split_name: str) -> None:
        """Create path to write files. If split name is defined, create split dir
        Args:
        split_name:
            `str` name of split
        """

        self.storage_filesystem.create_dir(str(self.write_path / split_name))

    def write_to_table(self, records: List[ImageRecord], split_name: Optional[str]) -> str:
        """Write records to pyarrow table

        Args:
            records:
                `List[ImageRecord]`

            split_name:
                `str` name of split
        """

        processed_records = []
        for record in records:
            arrow_record = self._create_record(record)
            processed_records.append(arrow_record)

        return self._write_buffer(processed_records, split_name)

    def write_dataset_to_table(self) -> List[str]:
        """Writes image dataset to pyarrow tables

        Args:
            image_data:
                `ImageDataset`
            file_system:
                `FileSystem`
            dir_path:
                directory path to save to
        """
        # get splits first (can be None, or more than one)
        # Splits are saved to their own paths for quick access in the future
        splits = self.data.split_data()
        for name, split in splits:
            num_shards = int(max(1, split.size // self.shard_size))
            records_per_shard = len(split.records) // num_shards
            shard_chunks = list(yield_chunks(split.records, records_per_shard))

            # create split name path
            self.create_path(name)

            # don't want the overhead for one shard
            if num_shards == 1:
                for chunk in shard_chunks:
                    self.parquet_paths.append(self.write_to_table(chunk, name))

            else:
                with ProcessPoolExecutor() as executor:
                    future_to_table = {
                        executor.submit(self.write_to_table, chunk, name): chunk for chunk in shard_chunks
                    }
                    for future in as_completed(future_to_table):
                        try:
                            self.parquet_paths.append(future.result())
                        except Exception as exc:
                            logger.error("Exception occurred while writing to table: {}", exc)
                            raise exc

        return self.parquet_paths


# this can be extended to language datasets in the future
class ImageDatasetWriter(PyarrowDatasetWriter):
    def _create_record(self, record: ImageRecord) -> Dict[str, Any]:
        """Create record for pyarrow table

        Returns:
            Record dictionary and buffer size
        """

        image_path = str(Path(f"{record.path}/{record.file_name}"))
        with pa.input_stream(image_path) as stream:
            record = {
                "file_name": record.file_name,
                "bytes": stream.read(),
                "split_label": record.split,
            }

        return record
