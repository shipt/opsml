# pylint: disable=protected-access
import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


# Constants
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TEMPLATE_PATH = os.path.abspath(os.path.join(PARENT_DIR, "templates"))


templates = Jinja2Templates(directory=TEMPLATE_PATH)

router = APIRouter()


@router.get("/")
async def opsml_homepage(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})
