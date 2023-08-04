# pylint: disable=protected-access
from fastapi import APIRouter, Request

from fastapi.responses import RedirectResponse


router = APIRouter()


@router.get("/")
async def opsml_homepage(request: Request):
    return RedirectResponse(url="/opsml/models/list/")
