from typing import List, Protocol, Tuple, Dict, Any, Optional, cast
import pyarrow as pa
from enum import Enum
from pathlib import Path
from opsml.registry.image.dataset import ImageDataset, ImageRecord, Split, ImageSplitHolder
from concurrent.futures import ProcessPoolExecutor, as_completed
from opsml.helpers.logging import ArtifactLogger
from opsml.registry.storage.storage_system import StorageClientType
from opsml.helpers.utils import FindPath
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
        yield lst[i : i + n], nbr


class PyarrowWriterBase:
    def __init__(
        self,
        data: ImageDataset,
        storage_client: StorageClientType,
        write_path: str,
    ):
        self.data = data
        self.storage_client = storage_client
        self.write_path = write_path
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

    def _create_record(self, record: ImageRecord) -> Tuple[Dict[str, Any], int]:
        """Create record for pyarrow table

        Returns:
            Record dictionary and buffer size
        """
        raise NotImplementedError

    def _write_buffer(
        self,
        records: List[Dict[str, Any]],
        shard_name: str,
        split_name: Optional[str] = None,
    ) -> None:
        temp_table = pa.Table.from_pylist(records)
        write_path = f"{self.write_path}/{split_name}/shard-{shard_name}-{uuid.uuid4().hex}.parquet"
        pq.write_table(
            table=temp_table,
            where=write_path,
            filesystem=self.storage_client.client,
        )

    def create_path(self, split_name: str) -> None:
        self.storage_client.create_directory(f"{self.write_path}/{split_name}")

    def write_to_table(
        self,
        records: Tuple[List[ImageRecord], int],
        split_name: Optional[str],
    ) -> pa.Table:
        """Write records to pyarrow table

        Args:
            records:
                `List[ImageRecord]`
        """

        # write different buffers for each split
        buffer_size = 0
        processed_records = []
        shard_name = records[1]

        # check directory exists
        self.create_path(split_name=records[0][0].split)

        for record in records[0]:
            arrow_record, size = self._create_record(record)
            processed_records[record.split].append(arrow_record)
            buffer_size += size

        # if there are records left, write to parquet
        self._write_buffer(processed_records, shard_name, split_name=record.split)

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
        # get splits first (can be None, or more than one
        splits = self.data.split_data()
        for name, split in splits:
            split = cast(Split, split)

            num_shards = max(1, split.size // self.shard_size)
            record_tables = []
            records_per_shard = len(split.records) // num_shards
            shard_chunks = list(chunks(split.records, records_per_shard))

        with ProcessPoolExecutor() as executor:
            future_to_table = {executor.submit(self.write_to_table, chunk, name): chunk for chunk in shard_chunks}
            for future in as_completed(future_to_table):
                try:
                    table = future.result()
                    # append to list of tables
                    record_tables.append(table)
                except Exception as exc:
                    logger.error("Exception occurred while writing to table: {}", exc)


# this can be extended to language datasets in the future
class PyarrowImageWriter(PyarrowWriterBase):
    def _create_record(self, record: ImageRecord) -> Tuple[Dict[str, Any], int]:
        """Create record for pyarrow table

        Returns:
            Record dictionary and buffer size
        """
        image_path = FindPath.find_filepath(record.file_name, self.data.image_dir)
        with pa.input_stream(image_path) as stream:
            record = {
                "file_name": record.file_name,
                "bytes": stream.read(),
                "split_label": record.split,
            }
            size = stream.size()

        return record, size
