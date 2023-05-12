import textwrap
from pathlib import Path
from typing import Dict, Union, List

from opsml.pipelines.utils import Copier, TemplateWriter
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

    @staticmethod
    def validate(entry_point: str) -> bool:
        raise NotImplementedError


class SqlWriter(FuncWriter):
    def write_file(self, entry_point: str) -> None:
        Copier.copy_file_to_dir(
            dir_path=self.pipeline_path,
            dir_name="sql",
            filename=entry_point,
        )

    @staticmethod
    def validate(entry_point: str) -> bool:
        return "sql" in entry_point


class PyWriter(FuncWriter):
    def _get_var_saver_text(self, assigned_cards: List[str]) -> str:
        text = ""
        for card in assigned_cards:
            text + f"registry = CardRegistry(registry_type={card.card_type}) \n"
            text + f"registry.register_card(card={card}, assign_to_pipeline=True) \n"

        return textwrap.indent(text, prefix="\t")

    def _creat_template(self) -> Dict[str, str]:
        return {
            "code": textwrap.indent(self.func_meta.text, prefix="\t"),
            "assigned_vars": self.func_meta.assigned_vars,
            "end_code": self._get_var_saver_text(assigned_var_text=self.func_meta.assigned_vars),
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

    @staticmethod
    def validate(entry_point: str) -> bool:
        return "sql" not in entry_point
