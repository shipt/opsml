import os
import shutil
import tarfile
from pathlib import Path
from typing import Dict, Optional, Any, cast
import tempfile
from opsml.pipelines import settings
from opsml.helpers.request_helpers import ApiClient, ApiRoutes
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.utils import YamlWriter
from opsml.helpers.utils import FindPath
from opsml.helpers import exceptions

# from opsml.pipelines.decorator import create_pipeline_card
from opsml.pipelines.types import CodeInfo, INCLUDE_ARGS
from opsml.pipelines.spec import SpecDefaults, PipelineBaseSpecHolder, PipelineMetadata
from opsml.pipelines.writer import PipelineWriter

logger = ArtifactLogger.get_logger(__name__)


class PipelineCompressor:
    @staticmethod
    def tar_compress_code(dir_path: str):
        with tarfile.open(SpecDefaults.COMPRESSED_FILENAME, bufsize=10240, mode="w:gz") as tar:
            tar.add(dir_path, arcname=os.path.basename(dir_path))


class PipelineCodeUploader:
    def __init__(self, specs: PipelineBaseSpecHolder, spec_dirpath: str):
        """Uploads compressed pipeline code to a given storage location"""

        self.specs = specs
        self.spec_dirpath = spec_dirpath
        self.spec_dir_name = self.spec_dirpath.split("/")[-1]

    def _upload_code_to_server(self):
        """Uploads compressed pipeline package to opsml server"""
        api_client = cast(ApiClient, settings.request_client)
        filename = SpecDefaults.COMPRESSED_FILENAME
        files = {"file": open(os.path.join(filename), "rb")}  # pylint: disable=consider-using-with
        headers = {
            "Filename": filename,
            "WritePath": self.specs.pipeline_metadata.storage_root,
        }

        response = api_client.stream_post_request(
            route=ApiRoutes.UPLOAD,
            files=files,
            headers=headers,
        )

        storage_uri = response.get("storage_uri")

        if storage_uri is not None:
            return storage_uri
        raise ValueError("No storage_uri found")

    def _upload_code(self, destination_path: str) -> str:
        """Uploads pipeline code via api call or storage"""

        if settings.request_client is not None:
            return self._upload_code_to_server()

        return settings.storage_client.upload(
            local_path=SpecDefaults.COMPRESSED_FILENAME,
            write_path=destination_path,
        )

    def upload_compressed_code(self) -> CodeInfo:
        """
        Compresses code and uploads to cloud storage

        Returns:
            `CodeInfo`

        """
        destination_path = f"{self.specs.pipeline_metadata.storage_root}/{SpecDefaults.COMPRESSED_FILENAME}"
        code_uri = self._upload_code(destination_path=destination_path)

        return CodeInfo(
            code_uri=code_uri,
            source_dir=self.spec_dir_name,
        )


class PipelinePackager:
    def __init__(self, specs: PipelineBaseSpecHolder, requirements_file: Optional[str]):
        """
        Helper class for packaging pipeline code

        Args:
            spec:
                Pipeline specification dictionary
            requirements_file:
                Name of requirements file
            req_path:
                Requirements file path

        """
        self.requirements = requirements_file
        self.specs = specs

    def package_pipeline(self, spec_writer: YamlWriter, spec_dirpath: str):
        spec_writer.write_file()
        PipelineCompressor.tar_compress_code(dir_path=spec_dirpath)

    def _delete_copied_req(self):
        try:
            os.remove(self.req_path.req_path)
        except OSError as error:
            logger.error("Failed to remove copied requirements file: %s", error)

        if "poetry" in self.requirements:
            try:
                os.remove(self.req_path.toml_path)
            except OSError as error:
                logger.error("Failed to remove toml file: %s", error)

    def clean_up(self, writer: YamlWriter):
        # revert original spec file
        writer.revert_temp_to_orig()

        if self.requirements is not None:
            self._delete_copied_req()

    def upload_pipeline(
        self,
        spec_dirpath: str,
        specs: PipelineBaseSpecHolder,
    ) -> CodeInfo:
        code_info = PipelineCodeUploader(
            specs=specs,
            spec_dirpath=spec_dirpath,
        ).upload_compressed_code()

        return code_info

    # @create_pipeline_card
    def package_and_upload_pipeline(
        self,
        spec_dirpath: str,
        spec_filename: str,
    ) -> CodeInfo:
        """
        Packages and uploads pipeline code

        Args:
            spec_dirpath:
                Directory of specification file
            spec_filename:
                Specification filename

        Returns:
            `CodeInfo`
        """

        writer = YamlWriter(
            dict_=self.specs.dict(include=INCLUDE_ARGS),
            path=spec_dirpath,
            filename=spec_filename,
        )

        self.package_pipeline(
            spec_writer=writer,
            spec_dirpath=spec_dirpath,
        )
        code_info = self.upload_pipeline(
            spec_dirpath=spec_dirpath,
            specs=self.specs,
        )

        self.clean_up(writer=writer)

        return code_info

    def package_local(self, writer: PipelineWriter):
        run_id = self.specs.pipeline_metadata.run_id
        Path(run_id).mkdir(parents=True, exist_ok=True)
        self.specs.path = writer.write_pipeline(tmp_dir=run_id)

        code_info = CodeInfo(code_uri=self.specs.path, source_dir=run_id)

        return code_info

    def package_code(self, writer: PipelineWriter):
        """
        Packages and uploads pipeline code. If the pipeline is created using decorators,
        a temp directory is created and the pipeline is written to it prior to compression and upload.

        Args:
            writer:
                `PipelineWriter`
        """

        if self.specs.decorated:
            with tempfile.TemporaryDirectory() as tmp_dir:
                self.specs.path = writer.write_pipeline(tmp_dir=tmp_dir)
                spec_dir_path = self._get_pipeline_spec_path_info()
                return self._package_and_upload(spec_dirpath=spec_dir_path)

        spec_dir_path = self._get_pipeline_spec_path_info()
        return self._package_and_upload(spec_dirpath=spec_dir_path)

    def _package_and_upload(self, spec_dirpath: str):
        code_info = self.package_and_upload_pipeline(
            spec_dirpath=spec_dirpath,
            spec_filename=self.specs.source_file,
        )

        setattr(self.specs, "code_uri", code_info.code_uri)
        setattr(self.specs, "source_dir", code_info.source_dir)

        return code_info

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
