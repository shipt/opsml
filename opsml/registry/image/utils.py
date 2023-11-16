from typing import List, Protocol, Tuple, Dict, Any, Optional, cast
import pyarrow as pa
from enum import Enum
from pathlib import Path
from opsml.registry.image.dataset import ImageDataset, ImageRecord, Split, ImageSplitHolder
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.storage.storage_system import StorageClientType
import pyarrow.parquet as pq
import re
import uuid

logger = ArtifactLogger.get_logger()

VALID_DATA = ImageDataset


class ShardSize(Enum):
    KB = 1e3
    MB = 1e6
    GB = 1e9


class FileSystem(Protocol):
    ...


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for nbr, i in enumerate(range(0, len(lst), n)):
        yield lst[i : i + n]


class PyarrowWriterBase:
    def __init__(
        self,
        data: ImageDataset,
        storage_client: StorageClientType,
        write_path: str,
    ):
        self.data = data
        self.storage_client = storage_client
        self.write_path = Path(write_path)
        self.shard_size = self._set_shard_size(data.shard_size)

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

    def _write_buffer(self, records: List[Dict[str, Any]], split_name: Optional[str] = None) -> None:
        temp_table = pa.Table.from_pylist(records)

        if split_name is not None:
            write_path = self.write_path / split_name / f"shard-{uuid.uuid4().hex}.parquet"
        else:
            write_path = self.write_path / f"shard-{uuid.uuid4().hex}.parquet"

        pq.write_table(
            table=temp_table,
            where=write_path,
            filesystem=self.storage_client.client,
        )

    def create_split_path(self, split_name: str) -> None:
        if split_name is None:
            return self.storage_client.create_directory(str(self.write_path))
        return self.storage_client.create_directory(str(self.write_path / split_name))

    def write_to_table(self, records: List[ImageRecord], split_name: Optional[str]) -> pa.Table:
        """Write records to pyarrow table

        Args:
            records:
                `List[ImageRecord]`
        """

        processed_records = []

        for record in records:
            arrow_record = self._create_record(record)
            processed_records.append(arrow_record)

        self._write_buffer(processed_records, split_name)

    def write_dataset_to_table(self):
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
            # check directory exists
            self.create_split_path(split_name=name)

            split = cast(Split, split)

            num_shards = max(1, split.size // self.shard_size)
            records_per_shard = len(split.records) // num_shards
            shard_chunks = list(chunks(split.records, records_per_shard))

            # don't want the overhead for one shard
            if num_shards == 1:
                for chunk in shard_chunks:
                    self.write_to_table(chunk, name)

            else:
                with ProcessPoolExecutor() as executor:
                    future_to_table = {
                        executor.submit(self.write_to_table, chunk, name): chunk for chunk in shard_chunks
                    }
                    for future in as_completed(future_to_table):
                        try:
                            _ = future.result()
                        except Exception as exc:
                            logger.error("Exception occurred while writing to table: {}", exc)


# this can be extended to language datasets in the future
class PyarrowImageWriter(PyarrowWriterBase):
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
