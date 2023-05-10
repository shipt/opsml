import textwrap
from pathlib import Path
from typing import Dict, Union

from opsml_artifacts.helpers.utils import Copier, TemplateWriter
from opsml_artifacts.pipelines.writer_utils.types import FuncMetadata


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
    def _get_var_saver_text(self, assigned_var_text: str) -> str:
        txt = f"""if os.getenv('PIPELINEcard_uid'): tracker.save_cards(assigned_cards={assigned_var_text}"""
        return textwrap.indent(
            txt + ", global_vars=globals())",
            prefix="\t",
        )

    def _creat_template(self) -> Dict[str, str]:
        return {
            "load_code": self.func_meta.input_vars,
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
