import ast
import glob
import os
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from black import FileMode, WriteBack, format_file_in_place
from opsml.helpers.utils import FindPath

from opsml.helpers.utils import Copier, YamlWriter
from opsml.pipelines.types import PipelineWriterMetadata, Task
from opsml.pipelines.writer_utils import FuncMetaCreator, FuncWriter
from opsml.pipelines.writer_utils.types import FuncMetadata

_MODULE_PATH = os.path.dirname(os.path.realpath(__file__))

AST_ARGS = [ast.ImportFrom, ast.Import, ast.Assign, ast.Pass, ast.AnnAssign]

INCLUDE_VARS = {
    "entry_point",
    "flavor",
    "number_instances",
    "machine_type",
    "gpu_count",
    "gpu_type",
    "custom_image",
    "retry",
}

text_wrapper = textwrap.TextWrapper(
    initial_indent="\t",
    break_long_words=False,
    break_on_hyphens=False,
)


class BlackFormatter:
    def __init__(self):
        self.mode = FileMode()
        self.write_back = WriteBack(True)


class PipelineDirCreator:
    def __init__(self, pipeline_dir: str, runner_filename: str):
        self.pipeline_dir = pipeline_dir
        self.runner_filename = runner_filename

    def create_base_files(self):
        """Creates init files and initial pipeline runner file"""

        for file_ in ["__init__.py", self.runner_filename]:
            with open(file=f"{self.pipeline_dir}/{file_}", mode="w", encoding="utf-8") as new_file:
                if file_ == self.runner_filename:
                    new_file.write("from opsml import PipelineRunner" + "\n")

    def create_starter_dir(self) -> str:
        # create dir
        Path(self.pipeline_dir).mkdir(exist_ok=True)
        pipeline_path = glob.glob(pathname=f"{self.pipeline_dir}", recursive=True)[0]
        self.create_base_files()

        return pipeline_path


class PipelineWriter:
    def __init__(
        self,
        pipeline_metadata: PipelineWriterMetadata,
        additional_dir: Optional[str] = None,
        template_name: str = "template.txt",
        runner_filename: str = "pipeline_runner.py",
    ):
        self.pipeline_metadata = pipeline_metadata
        self.template_name = template_name
        self.template_path = FindPath.find_filepath(name=self.template_name, path=_MODULE_PATH)
        self.runner_filename = runner_filename
        self.additional_dir = additional_dir
        self.pipeline_dir = f"ops_pipeline_{pipeline_metadata.project}_{pipeline_metadata.run_id}"
        self.pipeline_path = "placeholder"
        self.formatter = BlackFormatter()

    def write_pipeline(self, tmp_dir: Optional[str] = None) -> str:
        """Writes pipeline from files and task funcs"""

        pipeline_dir = tmp_dir or self.pipeline_dir

        # create initial dir
        pipeline_creator = PipelineDirCreator(pipeline_dir=pipeline_dir, runner_filename=self.runner_filename)
        self.pipeline_path = pipeline_creator.create_starter_dir()

        self.write_pipeline_tasks()

        if self.additional_dir is not None:
            Copier.copy_dir_to_path(
                dir_name=self.additional_dir,
                new_path=self.pipeline_path,
            )

        # write config yaml
        YamlWriter.dict_to_yaml(
            dict_=self.pipeline_metadata.config,
            filename="pipeline-config.yaml",
            path=self.pipeline_path,
        )

        # modify params
        return self.pipeline_path

    def write_pipeline_tasks(self):
        task_list = []
        for task in self.pipeline_metadata.pipeline_tasks:
            self.write_pipeline_task(task=task)
            task_list.append(task.name)

        self.finalize_runner(task_list=task_list)

    def write_pipeline_task(self, task: Task):
        func_metadata = FuncMetaCreator(function=task.func, name=task.name).parse()
        self._write_file(entry_point=task.entry_point, func_meta=func_metadata)

        self.append_args_to_runner(func_definition=func_metadata.definition, task_args=task_args)

    def _get_func_args(self, func: Any) -> Tuple[str, str, Dict[str, Any]]:
        name = func.__name__
        entry_point = self.pipeline_metadata.pipeline_resources[name].entry_point
        task_args = self.pipeline_metadata.pipeline_resources[name].dict(INCLUDE_VARS)

        return name, entry_point, task_args

    def _write_file(self, entry_point: str, func_meta: FuncMetadata) -> None:
        writer = next(
            (
                writer
                for writer in FuncWriter.__subclasses__()
                if writer.validate(
                    entry_point=entry_point,
                )
            )
        )
        writer(
            pipeline_path=self.pipeline_path,
            template_path=self.template_path,
            func_meta=func_meta,
        ).write_file(entry_point=entry_point)

        # format
        self.format_code(entry_point)

    def _write_text(self, file_, name, value, string_type=False):
        if string_type:
            txt = text_wrapper.fill(f"{name}='{value}'") + "\n"
        else:
            txt = text_wrapper.fill(f"{name}={value}") + "\n"
        file_.write(txt)

    def append_args_to_runner(self, func_definition: str, task_args: Dict[str, Any]):
        with open(f"{self.pipeline_path}/{self.runner_filename}", "a", encoding="utf-8") as file_:
            # write tasks
            file_.write(f"{func_definition}" + "\n")
            for key, val in task_args.items():
                if key == "machine_type":
                    if val["machine_type"] is not None:
                        self._write_text(file_=file_, name="machine_type", value=val["machine_type"])
                    else:
                        self._write_text(file_=file_, name="memory", value=val["memory"])
                        self._write_text(file_=file_, name="cpu", value=val["cpu"])
                else:
                    if isinstance(val, str):
                        self._write_text(file_=file_, name=key, value=f"{val}", string_type=True)
                    else:
                        self._write_text(file_=file_, name=key, value=val)
            file_.write("\n")

    def finalize_runner(self, task_list: List[str]):
        with open(f"{self.pipeline_path}/{self.runner_filename}", "a", encoding="utf-8") as file_:
            # add final imports
            file_.write(f"task_list = [{','.join(map(str, task_list))}]" + "\n")
            file_.write("\n")
            file_.write("if __name__=='__main__':")
            txt = text_wrapper.fill("runner = PipelineRunner(tasks=task_list).run()")
            file_.write(txt)

        self.format_code(self.runner_filename)

    def format_code(self, filename: str):
        src = Path(f"{self.pipeline_path}/{filename}")
        format_file_in_place(
            src=src,
            fast=True,
            mode=self.formatter.mode,
            write_back=self.formatter.write_back,
        )
