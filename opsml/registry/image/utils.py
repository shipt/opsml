from typing import List, Protocol
import pyarrow as pa
from enum import Enum
from opsml.registry.image.dataset import ImageDataset, ImageRecord
from concurrent.futures import ProcessPoolExecutor, as_completed
from opsml.helpers.logging import ArtifactLogger
import re

logger = ArtifactLogger.get_logger()


class ShardSize(Enum):
    KB = 1e3
    MB = 1e6
    GB = 1e9


class FileSystem(Protocol):
    ...


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class PyarrowImageWriter:
    def __init__(
        self,
        image_data: ImageDataset,
        file_system: FileSystem,
        dir_path: str,
    ):
        self.image_data = image_data
        self.file_system = file_system
        self.dir_path = dir_path

        shard_size = re.findall("[a-zA-Z]+", image_data.shard_size)

        if len(shard_size) > 0:
            try:
                self.shard_size = ShardSize[shard_size[0].upper()].value
            except KeyError:
                logger.error("Invalid shard size: {}", image_data.shard_size)
                logger.info("Defaulting to 512MB")
                self.shard_size = 512 * ShardSize.MB.value

    def _set_shard_size(self, shard_size: str):
        shard_num = re.findall("\d+", shard_size)
        shard_size = re.findall("[a-zA-Z]+", shard_size)

        if len(shard_size) > 0:
            try:
                self.shard_size = int(shard_num[0]) * ShardSize[shard_size[0].upper()].value
            except Exception as exc:
                logger.error("Invalid shard size: {}", shard_size)
                logger.info("Defaulting to 512MB")
                self.shard_size = 512 * ShardSize.MB.value

    def write_to_table(self, image_records: List[ImageRecord]) -> pa.Table:
        """Write image records to pyarrow table

        Args:
            image_records:
                `List[ImageRecord]`
            file_system:
                `FileSystem`
            dir_path:
                directory path to save to
        """
        records = []
        for record in image_records:
            with pa.input_stream(record.file_name) as stream:
                records.append(
                    {
                        "file_name": record.file_name,
                        "bytes": stream.read(),
                        "split_label": record.split,
                    }
                )
        table = pa.Table.from_pylist(records)

        return pa.Table.from_pylist(records)

    def write_dataset_to_table(self, image_data: ImageDataset, file_system: FileSystem, dir_path: str):
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
        record_chunks = list(chunks(image_data.metadata.records, 10))

        with ProcessPoolExecutor() as executor:
            future_to_table = {
                executor.submit(PyarrowImageWriter.write_to_table, chunk): chunk for chunk in record_chunks
            }
            for future in as_completed(future_to_table):
                try:
                    table = future.result()
                    # append to list of tables
                    record_tables.append(table)
                except Exception as exc:
                    logger.error("Exception occurred while writing to table: {}", exc)
