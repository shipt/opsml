import re
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union
from pydantic import BaseModel, ConfigDict, field_validator
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow.fs import LocalFileSystem

from opsml.helpers.logging import ArtifactLogger
from opsml.registry.data.types import yield_chunks
from opsml.registry.image.dataset import ImageDataset, ImageRecord

logger = ArtifactLogger.get_logger()

VALID_DATA = ImageDataset


class ShardSize(Enum):
    KB = 1e3
    MB = 1e6
    GB = 1e9


class FileSystem(Protocol):
    ...


class DatasetWriteInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: ImageDataset
    storage_filesystem: LocalFileSystem
    write_path: Path

    @field_validator("write_path", mode="before")
    @classmethod
    def convert_to_path(cls, write_path: Union[str, Path]) -> Path:
        return Path(write_path)


class PyarrowDatasetWriter:
    """Client side writer for pyarrow datasets"""

    def __init__(self, info: DatasetWriteInfo):
        """Instantiates a PyarrowDatasetWriter object

        Args:
            info:
                DatasetWriteInfo object
        """

        self.info = info
        self.shard_size = self._set_shard_size(info.data.shard_size)
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
            write_path = self.info.write_path / split_name / f"shard-{uuid.uuid4().hex}.parquet"

            pq.write_table(
                table=temp_table,
                where=write_path,
                filesystem=self.info.storage_filesystem,
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
        write_path = str(self.info.write_path / split_name)
        self.info.storage_filesystem.create_dir(write_path)

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
        """Writes image dataset to pyarrow tables"""
        # get splits first (can be None, or more than one)
        # Splits are saved to their own paths for quick access in the future
        splits = self.info.data.split_data()
        for name, split in splits:
            num_shards = int(max(1, split.size // self.shard_size))
            records_per_shard = len(split.records) // num_shards
            shard_chunks = list(yield_chunks(split.records, records_per_shard))

            # create split name path
            self.create_path(name)

            logger.info("Writing {} images to parquet for split {}", len(split.records), name)

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

        image_path = str(Path(f"{record.path}/{record.filename}"))
        with pa.input_stream(image_path) as stream:
            record = {
                "bytes": stream.read(),
                "split_label": record.split,
                "path": str(Path(record.split or "") / record.filename),
            }

        return record
