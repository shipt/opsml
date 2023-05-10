import os
import re
from enum import Enum
from datetime import datetime

from typing import Any, Dict, Optional, Union, List
import yaml
from pydantic import BaseModel, validator, Field, Extra

from opsml_artifacts.helpers.settings import settings
from opsml_artifacts.helpers.utils import ConfigFileLoader
from opsml_artifacts.pipelines.types import PipelineSystem
from opsml_artifacts.helpers.types import OpsmlEnvVars

env_pattern = re.compile(r".*?\${(.*?)}.*?")


class VertexExtraArgs(BaseModel):
    """
    Extra args to be used when creating Vertex custom training ops

    Args:
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
    reserved_ip_ranges: Optional[List[str]] = (
        Field([], description="Allocated IP range name to use when running vertex pipeline"),
    )
    gcp_region = Field("us-central1", description="gcp region to use when running pipelines")
    scheduler_uri: Optional[str] = Field(
        None, description="Scheduler URI to use when scheduling jobs", env=OpsmlEnvVars.SCHEDULER_URI
    )


class PipelineSpec(BaseModel):
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
    """

    project_name: str = Field(..., description="ML Project name")
    cron: Optional[str] = Field(None, description="CRON schedule")
    owner: str = Field(..., description="Code owner")
    team: str = Field(..., description="Team pipeline belongs to")
    user_email: str = Field(..., description="List of user emails to notify")
    pipeline_system: str = Field("local", description="Pipeline system to use")
    additional_dir: Optional[str] = Field(None, description="Optional directory to include with code")
    env_vars: Dict[str, Any] = Field({}, description="Env vars for pipeline")
    additional_task_args: Optional[VertexExtraArgs] = Field(None, description="Extra args to pass during job build")
    container_registry: str = Field(..., description="Container registry path", env=OpsmlEnvVars.CONTAINER_REGISTRY)
    cache: bool = Field(False, description="Boolean indicating whether pipeline tasks should be cached")

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True


def env_constructor(loader, node):
    """Constructor for finding env vars"""

    value = loader.construct_scalar(node)
    for group in env_pattern.findall(value):
        value = value.replace(f"${{{group}}}", os.environ.get(group))
    return value


yaml.add_implicit_resolver("!pathex", env_pattern)
yaml.add_constructor("!pathex", env_constructor)


class ParamDefaults(str, Enum):
    SOURCE_FILE = "pipeline_runner.py"
    COMPRESSED_FILENAME = "archive.tar.gz"
    SPEC_FILENAME = "pipeline-config.yaml"
    SOURCE_DIR = "src_dir"


class PipelineParams(BaseModel):
    """
    Creates pipeline params associated with the current pipeline run.
    """

    project_name: str
    owner: str
    user_email: str
    team: str
    pipeline_system: str
    container_registry: str
    env_vars: Dict[str, Any]
    pipe_filename: str
    pipe_filepath: str
    pipe_storage_root: str
    pipe_project_name: str
    pipe_job_id: str
    run_id: str
    cache: bool

    # defaults
    decorated: bool = False
    cron: Optional[str] = None
    is_proxy: bool = False
    directory: Optional[str] = None
    additional_dir: Optional[str] = None
    code_uri: Optional[str] = None
    source_dir: Optional[str] = None
    pipelinecard_uid: str = "NO_ID"
    source_file: str = ParamDefaults.SOURCE_FILE
    path: str = os.getcwd()
    additional_task_args: Dict[str, Any]

    @validator("is_proxy", pre=True)
    def set_default(cls, value):
        """Checks if a proxy is being used"""
        if settings.request_client is not None:
            return True
        return False

    @validator("additional_task_args", pre=True)
    def default_to_dictionary(cls, value):
        if value is None:
            return {}
        return value

    def add_attr(self, name: str, value: Union[int, float, str]):
        setattr(self, name, value)


class PipelineParamCreator:
    def __init__(
        self,
        spec: Optional[PipelineSpec] = None,
    ):

        """
        Class for setting up pipeline parameters

        Args:
            spec:
                Pipeline specification

        """
        self.pipe_spec = self.set_pipe_spec(spec=spec)

    @property
    def params(self) -> PipelineParams:
        pipeline_paths = self.create_pipeline_path_params()
        params = {**self.pipe_spec.dict(), **pipeline_paths}

        return PipelineParams(**params)

    def create_pipeline_path_params(self) -> Dict[str, str]:

        """Sets pipeline path parameters that are used when building pipeline systems"""

        suffix = "yaml" if self.pipe_spec.pipeline_system == PipelineSystem.KUBEFLOW else "json"

        run_id = str(datetime.now().strftime("%Y%m%d%H%M%S"))
        project_name = self.pipe_spec.project_name
        pipe_filename = f"{project_name}-{run_id}-pipeline.{suffix}"
        pipe_project_name = project_name.replace("_", "-")
        pipe_storage_path = f"{project_name}/pipeline"
        pipe_storage_root = f"{settings.storage_settings.storage_uri}/{pipe_storage_path}/{run_id}"

        paths = {
            "pipe_filename": pipe_filename,
            "pipe_filepath": pipe_filename.replace(" ", "_"),
            "pipe_storage_root": pipe_storage_root,
            "pipe_project_name": pipe_project_name,
            "pipe_job_id": f"{pipe_project_name}-{run_id}",
            "app_env": settings.app_env,
            "run_id": run_id,
        }

        return paths

    def set_pipe_spec(self, spec: Optional[PipelineSpec] = None) -> PipelineSpec:

        if spec is None:
            loaded_spec = self._get_pipeline_spec(filename=ParamDefaults.SPEC_FILENAME.value)
            spec = PipelineSpec(**loaded_spec)

        return spec

    def _get_pipeline_spec(
        self,
        filename: str,
        dir_name: Optional[str] = None,
    ) -> Dict[Union[str, int], Any]:

        """
        Extracts pipeline config

        Args:
            filename:
                Name of pipeline configuration file
        """

        loader = ConfigFileLoader(dir_name=dir_name, filename=filename)
        return loader.load()
