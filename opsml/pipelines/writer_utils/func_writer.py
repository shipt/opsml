import textwrap
from pathlib import Path
from typing import Dict, List, Union

from opsml.pipelines.utils import TemplateWriter
from opsml.pipelines.writer_utils.types import FuncMetadata


class FuncWriter:
    def __init__(
        self,
        pipeline_path: str,
        template_path: Union[str, Path],
        func_meta: FuncMetadata,
    ):
        self.pipeline_path = pipeline_path
        self.template_path = template_path
        self.func_meta = func_meta

    def write_file(self, entry_point: str) -> None:
        raise NotImplementedError


class PyWriter(FuncWriter):
    def _get_card_saver_text(self, assigned_cards: List[str]) -> str:
        text = ""
        for card in assigned_cards:
            text = text + f"registry = CardRegistries.getattr({card}.card_type) \n"
            text = text + f"registry.register_card(card={card}, assign_to_pipeline=True) \n"

        return textwrap.indent(text, prefix="\t")

    def _creat_template(self) -> Dict[str, str]:
        return {
            "code": textwrap.indent(self.func_meta.text, prefix="\t"),
            "assigned_cards": self.func_meta.assigned_cards,
            "end_code": self._get_card_saver_text(assigned_cards=self.func_meta.assigned_cards),
        }

    def write_file(self, entry_point: str) -> None:
        # get template mapping
        template_mapping = self._creat_template()

        # write template for py tasks
        TemplateWriter(
            template_mapping=template_mapping,
            template_path=self.template_path,
            file_path=self.pipeline_path,
            filename=entry_point,
        ).write_file()
