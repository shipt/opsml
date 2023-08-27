# pylint: disable=protected-access
# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from typing import Union

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from opsml.app.core.config import config
from opsml.app.core.dependencies import verify_token
from opsml.app.routes.pydantic_models import (
    AddCardRequest,
    AddCardResponse,
    ListCardRequest,
    ListCardResponse,
    UidExistsRequest,
    UidExistsResponse,
    UpdateCardRequest,
    UpdateCardResponse,
    VersionRequest,
    VersionResponse,
)
from opsml.app.routes.utils import replace_proxy_root
from opsml.helpers.logging import ArtifactLogger
from opsml.registry import CardRegistry
from opsml.registry.sql.card_validator import card_validator

logger = ArtifactLogger.get_logger(__name__)

router = APIRouter()


@router.post("/cards/uid", response_model=UidExistsResponse, name="check_uid")
def check_uid(
    request: Request,
    payload: UidExistsRequest = Body(...),
) -> UidExistsResponse:
    """Checks if a uid already exists in the database"""

    if card_validator.check_uid_exists(
        uid=payload.uid,
        table_to_check=payload.table_name,
    ):
        return UidExistsResponse(uid_exists=True)
    return UidExistsResponse(uid_exists=False)


@router.post("/cards/version", response_model=Union[VersionResponse, UidExistsResponse], name="version")
def set_version(
    request: Request,
    payload: VersionRequest = Body(...),
) -> Union[VersionResponse, UidExistsResponse]:
    """Sets the version for an artifact card"""
    table_for_registry = payload.table_name.split("_")[1].lower()
    registry: CardRegistry = getattr(request.app.state.registries, table_for_registry)

    version = registry._registry.set_version(
        name=payload.name,
        team=payload.team,
        supplied_version=payload.version,
        version_type=payload.version_type,
        pre_tag=payload.pre_tag,
        build_tag=payload.build_tag,
    )

    return VersionResponse(version=version)


@router.post("/cards/list", response_model=ListCardResponse, name="list_cards")
def list_cards(
    request: Request,
    payload: ListCardRequest = Body(...),
) -> ListCardResponse:
    """Lists a Card"""

    try:
        table_for_registry = payload.table_name.split("_")[1].lower()
        registry: CardRegistry = getattr(request.app.state.registries, table_for_registry)
        logger.info("Listing cards with request: %s", payload.dict())

        cards = registry.list_cards(
            uid=payload.uid,
            name=payload.name,
            team=payload.team,
            version=payload.version,
            max_date=payload.max_date,
            limit=payload.limit,
            tags=payload.tags,
            as_dataframe=False,
            ignore_release_candidates=payload.ignore_release_candidates,
        )

        if config.is_proxy:
            cards = [
                replace_proxy_root(
                    card=card,
                    storage_root=config.STORAGE_URI,
                    proxy_root=str(config.proxy_root),
                )
                for card in cards
            ]

        return ListCardResponse(cards=cards)

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"""Error listing cards. {error}""",
        ) from error


@router.post(
    "/cards/create",
    response_model=AddCardResponse,
    name="create_card",
    dependencies=[Depends(verify_token)],
)
def add_card(
    request: Request,
    payload: AddCardRequest = Body(...),
) -> AddCardResponse:
    """Adds Card record to a registry"""

    table_for_registry = payload.table_name.split("_")[1].lower()
    registry: CardRegistry = getattr(request.app.state.registries, table_for_registry)

    logger.info("Creating card: %s", payload.dict())

    registry._registry._add_and_commit(card=payload.card)
    return AddCardResponse(registered=True)


@router.post(
    "/cards/update",
    response_model=UpdateCardResponse,
    name="update_card",
    dependencies=[Depends(verify_token)],
)
def update_card(
    request: Request,
    payload: UpdateCardRequest = Body(...),
) -> UpdateCardResponse:
    """Updates a specific artifact card"""
    table_for_registry = payload.table_name.split("_")[1].lower()
    registry: CardRegistry = getattr(request.app.state.registries, table_for_registry)
    registry._registry.update_card_record(card=payload.card)

    logger.info("Updated card: %s", payload.dict())

    return UpdateCardResponse(updated=True)
