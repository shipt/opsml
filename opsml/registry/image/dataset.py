# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import json
import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)

from opsml.helpers.logging import ArtifactLogger

logger = ArtifactLogger.get_logger()


class BBox(BaseModel):
    """Bounding box for an image

    Args:
        bbox:
            List of coordinates for bounding box
        categories:
            List of categories for bounding box
    """

    bbox: List[List[float]]
    categories: List[Union[str, int, float]]


class ImageRecord(BaseModel):
    """Image record to associate with image file

    Args:
        filename:
            Full path to the file
        caption:
            Optional caption for image
        categories:
            Optional list of categories for image
        objects:
            Optional `BBox` for the image
        split:
            Optional split for the image. It is expected that split is name of the subdirectory
            that contains the file.

            Example:
                If the image file is in `images/train/` then split should be `train`

    """

    filename: str
    path: str
    caption: Optional[str] = None
    categories: Optional[List[Union[str, int, float]]] = None
    objects: Optional[BBox] = None
    split: Optional[str] = None
    size: int

    @model_validator(mode="before")
    @classmethod
    def check_args(cls, data_args: Dict[str, Any]) -> Dict[str, Any]:
        parent_path = data_args.get("path")
        file_path = data_args.get("filename")
        size = data_args.get("size")

        # if reloading record
        if all([parent_path, file_path, size]):
            return data_args

        # For creating image record
        file_path = Path(file_path)
        if not file_path.exists():
            file_path = Path(os.path.join(parent_path, file_path.name))

        data_args["path"] = str(file_path.parent)
        data_args["filename"] = str(file_path.name)
        data_args["size"] = file_path.stat().st_size

        return data_args


class ImageSplitHolder(BaseModel):
    """Class for holding data objects"""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")


@dataclass
class Split:
    records: List[ImageRecord]
    size: int


class ImageMetadata(BaseModel):
    """Create Image metadata from a list of ImageRecords

    Args:
        records:
            List of ImageRecords
    """

    records: List[ImageRecord]

    def write_to_file(self, filename: str) -> None:
        """Write all records to file

        Args:
            filename:
                Path to file to write records to
        """
        with open(filename, "w", encoding="utf-8") as file_:
            for record in self.records:
                json.dump(record.model_dump(), file_)
                file_.write("\n")


class ImageDataset(BaseModel):

    """Create an image dataset from a directory of images and a metadata file


    Args:
        image_dir:
            Directory of images
        metadata:
            Metadata file for images. Can be a jsonl file or an ImageMetadata object
        split_filter:
            Optional label used to filter data when loading. Must match current dataset split labels
        batch_size:
            batch size to use when loading data
    """

    image_dir: str
    metadata: Union[str, ImageMetadata]
    shard_size: str = "512MB"
    split_filter: Optional[str] = None
    batch_size: int = 1000

    @field_validator("image_dir", mode="before")
    @classmethod
    def check_dir(cls, value: str) -> str:
        assert os.path.isdir(value), "image_dir must be a directory"

        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def check_metadata(cls, metadata: Union[str, ImageMetadata], info: ValidationInfo) -> Union[str, ImageMetadata]:
        """Validates if metadata is a jsonl file and if each record is valid"""
        if isinstance(metadata, str):
            # check metadata file is valid
            assert "jsonl" in metadata, "metadata must be a jsonl file"

            # metadata file should exist in image dir
            filepath = os.path.join(info.data.get("image_dir"), metadata)  # type: ignore

            assert os.path.isfile(filepath), f"metadata file {metadata} does not exist in image_dir"

            # read and validate each record in the jsonl file
            with open(filepath, "r", encoding="utf-8") as file_:
                records = []
                for line in file_:
                    records.append(ImageRecord(**json.loads(line)))
                metadata = ImageMetadata(records=records)

        return metadata

    def convert_metadata(self) -> None:
        """Converts metadata to jsonl file if metadata is an ImageMetadata object"""

        if isinstance(self.metadata, ImageMetadata):
            logger.info("convert metadata to jsonl file")
            filepath = os.path.join(self.image_dir, "metadata.jsonl")
            self.metadata.write_to_file(filepath)

    @cached_property
    def size(self) -> int:
        return sum([record.size for record in self.metadata.records])

    @cached_property
    def splits(self) -> List[str]:
        """Returns list of unique splits"""
        return list(set([record.split for record in self.records]))

    def split_data(self) -> Dict[str, Split]:
        """Loops through ImageRecords and splits them based on specified split

        Returns:
            `ImageSplitHolder`
        """

        splits = {}
        data_holder = ImageSplitHolder()

        for record in self.metadata.records:
            if record.split not in splits:
                splits[record.split] = Split(records=[record], size=record.size)

            else:
                splits[record.split].records.append(record)
                splits[record.split].size += record.size

        for split_name, split in splits.items():
            setattr(data_holder, split_name, split)

        return data_holder
