from typing import Dict, List, Any, cast

from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.systems.kubeflow import KubeFlowServerPipeline
from opsml.pipelines.utils import stdout_msg
from opsml.registry.sql.settings import settings
from opsml.pipelines.spec import VertexSpecHolder
from opsml.pipelines.types import (
    PipelineJob,
    PipelineSystem,
    PipelineParams,
)

logger = ArtifactLogger.get_logger(__name__)


class VertexServerPipeline(KubeFlowServerPipeline):
    def run(self) -> None:
        """
        Runs a Vertex pipeline

        Args:
            pipeline_job:
                Vertex pipeline job
            pipeline_params:
                Pydantic model of pipeline params
            schedule:
                Whether to schedule pipeline or not

        """
        import google.cloud.aiplatform as aip

        self.specs = cast(VertexSpecHolder, self.specs)
        aip.init(
            project=settings.storage_settings.gcp_project,
            staging_bucket=settings.storage_settings.gcs_bucket,
            credentials=settings.storage_settings.credentials,
            location=self.specs.gcp_region,
        )

        filepath = f"{self.specs.pipeline_metadata.storage_root}/{self.specs.pipeline_metadata.filename}"
        pipeline_job = aip.PipelineJob(
            display_name=self.specs.project_name,
            template_path=filepath,
            job_id=self.specs.pipeline_metadata.job_id,
            pipeline_root=self.specs.pipeline_metadata.storage_root,
            enable_caching=self.specs.cache,
        )

        pipeline_job.job.submit(
            service_account=self.specs.service_account,
            network=self.specs.network,
        )

        stdout_msg("Pipeline Submitted!")

    @staticmethod
    def upload_pipeline_to_gcs(compiled_pipeline_path: str, destination_path: str):
        """
        Uploads vertex pipeline to cloud storage (gcs)

        Args:
            compiled_pipeline_path:
                Local path to compiled pipeline file
            destination_path:
                Destination path to write to

        Returns:
            Pipeline storage uri

        """

        pipeline_uri = settings.storage_client.upload(
            local_path=compiled_pipeline_path,
            write_path=destination_path,
        )

        return pipeline_uri

    @staticmethod
    def _submit_schedule_from_payload(params: PipelineParams, payload: Dict[str, str]):
        from opsml.helpers.gcp_utils import GCPClient

        if not bool(params.cron):
            raise ValueError(
                """No CRON found in PipelineSpec of pipeline_config.yaml file.
                Please ensure the CRON is specified""",
            )

        job_name = f"{payload.get('display_name')}-ml-model"

        schedule_client = GCPClient.get_service(
            "scheduler",
            gcp_credentials=settings.storage_settings.credentials,
        )

        schedule_client.submit_schedule(
            payload=payload,
            job_name=job_name,
            schedule=str(params.cron),
            scheduler_uri=str(params.additional_task_args.get("scheduler_uri")),
            gcp_project=settings.storage_settings.gcp_project,
            gcp_region=params.additional_task_args.get("gcp_region"),
        )

    @staticmethod
    def schedule(pipeline_job: PipelineJob) -> None:
        """
        Schedules a Vertex pipeline using Cloud Scheduler

        Args:
            pipeline_params:
                Pydantic model of pipeline params

        """
        # params are passed during pipeline building
        params: PipelineParams = pipeline_job.job

        destination_path = f"{params.pipe_storage_root}/{params.pipe_filepath}"
        pipeline_uri = VertexServerPipeline.upload_pipeline_to_gcs(
            compiled_pipeline_path=params.pipe_filepath,
            destination_path=destination_path,
        )

        payload = {
            "name": params.project_name,
            "team": params.team,
            "user_email": params.user_email,
            "pipeline_code_uri": params.code_uri,
            "pipeline_spec_uri": pipeline_uri,
            "pipeline_root": params.pipeline_root,
            "display_name": params.pipe_project_name,
            "job_id": params.pipe_job_id,
        }

        VertexServerPipeline._submit_schedule_from_payload(
            params=params,
            payload=payload,
        )

    @staticmethod
    def validate(pipeline_system: PipelineSystem, is_proxy: bool) -> bool:
        return pipeline_system == PipelineSystem.VERTEX and is_proxy == False
