# pylint: disable=no-self-argument
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Extra, Field, root_validator, validator

from opsml.helpers.types import OpsmlPipelineVars
from opsml.helpers.utils import clean_string
from opsml.pipelines.types import PipelineSystem, Task
from opsml.pipelines.utils import SpecLoader
from opsml.registry.sql.settings import settings

env_pattern = re.compile(r".*?\${(.*?)}.*?")


# Spec types
class SpecDefaults(str, Enum):
    COMPRESSED_FILENAME = "archive.tar.gz"
    SPEC_FILENAME = "pipeline-spec.yaml"
    SOURCE_DIR = "src_dir"


class PipelineTasks(BaseModel):
    tasks: Optional[Dict[str, Dict[str, Any]]] = None


class PipelineArgs(BaseModel):
    service_account: Optional[str] = None
    network: Optional[str] = None
    reserved_ip_ranges: Optional[str] = None
    gcp_region: Optional[str] = None
    gcp_project: Optional[str] = None
    container_registry: Optional[str] = None
    pipeline_system: Optional[str] = None


class PipelineMetadata(BaseModel):
    filename: str
    storage_root: str
    job_id: str
    app_env: str
    run_id: str


# Classes for decorators specs
class PipelineSpec(BaseModel):
    project_name: str = Field(..., description="ML Project name")
    cron: Optional[str] = Field(None, description="CRON schedule")
    owner: str = Field(..., description="Code owner")
    team: str = Field(..., description="Team pipeline belongs to")
    user_email: str = Field(..., description="List of user emails to notify")
    additional_dir: Optional[str] = Field(None, description="Optional directory to include with code")
    env_vars: Dict[str, Any] = Field({}, description="Env vars for pipeline")
    container_registry: str = Field(
        ...,
        description="Container registry path",
        env=OpsmlPipelineVars.CONTAINER_REGISTRY,
    )
    cache: bool = Field(False, description="Boolean indicating whether pipeline tasks should be cached")

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True

    @property
    def pipeline_system(self):
        raise NotImplementedError


class VertexPipelineSpecs(PipelineSpec):

    """
    Config used as part decorator-based training of pipelines

    Args:
        project_name:
            ML Project name
        cron:
            CRON schedule
        owner:
            Code owner
        user_email:
            User email to associate with pipeline
        team:
            Team pipeline belongs to
        pipeline_system:
            Pipeline system to use (Local, Vertex, or KubeFlow)
        additional_dir:
            Additional directory to include when packaging code. This directory
            will be available to import from for all tasks
        env_vars:
            Additional env vars to include with all tasks
        additional_task_args:
            Additional args to pass when building custom job. Currently accepts instance
            of `VertexExtraArgs`.
        service_account:
            Optional GCP service account to use when running custom job
        cron:
            CRON schedule
        owner:
            Code owner
        user_email:
            User email to associate with pipeline
        team:
            Team pipeline belongs to
    """

    service_account: Optional[str] = Field(None, description="Service account to use when custom task")
    network: Optional[str] = Field(None, description="VPC network to use when running vertex pipeline")
    reserved_ip_ranges: Optional[List[str]] = Field(None, description="IP range to use")
    gcp_region = Field("us-central1", description="gcp region to use when running pipelines")
    gcp_project: Optional[str] = Field(None, description="gcp project associated with vertex pipeline")

    @property
    def pipeline_system(self):
        return PipelineSystem.VERTEX


class PipelineBaseSpecHolder(BaseModel):
    """
    Creates pipeline params associated with the current pipeline run.
    """

    project_name: str
    owner: str
    user_email: str
    team: str
    pipeline_metadata: PipelineMetadata
    container_registry: str
    env_vars: Dict[str, Any]
    cache: Optional[bool] = False

    # defaults
    decorated: bool = False
    cron: Optional[str] = None
    is_proxy: bool = False
    directory: Optional[str] = None
    additional_dir: Optional[str] = None
    code_uri: Optional[str] = None
    source_dir: Optional[str] = None
    pipelinecard_uid: str = "NO_ID"
    pipeline_system: str = PipelineSystem.LOCAL
    source_file: str = SpecDefaults.SPEC_FILENAME
    path: str = os.getcwd()
    requirements: Optional[str] = None

    # pipeline spec
    pipeline: Optional[PipelineTasks] = None

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True

    @validator("project_name", pre=True)
    def clean_name(cls, value):
        return clean_string(value)

    @validator("is_proxy", pre=True)
    def set_default(cls, value):
        """Checks if a proxy is being used"""
        if settings.request_client is not None:
            return True
        return False

    @root_validator(pre=True)
    def set_pipeline_vars(cls, values):
        # set env vars with tasks
        if bool(values.get("env_vars")):
            env_vars = values.get("env_vars")
        else:
            env_vars = {}

        env_vars["project_name"] = values["project_name"]
        env_vars["team"] = values["team"]
        env_vars["owner"] = values["owner"]

        values["env_vars"] = env_vars

        return values

    @staticmethod
    def validate(pipeline_system: str):
        return pipeline_system == PipelineSystem.LOCAL


class VertexSpecHolder(PipelineBaseSpecHolder):
    """
    Pipeline Specs for Vertex
    """

    service_account: Optional[str] = None
    network: Optional[str] = None
    reserved_ip_ranges: Optional[List[str]] = None
    gcp_region: Optional[str] = None
    gcp_project: Optional[str] = None

    @staticmethod
    def validate(pipeline_system: str):
        return pipeline_system == PipelineSystem.VERTEX


class PipelineSpecCreator:
    def __init__(
        self,
        spec_filename: Optional[str] = SpecDefaults.SPEC_FILENAME.value,
        spec: Optional[PipelineSpec] = None,
    ):
        """
        Class for setting up pipeline parameters

        Args:
            spec:
                Pipeline specification

        """

        self.spec_filename = spec_filename or SpecDefaults.SPEC_FILENAME.value
        self.pipe_spec = self.set_pipe_spec(spec=spec)

    @property
    def specs(self) -> PipelineBaseSpecHolder:
        pipeline_metadata = self.create_pipeline_metadata()
        specs = {
            **self.pipe_spec,
            **{"pipeline_metadata": pipeline_metadata},
            **{"source_file": self.spec_filename},
        }

        return PipelineSpecCreator.get_pipeline_spec(specs=specs)

    @staticmethod
    def get_pipeline_spec(specs: Dict[str, Any]) -> PipelineBaseSpecHolder:
        pipeline_system = str(specs.get("pipeline_system"))
        pipeline_spec = next(
            (
                pipeline_spec
                for pipeline_spec in PipelineBaseSpecHolder.__subclasses__()
                if pipeline_spec.validate(pipeline_system=pipeline_system)
            ),
            PipelineBaseSpecHolder,
        )
        return pipeline_spec(**specs)

    def create_pipeline_metadata(self) -> PipelineMetadata:
        """Sets pipeline path parameters that are used when building pipeline systems"""

        # suffix = "yaml" if self.pipe_spec.get("pipeline_system") != PipelineSystem.KUBEFLOW else "json"
        file_ext = "json"
        run_id = str(datetime.now().strftime("%Y%m%d%H%M%S"))
        project_name = self.pipe_spec.get("project_name")
        pipe_filename = f"{project_name}-{run_id}-pipeline.{file_ext}"
        pipe_storage_path = f"{project_name}/pipeline"
        pipe_storage_root = f"{settings.storage_settings.storage_uri}/{pipe_storage_path}/{run_id}"

        metadata = PipelineMetadata(
            filename=pipe_filename,
            storage_root=pipe_storage_root,
            job_id=f"{project_name}-{run_id}",
            app_env=settings.app_env,
            run_id=run_id,
        )

        return metadata

    def set_pipeline_tasks(self, loaded_spec: Dict[str, Any]):
        tasks = loaded_spec.get("pipeline")
        if tasks is not None:
            loaded_spec["pipeline"] = PipelineTasks(tasks=tasks)

        return loaded_spec

    def set_pipe_spec(self, spec: Optional[PipelineSpec] = None) -> Dict[str, Any]:
        if spec is None:
            return self._get_pipeline_yaml_spec(filename=self.spec_filename)
        return spec.dict()

    def _get_pipeline_yaml_spec(
        self,
        filename: str,
        dir_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Loads pipeline spec from file

        Args:
            filename:
                Name of pipeline specification file
        """

        loader = SpecLoader(dir_name=dir_name, filename=filename)
        spec = loader.load()

        # yaml specs define pipeline args under pipeline
        # Spec class expect all args to be key, value pairs
        pipeline = spec.get("pipeline")
        if pipeline is not None:
            args = pipeline.get("args")
            if args is not None:
                for key, value in args.items():
                    spec[key] = value
                pipeline.pop("args")

            env_vars = pipeline.get("env_vars")
            if env_vars is not None:
                spec["env_vars"] = env_vars

                pipeline.pop("env_vars")

        return spec


@dataclass
class PipelineWriterMetadata:
    run_id: str
    project: str
    pipeline_tasks: List[Task]
    specs: PipelineBaseSpecHolder
