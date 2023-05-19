from typing import Dict, List, Any, cast
import json
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.spec import VertexPipelineSpecs
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
    @staticmethod
    def run(specs: VertexPipelineSpecs) -> None:
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
            project=settings.storage_settings.gcp_project,
            staging_bucket=settings.storage_settings.storage_uri,
            credentials=settings.storage_settings.credentials,
            location=specs.gcp_region,
        )

        pipeline_job = aip.PipelineJob(
            display_name=specs.project_name,
            template_path=specs.pipeline_metadata.filename,
            job_id=specs.pipeline_metadata.job_id,
            pipeline_root=specs.pipeline_metadata.storage_root,
            enable_caching=specs.cache,
        )

        pipeline_job.submit(
            service_account=specs.service_account,
            network=specs.network,
        )

        stdout_msg("Pipeline Submitted!")

    def upload_pipeline_to_gcs(compiled_pipeline_path: str, destination_path: str) -> str:
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

    def _submit_schedule_from_payload(self, payload: Dict[str, str]):
        from opsml.helpers.gcp_utils import GCPClient

        self.specs = cast(VertexSpecHolder, self.specs)

        if self.specs.cron is not None:
            job_name = f"{payload.get('display_name')}-ml-model"

            schedule_client = GCPClient.get_service(
                "scheduler",
                gcp_credentials=settings.storage_settings.credentials,
            )

            schedule_client.submit_schedule(
                payload=payload,
                job_name=job_name,
                schedule=self.specs.cron,
                scheduler_uri=settings.scheduler_uri,
                gcp_project=str(self.specs.gcp_project),
                gcp_region=str(self.specs.gcp_region),
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

        destination_path = f"{self.specs.pipeline_metadata.storage_root}/{self.specs.pipeline_metadata.filepath}"
        pipeline_uri = self.upload_pipeline_to_gcs(
            compiled_pipeline_path=self.specs.pipeline_metadata.filepath,
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
    def write_pipeline_to_temp_file(pipeline_definition: Dict[Any, Any], filename: str) -> None:
        """
        Writes a pipeline definition to a file

        Args:
            pipeline_definition:
                dictionary containing compiled pipeline
            filename:
                name or file to write

        Returns:
            Path to temp json file
        """

        json_object = json.dumps(pipeline_definition, indent=4)
        with open(filename, "w", encoding="utf8") as temp_file:
            temp_file.write(json_object)

        return filename

    @staticmethod
    def validate(pipeline_system: PipelineSystem, is_proxy: bool) -> bool:
        return pipeline_system == PipelineSystem.VERTEX and is_proxy == False
