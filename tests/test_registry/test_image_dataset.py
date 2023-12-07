from typing import Dict, Tuple, List
import os
from pathlib import Path
from opsml.registry.cards import DataCard
from opsml.registry.sql.registry import CardRegistry
from opsml.registry.image import ImageDataset, ImageRecord, ImageMetadata
from pydantic_core._pydantic_core import ValidationError
import pytest
import tempfile

# these examples are pulled from huggingface
# the aim is to have as much parity as possible


def test_image_record():
    record = {
        "filename": "tests/assets/image_dataset/cats.jpg",
        "caption": "This is a second value of a text feature you added to your images",
    }

    record = ImageRecord(**record)
    assert record.filename == "cats.jpg"

    bbox_record = {
        "filename": "tests/assets/image_dataset/cat2.jpg",
        "objects": {"bbox": [[160.0, 31.0, 248.0, 616.0], [741.0, 68.0, 202.0, 401.0]], "categories": [2, 2]},
    }

    record = ImageRecord(**bbox_record)
    assert record.filename == "cat2.jpg"
    assert record.objects.bbox == [[160.0, 31.0, 248.0, 616.0], [741.0, 68.0, 202.0, 401.0]]


def test_image_metadata():
    records = [
        {
            "filename": "tests/assets/image_dataset/cats.jpg",
            "caption": "This is a second value of a text feature you added to your images",
        },
        {
            "filename": "tests/assets/image_dataset/cat2.jpg",
            "objects": {"bbox": [[810.0, 100.0, 57.0, 28.0]], "categories": [1]},
        },
    ]

    metadata = ImageMetadata(records=records)

    assert metadata.records[1].filename == "cat2.jpg"
    assert metadata.records[1].objects.bbox == [[810.0, 100.0, 57.0, 28.0]]

    with tempfile.TemporaryDirectory() as tmp_dir:
        filename = os.path.join(tmp_dir, "metadata.jsonl")
        metadata.write_to_file(filename)
        assert os.path.exists(filename)


def test_image_dataset():
    ImageDataset(
        image_dir="tests/assets/image_dataset",
        metadata="metadata.jsonl",
    )

    # fail if file doesn't exists
    with pytest.raises(ValidationError) as ve:
        ImageDataset(
            image_dir="tests/assets/image_dataset",
            metadata="blah.jsonl",
        )
    ve.match("metadata file blah.jsonl does not exist")

    # fail on non-json
    with pytest.raises(ValidationError) as ve:
        ImageDataset(
            image_dir="tests/assets/image_dataset",
            metadata="metadata.txt",
        )
    ve.match("metadata must be a jsonl file")


def test_register_data(db_registries: Dict[str, CardRegistry], create_image_dataset: Tuple[str, List[ImageRecord]]):
    # create images
    image_dataset_path, records = create_image_dataset

    # create data card
    registry = db_registries["data"]

    image_dataset = ImageDataset(
        image_dir=image_dataset_path,
        metadata=ImageMetadata(records=records),
    )

    data_card = DataCard(
        data=image_dataset,
        name="test_dataset",
        team="mlops",
        user_email="mlops.com",
    )

    registry.register_card(card=data_card)

    loaded_card = registry.load_card(uid=data_card.uid)
    loaded_card.data.image_dir = f"{loaded_card.data.image_dir}/download"
    loaded_card.load_data()

    assert os.path.isdir(loaded_card.data.image_dir)

    # count number for files in image_dir
    p = Path(loaded_card.data.image_dir).glob("**/*")
    nbr_downloaded = len([x for x in p if x.is_file() and not x.name.startswith("metadata")])
    assert nbr_downloaded == len(records)


#
# loaded_card = registry.load_card(uid=data_card.uid)
# loaded_card.data.image_dir = "test_image_dir"
# loaded_card.load_data()
#
# assert os.path.isdir(loaded_card.data.image_dir)
# meta_path = os.path.join(loaded_card.data.image_dir, "metadata.jsonl")
# assert os.path.exists(meta_path)
