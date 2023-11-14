# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import json
import os
from typing import List, Optional, Union, Protocol, Dict, Any
from pathlib import Path
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator
from opsml.helpers.logging import ArtifactLogger


logger = ArtifactLogger.get_logger()


class DataSplit(Protocol):
    """Protocol for a data split"""

    @property
    def label(self) -> str:
        """Label for the split"""
        ...

    @property
    def directory(self) -> Optional[str]:
        """Directory for the split"""
        ...


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
        file_name:
            Name of image file
        caption:
            Optional caption for image
        categories:
            Optional list of categories for image
        objects:
            Optional `BBox` for the image
        split:
            Optional split for the image

    """

    file_name: str
    parent_dir: str
    caption: Optional[str] = None
    categories: Optional[List[Union[str, int, float]]] = None
    objects: Optional[BBox] = None
    split: Optional[str] = None

    @model_validator(mode="before")
    def check_args(cls, values: Dict[str, Any]):
        file_path = Path(values.get("file_name"))

        values["parent_dir"] = str(file_path.parent)
        values["file_name"] = str(file_path.name)

        return values


class ImageMetadata(BaseModel):
    """Create Image metadata from a list of ImageRecords

    Args:
        records:
            List of ImageRecords
    """

    records: List[ImageRecord]

    def write_to_file(self, file_name: str) -> None:
        with open(file_name, "w", encoding="utf-8") as file_:
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

    """

    image_dir: str
    metadata: Union[str, ImageMetadata]
    splits_defined: bool = False
    shard_size: str = "512MB"

    @field_validator("image_dir", mode="before")
    def check_dir(cls, value):
        assert os.path.isdir(value), "image_dir must be a directory"

        return value

    @field_validator("metadata", mode="before")
    def check_metadata(cls, value, info: ValidationInfo):
        """Validates if metadata is a jsonl file and if each record is valid"""
        if isinstance(value, str):
            # check metadata file is valid
            assert "jsonl" in value, "metadata must be a jsonl file"

            # file should exist in image dir
            filepath = os.path.join(info.data.get("image_dir"), value)  # type: ignore

            assert os.path.isfile(filepath), f"metadata file {value} does not exist in image_dir"

            # read and validate each record in the jsonl file
            # tag: rust-op
            with open(filepath, "r", encoding="utf-8") as file_:
                for line in file_:
                    ImageRecord(**json.loads(line))

        return value

    def convert_metadata(self):
        """Converts metadata to jsonl file if metadata is an ImageMetadata object"""

        if isinstance(self.metadata, ImageMetadata):
            logger.info("convert metadata to jsonl file")
            filepath = os.path.join(self.image_dir, "metadata.jsonl")

            # tag: rust-op
            self.metadata.write_to_file(filepath)

    def update_split_labels(self, splits: List[DataSplit]) -> None:
        """Updates split labels for each image record

        Args:
            splits:
                List of DataSplit objects

        """

        if not self.splits_defined:
            for record in self.metadata.records:
                if record.split is None:
                    for split in splits:
                        if split.directory in record.file_name:
                            record.split = split.label

            self.splits_defined = True
