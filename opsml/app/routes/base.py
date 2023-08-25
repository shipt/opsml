# pylint: disable=protected-access

# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from fastapi import APIRouter, Request

from fastapi.responses import RedirectResponse
from opsml.helpers.logging import ArtifactLogger
from opsml.model.challenger import ModelChallenger
from opsml.registry import CardInfo, CardRegistries, CardRegistry, ModelCard, RunCard


logger = ArtifactLogger.get_logger(__name__)

router = APIRouter()


@router.get("/")
async def opsml_homepage(request: Request):
    return RedirectResponse(url="/opsml/models/list/")
