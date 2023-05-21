import ast
import glob
import os
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from black import FileMode, WriteBack, format_file_in_place
from opsml.helpers.utils import FindPath, clean_string


from opsml.pipelines.utils import YamlWriter, Copier
from opsml.pipelines.types import Task
from opsml.pipelines.writer_utils import FuncMetaCreator, PyWriter
from opsml.pipelines.writer_utils.types import FuncMetadata
from opsml.pipelines.spec import SpecDefaults, PipelineWriterMetadata
from opsml.pipelines.utils import RequirementsCopier

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
    "memory",
    "cpu",
}

BASE_SPEC_ARGS = {
    "project_name",
    "owner",
    "user_email",
    "team",
    "cache",
    "cron",
    "additional_dir",
    "pipelinecard_uid",
    "pipeline_system",
}

PIPELINE_TEMPLATE_FILE = "template.txt"

text_wrapper = textwrap.TextWrapper(
    initial_indent="\t",
    break_long_words=False,
    break_on_hyphens=False,
)


class BlackFormatter:
    def __init__(self):
        self.mode = FileMode()
        self.write_back = WriteBack(True)


@dataclass
class PipelinePaths:
    base_dir_path: str
    pipeline_path: str


class PipelineDirCreator:
    def __init__(self, pipeline_dir: str):
        self.pipeline_base_dir = pipeline_dir
        self.pipeline_dir = f"{self.pipeline_base_dir}/pipeline"

    def create_base_files(self):
        """Creates init files and initial pipeline runner file"""

        with open(
            file=f"{self.pipeline_dir}/__init__.py",
            mode="w",
            encoding="utf-8",
        ) as new_file:
            pass

    def create_starter_dir(self) -> PipelinePaths:
        # create dir
        Path(self.pipeline_dir).mkdir(parents=True, exist_ok=True)
        base_pipeline_path = glob.glob(pathname=self.pipeline_base_dir, recursive=True)[0]
        pipeline_dir_path = glob.glob(pathname=self.pipeline_dir, recursive=True)[0]
        self.create_base_files()

        return PipelinePaths(
            base_dir_path=base_pipeline_path,
            pipeline_path=pipeline_dir_path,
        )


class PipelineWriter:
    def __init__(self, pipeline_metadata: PipelineWriterMetadata):
        self.writer_metadata = pipeline_metadata
        self.template_path = FindPath.find_filepath(name=PIPELINE_TEMPLATE_FILE, path=_MODULE_PATH)
        self.pipeline_dir = clean_string(f"{pipeline_metadata.project}-{pipeline_metadata.run_id}")
        self.formatter = BlackFormatter()
        self._pipeline_paths: Optional[PipelinePaths] = None

    @property
    def pipeline_paths(self) -> PipelinePaths:
        if self._pipeline_paths is not None:
            return self._pipeline_paths
        raise ValueError("No pipeline paths exists")

    @pipeline_paths.setter
    def pipeline_paths(self, path: PipelinePaths) -> None:
        self._pipeline_paths = path

    def _create_pipeline_dir(self, pipeline_dir: str):
        """
        Creates pipeline base folder and init file

        Args:
            pipeline_dir:
                Name of pipeline directory

        """

        # create initial dir
        pipeline_creator = PipelineDirCreator(pipeline_dir=pipeline_dir)
        self.pipeline_paths = pipeline_creator.create_starter_dir()

    def _add_additional_dir(self) -> None:
        """
        Copies specified directory to pipeline path

        Args:
            pipeline_path:
                Path to pipeline directory
        """
        additional_dir = self.writer_metadata.specs.additional_dir
        if additional_dir is not None:
            Copier.copy_dir_to_path(
                dir_name=additional_dir,
                new_path=self.pipeline_paths.base_dir_path,
            )

    def _get_task_args(self, task: Task) -> Dict[str, Any]:
        """
        Gets non-None args from task

        Args:
            task:
                `Task`
        Returns:
            Dictionary of task args
        """
        task_args = task.dict(include=INCLUDE_VARS)
        return {key: value for key, value in task_args.items() if value is not None}

    def _get_pipeline_env_vars(self) -> Dict[str, Union[str, int, float]]:
        env_vars = self.writer_metadata.specs.env_vars
        if bool(env_vars):
            return env_vars

    def _get_additional_spec_args(self) -> Dict[str, Union[str, int, float]]:
        base_args = self.writer_metadata.specs.dict(include=BASE_SPEC_ARGS)

        # get path metadata
        base_args["pipeline_metadata"] = self.writer_metadata.specs.pipeline_metadata.dict()

        return base_args

    def _write_pipeline_specification(self):
        specs = {}

        # gather specification args
        pipeline_tasks = {task.name: self._get_task_args(task) for task in self.writer_metadata.pipeline_tasks}
        specs["pipeline"] = {"tasks": pipeline_tasks}
        specs["pipeline"]["env_vars"] = self._get_pipeline_env_vars()
        specs["pipeline"]["args"] = self._get_additional_spec_args()

        # write config yaml
        YamlWriter.dict_to_yaml(
            dict_=specs,
            filename=SpecDefaults.SPEC_FILENAME,
            path=self.pipeline_paths.base_dir_path,
        )

    def _add_requirements(self) -> None:
        """Adds requirement file to pipeline directory"""

        if self.writer_metadata.specs.requirements is not None:
            self.req_path = RequirementsCopier(
                requirements_file=self.writer_metadata.specs.requirements,
                spec_filepath=self.pipeline_paths.base_dir_path,
            ).copy_req_to_src()

    def write_pipeline(self, tmp_dir: Optional[str] = None) -> str:
        """Writes pipeline from files and task funcs"""

        self._create_pipeline_dir(pipeline_dir=tmp_dir or self.pipeline_dir)
        self._write_pipeline_tasks()
        self._add_additional_dir()
        self._add_requirements()
        self._write_pipeline_specification()

        # modify params
        return self.pipeline_paths.base_dir_path

    def _write_pipeline_tasks(self):
        task_list = []
        for task in self.writer_metadata.pipeline_tasks:
            self._write_pipeline_task(task=task)
            task_list.append(task.name)

    def _write_pipeline_task(self, task: Task):
        func_metadata = FuncMetaCreator(
            function=task.func,
            name=task.name,
        ).parse()

        self._write_file(
            entry_point=task.entry_point,
            func_meta=func_metadata,
        )

    def _write_file(self, entry_point: str, func_meta: FuncMetadata) -> None:
        PyWriter(
            pipeline_path=self.pipeline_paths.pipeline_path,
            template_path=self.template_path,
            func_meta=func_meta,
        ).write_file(entry_point=entry_point)

        # format
        self.format_code(entry_point)

    def format_code(self, filename: str):
        src = Path(f"{self.pipeline_paths.pipeline_path}/{filename}")
        format_file_in_place(
            src=src,
            fast=True,
            mode=self.formatter.mode,
            write_back=self.formatter.write_back,
        )
