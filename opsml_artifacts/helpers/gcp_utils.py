import json
from typing import Any, Dict, Optional, Union, cast

from google.cloud import scheduler_v1, secretmanager, storage  # type: ignore
from google.cloud.scheduler_v1.types import Job
from google.oauth2.service_account import Credentials
from google.protobuf import duration_pb2
from pyshipt_logging import ShiptLogging

logger = ShiptLogging.get_logger(__name__)


class GCPService:
    def __init__(
        self,
        gcp_credentials: Optional[Credentials] = None,
    ):
        """Generic init"""

    @staticmethod
    def valid_service_name(service_name: str):
        """Validates service name"""


class GCPSecretManager(GCPService):
    def __init__(
        self,
        gcp_credentials: Optional[Credentials] = None,
    ):
        """Class for interacting with GCP secrets related to
        a project.

        Args:
            gcp_credentials (gcp Credentials): Credentials associated with
            a given gcp account that has permissions for accessing secrets.
            If not supplied, gcp will infer credentials for you local environment.
        """
        self.client = secretmanager.SecretManagerServiceClient(
            credentials=gcp_credentials,
        )

    def get_secret(
        self,
        project_name: str,
        secret: str,
        version: str = "latest",
    ):

        """Gets secret for GCP secrets manager.

        Args:
            project (str): GCP Project
            secret (str): Name of secret
            version (str) Version of secret to pull

        Returns
            secret value

        """

        response = self.client.access_secret_version(
            request={"name": f"projects/{project_name}/secrets/{secret}/versions/{version}"}  # noqa
        )

        payload = response.payload.data.decode("UTF-8")

        return payload

    @staticmethod
    def valid_service_name(service_name: str):
        return bool(service_name == "secret_manager")


class GCSStorageClient(GCPService):
    def __init__(
        self,
        gcp_credentials: Optional[Credentials] = None,
    ):

        """Instantiates GCP storage client

        Args:
            gcp_credentials (Credentials): Credentials with permissions for
            gcp storage client

        """
        self.client = storage.Client(
            credentials=gcp_credentials,
        )

    def list_objects(
        self,
        gcs_bucket: Union[str, None] = None,
        prefix: Union[str, None] = None,
    ):
        """List object is a given bucket with the specified prefix

        Args:
            gcs_bucket (str): Name of GCS bucket
            prefix (str): Blob prefix

        Returns:
            List of storage blobs

        """
        bucket = self.client.bucket(gcs_bucket)
        blobs = bucket.list_blobs(prefix=prefix)
        return blobs

    def download_object(
        self,
        gcs_bucket: str,
        blob_path: Union[str, None] = None,
        destination_filename: Union[str, None] = None,
    ):

        """Download an object from gcs

        Args:
            gcs_bucket (str): Name of GCS bucket
            blob_path (str): Path to object in gcs (including object name)
            destination_filename (str): Local filename to download to.

        """

        bucket = self.client.bucket(gcs_bucket)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(destination_filename)

        logger.info("Successully downloaded gs://%s/%s", gcs_bucket, blob_path)

    def download_object_from_uri(self, gcs_uri: str):
        bucket, blob, filename = self.parse_gcs_uri(gcs_uri=gcs_uri)

        self.download_object(
            gcs_bucket=bucket,
            blob_path=blob,
            destination_filename=filename,
        )

        return filename

    def delete_object(
        self,
        gcs_bucket: str,
        blob_path: Union[str, None] = None,
    ):
        """Delete object from gcs

        Args:
            gcs_bucket (str): Name of GCS bucket
            blob_path (str): Path to object in gcs (including object name)

        """

        bucket = self.client.bucket(gcs_bucket)
        blob = bucket.blob(blob_path)
        blob.delete()

        logger.info("Successully deleted gs://%s/%s", gcs_bucket, blob_path)

    def parse_gcs_uri(
        self,
        gcs_uri: str,
    ):
        """Parses gcs url

        Args:
            gcs_uri (str): Uri for gcs object

        Return:
            gcs_bucket and path
        """

        split_url = gcs_uri.split("/")
        bucket = split_url[2]
        blob_path = "/".join(split_url[3:])
        filename = split_url[-1]

        return bucket, blob_path, filename

    def delete_object_from_url(self, gcs_uri: str):

        """Delete object from gcs

        Args:
            gcs_uri (str): GCS uri of object

        """

        bucket, blob_path, _ = self.parse_gcs_uri(
            gcs_uri,
        )

        self.delete_object(
            bucket,
            blob_path,
        )

    def upload(
        self,
        gcs_bucket: str,
        filename: str,
        destination_path: str,
    ):
        """Upload local file to gcs

        Args:
            gcs_bucket (str): Name of gcs bucket
            filename (str): Local filename to upload
            destination_path (str): gcs path to write to

        Returns:
            Location of gcs object

        """

        bucket = self.client.bucket(gcs_bucket)
        blob = bucket.blob(destination_path)
        blob.upload_from_filename(filename)
        gcs_uri = f"gs://{gcs_bucket}/{destination_path}"

        logger.info("Uploaded %s to %s", filename, gcs_uri)

        return gcs_uri

    @staticmethod
    def valid_service_name(service_name: str):
        return bool(service_name == "storage")


class GCPMLScheduler(GCPService):
    def __init__(
        self,
        gcp_credentials: Optional[Credentials] = None,
    ):

        """Class for interacting with GCP cloud scheduler

        Args:
            gcp_region (str): GCP region to use
            gcp_project (str): GCP project to us
            schedule_uri_secret_name (str): Name of secret related to
            your cloud schedule uri. This will be pulled from secrets manager.
            gcp_credentials (Credentials): GCP Credentials. Inferred from
            environment if not supplied.
        """

        if bool(gcp_credentials):
            credentials = cast(Credentials, gcp_credentials)
        else:
            credentials = None

        # set instance vars
        self.schedule_client = scheduler_v1.CloudSchedulerClient(
            credentials=credentials,
        )
        self.oidc_token = scheduler_v1.OidcToken(
            service_account_email=credentials.service_account_email,
        )
        self.parent_path: Optional[str] = None

    def _set_job_name(self, gcp_project: str, gcp_region: str, job_name: str) -> str:
        parent_path: str = self.schedule_client.common_location_path(
            project=gcp_project,
            location=gcp_region,
        )
        self.parent_path = parent_path
        return f"{parent_path}/jobs/{job_name}"

    def job_already_exists(self, job_name):

        """Checks if schedule job exists

        Args:
            job_name (str): Name of schdule job

        Returns:
            Whether job exists or not (bool)

        """

        jobs = self.schedule_client.list_jobs(parent=self.parent_path)
        if any(job.name == job_name for job in jobs):
            logger.info("found existing job")
            return True
        return False

    def delete_job(self, job_name: str):
        """Deletes a given schedule job
        Args:
            job_name (str): Schedule job name
        """
        self.schedule_client.delete_job(name=job_name)
        logger.info("deleted existing job")

    def _get_retry_config(self) -> scheduler_v1.RetryConfig:
        retry_config = scheduler_v1.RetryConfig()
        retry_config.retry_count = 5
        retry_config.max_doublings = 5
        retry_config.min_backoff_duration = duration_pb2.Duration(seconds=5)  # pylint: disable=no-member
        retry_config.max_backoff_duration = duration_pb2.Duration(seconds=60)  # pylint: disable=no-member

        return retry_config

    def _create_job_class(self, job: Dict[str, Any]) -> Job:
        job = scheduler_v1.Job(job)
        job.retry_config = self._get_retry_config()

        return job

    def create_job(
        self,
        name: str,
        schedule: str,
        payload: Dict[str, str],
        scheduler_uri: str,
    ) -> Any:

        """Create cloud scheduler job

        Args:
            name (str): Name of job
            schedule (str): Schedule for job
            payload (str): Payload to pass to scheduler

        Returns:
            Created job
        """
        job: Dict[str, Any] = {
            "name": name,
            "http_target": {
                "http_method": "POST",
                "uri": scheduler_uri,
                "oidc_token": self.oidc_token,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode("utf-8"),
            },
            "schedule": schedule,
        }

        job_class = self._create_job_class(job=job)

        created_job = self.schedule_client.create_job(
            parent=self.parent_path,
            job=job_class,
        )

        return created_job

    def submit_schedule(
        self,
        payload: Dict[str, str],
        job_name: str,
        schedule: str,
        scheduler_uri: str,
        gcp_project: str,
        gcp_region: str,
    ):

        """Submits schedule to cloud scheduler

        Args:
            payload (dict): Payload to pass to cloud scheduler
            job_name (str): Name of schedule job
            schedule (str): Cron schedule

        """
        job_name = self._set_job_name(gcp_project=gcp_project, gcp_region=gcp_region, job_name=job_name)

        # check if job exists
        if self.job_already_exists(job_name=job_name):
            self.delete_job(job_name)

        created_job = self.create_job(
            name=job_name,
            schedule=schedule,
            payload=payload,
            scheduler_uri=scheduler_uri,
        )
        logger.info(created_job)

    @staticmethod
    def valid_service_name(service_name: str):
        return bool(service_name == "scheduler")


ClientTypes = Union[GCPSecretManager, GCSStorageClient]


class GCPClient:
    @staticmethod
    def get_service(
        service_name: str,
        gcp_credentials: Optional[Credentials] = None,
    ) -> ClientTypes:

        service = next(
            service
            for service in GCPService.__subclasses__()
            if service.valid_service_name(
                service_name=service_name,
            )
        )
        return cast(ClientTypes, service(gcp_credentials=gcp_credentials))
