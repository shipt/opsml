"""Code for building Tasks and Pipelines"""
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, Dict, Any, Protocol
import tempfile
from opsml.registry.sql.settings import settings
from opsml.helpers.utils import FindPath
from opsml.helpers.logging import ArtifactLogger

from opsml.pipelines.systems.task_builder import get_task_builder
from opsml.pipelines.types import CodeInfo
from opsml.pipelines.spec import SpecDefaults, PipelineBaseSpecHolder
from opsml.pipelines.types import PipelineHelpers, PipelineJob, PipelineSystem, PathInfo, Task


logger = ArtifactLogger.get_logger(__name__)


class Pipeline:
    def __init__(
        self,
        specs: PipelineBaseSpecHolder,
        tasks: List[Task],
        helpers: PipelineHelpers,
    ):
        """
        Parent pipeline class that all pipeline systems inherit from. This class will
        set params, a pipeline packager, an httpx session if running as a client, a storage client,
        and a task builder that's used to build pipeline tasks.

        Args:
            specs:
                `PipelineBaseSpecs`
            tasks:
                List of pipeline `Task`s
            helpers:
                `PipelineHelpers`

        """
        self.specs = specs
        self.tasks = tasks
        self.helpers = helpers
        self._session = self._get_session()
        self._storage_client = settings.storage_client
        self._task_builder = get_task_builder(
            specs=specs,
            pipeline_system=self.specs.pipeline_system,
        )

    @property
    def env_vars(self) -> Dict[str, Any]:
        return self.specs.pipeline.env_vars

    def _package_and_upload(self, spec_dirpath: str):
        code_info = self.helpers.packager.package_and_upload_pipeline(
            spec_dirpath=spec_dirpath,
            spec_filename=self.specs.source_file,
        )

        setattr(self.specs, "code_uri", code_info.code_uri)
        setattr(self.specs, "source_dir", code_info.source_dir)

        return code_info

    def package_code(self) -> CodeInfo:
        """
        Packages and uploads pipeline code. If the pipeline is created using decorators,
        a temp directory is created and the pipeline is written to it prior to compression and upload.
        """

        if self.specs.decorated:
            with tempfile.TemporaryDirectory() as tmp_dir:
                self.specs.path = self.helpers.writer.write_pipeline(tmp_dir=tmp_dir)
                runner_path_info = self._get_pipeline_runner_path_info()

                return self._package_and_upload(
                    filepath=runner_path_info.filepath,
                    dir_name=runner_path_info.dir_name,
                )

        spec_dir_path = self._get_pipeline_spec_path_info()
        return self._package_and_upload(spec_dirpath=spec_dir_path)

    def _get_pipeline_spec_path_info(self) -> str:
        """
        Searches for the pipeline specification file along a given path.
        If a unique directory is given, that directory is searched. This is helpful
        in cases where multiple pipelines are in one repository. If no directory is specified,
        it is assumed there is only one `pipeline_runner.py` present, and the path associated
        with this pipeline will be used.
        """

        # if directory has been specified
        if self.specs.directory is not None:
            dir_path = FindPath.find_dirpath(
                dir_name=self.specs.directory,
                anchor_file=self.specs.source_file,
            )

            return FindPath.find_source_dir(
                path=dir_path,
                runner_file=self.specs.source_file,
            )

        return FindPath.find_source_dir(
            path=self.specs.path,
            spec_file=self.specs.source_file,
        )

    def _get_session(self):
        """Gets the requests session for connecting to the opsml api"""
        return settings.request_client

    def build(self) -> PipelineJob:
        """
        Builds a pipeline.

        Args:
            pipeline_config:
                Pydantic pipeline configuration

        Returns:
            AI platform pipeline job. Will also incude airflow job in the future
        """
        raise NotImplementedError

    @staticmethod
    def run(specs: PipelineBaseSpecHolder) -> None:
        """
        Runs a pipeline.

        Args:
            pipeline_job (PipelineJob): Pipeline job to run
        """
        raise NotImplementedError

    @staticmethod
    def write_pipeline_file(pipeline_definition: Dict[Any, Any], filename: str) -> str:
        """
        Writes a pipeline definition to a file

        Args:
            pipeline_definition:
                dictionary containing compiled pipeline
            filename:
                name or file to write


        """
        raise NotImplementedError

    def schedule():
        """
        Schedules a pipelines.

        Args:
            pipeline_job:
                `PipelineJob`
        """
        raise NotImplementedError

    @staticmethod
    def validate(pipeline_system: PipelineSystem, is_proxy: bool) -> bool:
        raise NotImplementedError

    def delete_files(self) -> None:
        paths: List[Union[str, Path]] = list(Path(os.getcwd()).rglob(f"{self.specs.project_name}-*.json"))
        paths.append(SpecDefaults.COMPRESSED_FILENAME)

        # remove deco dir
        ops_pipeline_name = self.specs.pipeline_metadata.job_id

        shutil.rmtree(ops_pipeline_name, ignore_errors=True)

        # remove local dir if running local pipeline
        shutil.rmtree(self.specs.pipeline_metadata.job_id, ignore_errors=True)

        for path in paths:
            try:
                os.remove(path)
            except Exception as error:  # pylint: disable=broad-except,unused-variable # noqa
                pass

    def _package_code(self) -> CodeInfo:
        if self.tasks.decorated:
            code_info = self._create_temp_package()

        self._add_code_info_to_params(code_info=code_info)

        return code_info
