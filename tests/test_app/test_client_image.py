import os
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

from opsml.registry import CardRegistries, DataCard
from opsml.registry.image import ImageDataset, ImageMetadata, ImageRecord


@pytest.mark.skipif(sys.platform == "win32", reason="No wn_32 test")
def test_register_data(api_registries: CardRegistries, create_image_dataset: Tuple[str, List[ImageRecord]]):
    """tests imagedataset saving and loading without splits"""

    # create images
    image_dataset_path, records = create_image_dataset

    # create data card
    registry = api_registries.data

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
