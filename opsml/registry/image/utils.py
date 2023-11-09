from typing import List, Protocol, Tuple, Dict, Any
import pyarrow as pa
from enum import Enum
from opsml.registry.image.dataset import ImageDataset, ImageRecord
from concurrent.futures import ProcessPoolExecutor, as_completed
from opsml.helpers.logging import ArtifactLogger
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
    for i in range(0, len(lst), n):
        yield lst[i : i + n], i


class PyarrowWriterBase:
    def __init__(
        self,
        data: ImageDataset,
        file_system: FileSystem,
        write_path: str,
    ):
        self.data = data
        self.file_system = file_system
        self.write_path = write_path

        self.shard_size = self._set_shard_size(data.metadata.shard_size)

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

    def create_record(self, record: ImageRecord) -> Tuple[Dict[str, Any], int]:
        """Create record for pyarrow table
        
        Returns:
            Record dictionary and buffer size
        """
        raise NotImplementedError

    def _write_buffer(self, processed_records)
    def write_to_table(self, records: Tuple[List[ImageRecord], int]) -> pa.Table:
        """Write image records to pyarrow table

        Args:
            image_records:
                `List[ImageRecord]`
            file_system:
                `FileSystem`
            dir_path:
                directory path to save to
        """
        current_buffer_size = 0
        processed_records = []
        shard_name = records[1]

        for record in records[0]:
            record, size =self.create_record(record)
            processed_records.append(record)
            current_buffer_size += size

                if current_buffer_size >= self.shard_size:
                    temp_table = pa.Table.from_pylist(records)
                    pq.write_table(
                        table=temp_table,
                        where=f"{self.write_path}/shard_{shard_name}-{uuid.uuid4().hex}.parquet",
                        filesystem=self.storage_filesystem,
                    )
                    records = []
                    current_buffer_size = 0


# this can be extended to language datasets in the future
class PyarrowWriter:
    def __init__(
        self,
        data: ImageDataset,
        file_system: FileSystem,
        write_path: str,
    ):
        self.image_data = image_data
        self.file_system = file_system
        self.write_path = write_path
        self.shard_size = self._set_shard_size(image_data.metadata.shard_size)

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

    def write_to_table(self, records: Tuple[List[ImageRecord], int]) -> pa.Table:
        """Write image records to pyarrow table

        Args:
            image_records:
                `List[ImageRecord]`
            file_system:
                `FileSystem`
            dir_path:
                directory path to save to
        """
        current_buffer_size = 0
        processed_records = []
        shard_name = records[1]

        for record in records[0]:
            with pa.input_stream(record.file_name) as stream:
                records.append(
                    {
                        "file_name": record.file_name,
                        "bytes": stream.read(),
                        "split_label": record.split,
                    }
                )
                current_buffer_size += stream.size

                if current_buffer_size >= self.shard_size:
                    temp_table = pa.Table.from_pylist(records)
                    pq.write_table(
                        table=temp_table,
                        where=f"{self.write_path}/shard_{shard_name}-{uuid.uuid4().hex}.parquet",
                        filesystem=self.storage_filesystem,
                    )
                    records = []
                    current_buffer_size = 0

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
        record_tables = []
        record_chunks = list(chunks(self.image_data.metadata.records, 10))

        with ProcessPoolExecutor() as executor:
            future_to_table = {executor.submit(self.write_to_table, chunk): chunk for chunk in record_chunks}
            for future in as_completed(future_to_table):
                try:
                    table = future.result()
                    # append to list of tables
                    record_tables.append(table)
                except Exception as exc:
                    logger.error("Exception occurred while writing to table: {}", exc)
