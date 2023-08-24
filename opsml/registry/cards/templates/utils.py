from typing import List
import os
from opsml.registry.cards import DataCard, ModelCard, RunCard
from jinja2 import FileSystemLoader, Environment


DIR_PATH = os.path.dirname(__file__)
AUDIT_TEMPLATE_PATH = os.path.join(DIR_PATH, "audit_card.yaml")
AUDIT_TEMPLATE_HTML_FILE = "report-copy.html"


def render_audit_template(models: List[ModelCard], data: List[DataCard], runs: List[RunCard]):
    from opsml.registry.sql.settings import settings

    template_env = Environment(
        loader=FileSystemLoader(searchpath=DIR_PATH),
    )
    template = template_env.get_template(AUDIT_TEMPLATE_HTML_FILE)

    output_text = template.render(
        zip=zip,
        models=models,
        data=data,
        runs=runs,
        tracking_url=settings.opsml_tracking_uri,
    )

    with open("audit.html", "w") as f:
        f.write(output_text)
