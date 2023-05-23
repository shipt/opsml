# pylint: disable=import-outside-toplevel
from typing import Any, Dict, cast

from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.spec import VertexSpecHolder
from opsml.pipelines.systems.kubeflow import KubeFlowPipeline
from opsml.pipelines.types import PipelineSystem
from opsml.pipelines.utils import stdout_msg
from opsml.registry.sql.settings import settings
from opsml.registry.storage.types import GcsStorageClientSettings

logger = ArtifactLogger.get_logger(__name__)


class VertexPipeline(KubeFlowPipeline):
    @property
    def vertex_specs(self) -> VertexSpecHolder:
        return cast(VertexSpecHolder, self.specs)

    @property
    def storage_settings(self) -> GcsStorageClientSettings:
        return cast(GcsStorageClientSettings, settings.storage_settings)

    @property
    def gcp_project(self) -> str:
        gcp_project = self.vertex_specs.gcp_project or self.storage_settings.gcp_project
        if gcp_project is not None:
            return gcp_project
        raise ValueError("No GCP project")

    @property
    def gcp_region(self) -> str:
        region = self.vertex_specs.gcp_region or self.storage_settings.gcp_region
        if region is not None:
            return region
        raise ValueError("No GCP region")

    @property
    def credentials(self) -> Any:
        return self.storage_settings.credentials

    @property
    def storage_uri(self) -> str:
        return self.storage_settings.storage_uri

    @property
    def scheduler_uri(self) -> str:
        if settings.scheduler_uri is not None:
            return settings.scheduler_uri
        raise ValueError("No Scheduler URI provided")

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

        aip.init(
            project=self.gcp_project,
            staging_bucket=self.storage_uri,
            credentials=self.credentials,
            location=self.gcp_region,
        )

        pipeline_job = aip.PipelineJob(
            display_name=self.gcp_project,
            template_path=self.specs.pipeline_metadata.filename,
            job_id=self.specs.pipeline_metadata.job_id,
            pipeline_root=self.specs.pipeline_metadata.storage_root,
            enable_caching=self.specs.cache,
        )

        pipeline_job.submit(
            service_account=self.vertex_specs.service_account,
            network=self.vertex_specs.network,
        )

        stdout_msg("Pipeline Submitted!")

    def upload_pipeline_to_gcs(self, compiled_pipeline_path: str, destination_path: str) -> str:
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

    def _submit_schedule_from_payload(self, payload: Dict[str, Any]):
        from opsml.helpers.gcp_utils import GCPClient, GCPMLScheduler

        if self.specs.cron is not None:
            job_name = f"{payload.get('display_name')}-ml-model"

            schedule_client: GCPMLScheduler = GCPClient.get_service("scheduler", gcp_credentials=self.credentials)

            schedule_client.submit_schedule(
                payload=payload,
                job_name=job_name,
                schedule=self.specs.cron,
                scheduler_uri=self.scheduler_uri,
                gcp_project=self.gcp_project,
                gcp_region=self.gcp_region,
            )

        else:
            raise ValueError(
                """No CRON found in PipelineSpec of pipeline_config.yaml file.
                Please ensure the CRON is specified""",
            )

    def schedule(self) -> None:
        """
        Schedules a Vertex pipeline using Cloud Scheduler

        Args:
            pipeline_params:
                Pydantic model of pipeline params

        """

        destination_path = f"{self.specs.pipeline_metadata.storage_root}/{self.specs.pipeline_metadata.filename}"
        pipeline_uri = self.upload_pipeline_to_gcs(
            compiled_pipeline_path=self.specs.pipeline_metadata.filename,
            destination_path=destination_path,
        )

        payload = {
            "name": self.specs.project_name,
            "team": self.specs.team,
            "user_email": self.specs.user_email,
            "pipeline_code_uri": self.specs.code_uri,
            "pipeline_spec_uri": pipeline_uri,
            "pipeline_root": self.specs.pipeline_metadata.storage_root,
            "display_name": self.specs.project_name,
            "job_id": self.specs.pipeline_metadata.job_id,
        }

        self._submit_schedule_from_payload(payload=payload)

    @staticmethod
    def validate(pipeline_system: str) -> bool:
        return pipeline_system == PipelineSystem.VERTEX
