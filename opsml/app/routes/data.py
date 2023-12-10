# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
from typing import Iterator, Optional, cast

from fastapi import APIRouter, Body, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from opsml.app.routes.pydantic_models import CardRequest, CompareCardRequest
from opsml.app.routes.route_helpers import DataRouteHelper
from opsml.app.routes.utils import error_to_500
from opsml.profile.profile_data import DataProfiler
from opsml.registry.cards.data import DataCard
from opsml.registry.sql.registry import CardRegistry
from opsml.app.routes.utils import verify_path

# Constants
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATE_PATH = os.path.abspath(os.path.join(PARENT_DIR, "templates"))


templates = Jinja2Templates(directory=TEMPLATE_PATH)

CHUNK_SIZE = 31457280
data_route_helper = DataRouteHelper()
router = APIRouter()


@router.get("/data/list/", response_class=HTMLResponse)
@error_to_500
async def data_list_homepage(request: Request, team: Optional[str] = None) -> HTMLResponse:
    """UI home for listing models in model registry

    Args:
        request:
            The incoming HTTP request.
        team:
            The team to query
    Returns:
        200 if the request is successful. The body will contain a JSON string
        with the list of models.
    """
    return data_route_helper.get_homepage(request=request, team=team)  # type: ignore[return-value]


@router.get("/data/versions/", response_class=HTMLResponse)
@error_to_500
async def data_versions_page(
    request: Request,
    load_profile: bool = False,
    name: Optional[str] = None,
    version: Optional[str] = None,
) -> HTMLResponse:
    if name is None:
        return RedirectResponse(url="/opsml/data/list/")  # type: ignore[return-value]

    return data_route_helper.get_versions_page(  # type: ignore[return-value]
        request=request,
        name=name,
        version=version,
        load_profile=load_profile,
    )


@router.get("/data/versions/uid/")
@error_to_500
async def data_versions_uid_page(
    request: Request,
    uid: str,
) -> HTMLResponse:
    registry: CardRegistry = request.app.state.registries.data
    selected_data = registry.list_cards(uid=uid)[0]

    return await data_versions_page(  # type: ignore
        request=request,
        name=selected_data["name"],
        version=selected_data["version"],
    )


@router.get("/data/profile/view/", response_class=HTMLResponse)
@error_to_500
async def data_versions_profile_page(
    request: Request,
    name: str,
    version: str,
    profile_uri: Optional[str] = None,
) -> HTMLResponse:
    return data_route_helper.get_data_profile_page(  # type: ignore[return-value]
        request=request,
        name=name,
        version=version,
        profile_uri=profile_uri,
    )


@router.post("/data/profile", name="download_data_profile")
def download_data_profile(
    request: Request,
    payload: CardRequest = Body(...),
) -> StreamingResponse:
    """Downloads a datacard profile"""

    registry: CardRegistry = request.app.state.registries.data
    datacard = cast(
        DataCard,
        registry.load_card(
            name=payload.name,
            version=payload.version,
            uid=payload.uid,
        ),
    )

    if datacard.data_profile is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No data profile available for datacard uid:{payload.uid}",
        )

    try:
        storage_client = request.app.state.storage_client
        return StreamingResponse(
            storage_client.iterfile(
                file_path=datacard.metadata.uris.profile_html_uri,
                chunk_size=CHUNK_SIZE,
            ),
            media_type="application/octet-stream",
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error downloading the file. {error}",
        ) from error


def iterfile(file_path: str) -> Iterator[bytes]:
    with open(file_path, mode="rb") as file_like:  #
        yield from file_like
    os.remove(file_path)


@router.post("/data/compare", name="compare_data_profile")
def compare_data_profile(
    request: Request,
    payload: CompareCardRequest = Body(...),
) -> StreamingResponse:
    """Runs a data comparison for multiple data profiles"""

    registry: CardRegistry = request.app.state.registries.data

    profiles = []

    # make mypy happy
    if payload.uids is not None and bool(payload.uids):
        for uid in payload.uids:
            datacard = cast(DataCard, registry.load_card(uid=uid))

            if datacard.data_profile is not None:
                profiles.append(datacard.data_profile.get_description())
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"No data profile detected for {datacard.uid}",
                )

    elif payload.versions is not None and bool(payload.versions):
        for version in payload.versions:
            datacard = cast(
                DataCard,
                registry.load_card(name=payload.name, version=version),
            )
            if datacard.data_profile is not None:
                profiles.append(datacard.data_profile.get_description())
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"No data profile detected for {datacard.uid}",
                )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DataCard versions or uids must be lists",
        )

    try:
        comparison = DataProfiler.compare_reports(reports=profiles)
        file_path = f"{datacard.name}-{datacard.team}-comparison.html"
        comparison.to_file(file_path)

        return StreamingResponse(
            iterfile(file_path=file_path),
            media_type="application/octet-stream",
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error downloading the file. {error}",
        ) from error


@router.get("/data/stream", name="stream_data")
def download_file(
    request: Request,
    read_path: str,
    batch_size: int,
    column_filter: Optional[str] = None,
) -> StreamingResponse:
    """Streams data from storage. Used by Image and Text datasets for streaming batches

    Args:
        request:
            request object
        read_path:
            path to file
        batch_size:
            batch size
        column_filter:
            column filter

    Returns:
        Streaming file response
    """

    # prevent arbitrary file downloads
    # Files can only be downloaded from registry paths
    verify_path(path=read_path)

    try:
        storage_client = request.app.state.storage_client
        return StreamingResponse(
            storage_client.iterfile(
                file_path=read_path,
                chunk_size=CHUNK_SIZE,
            ),
            media_type="application/octet-stream",
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error downloading the file. {error}",
        ) from error
