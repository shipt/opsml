"""Code for building Tasks and Pipelines"""
import os
import shutil
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Union

from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.spec import PipelineBaseSpecHolder, SpecDefaults
from opsml.pipelines.systems.task_builder import get_task_builder
from opsml.pipelines.types import Task
from opsml.registry import CardRegistry, PipelineCard

logger = ArtifactLogger.get_logger(__name__)


class Pipeline:
    def __init__(self, specs: PipelineBaseSpecHolder, tasks: List[Task]):
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
        self._task_builder = get_task_builder(specs=specs, pipeline_system=self.specs.pipeline_system)

    @property
    def env_vars(self) -> Dict[str, Any]:
        return self.specs.env_vars

    @cached_property
    def pipelinecard_card(self) -> PipelineCard:
        pipeline_card = PipelineCard(
            name=self.specs.project_name,
            team=self.specs.team,
            user_email=self.specs.user_email,
            pipeline_code_uri=self.specs.code_uri,
        )
        registry = CardRegistry(registry_name="pipeline")
        registry.register_card(card=pipeline_card)
        self.specs.pipelinecard_uid = str(pipeline_card.uid)

        return pipeline_card

    def build(self) -> None:
        """
        Builds a pipeline.

        Args:
            pipeline_config:
                Pydantic pipeline configuration

        Returns:
            AI platform pipeline job. Will also incude airflow job in the future
        """
        raise NotImplementedError

    def run(self) -> None:
        """
        Runs a pipeline.

        Args:
            pipeline_job (PipelineJob): Pipeline job to run
        """
        raise NotImplementedError

    def schedule(self):
        """
        Schedules a pipelines.

        Args:
            pipeline_job:
                `PipelineJob`
        """
        raise NotImplementedError

    @staticmethod
    def validate(pipeline_system: str) -> bool:
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
