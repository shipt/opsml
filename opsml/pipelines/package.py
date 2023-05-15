import os
import shutil
import tarfile
from pathlib import Path
from typing import Dict, Optional, Any

from opsml.pipelines import settings
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.utils import YamlWriter
from opsml.helpers.utils import FindPath
from opsml.helpers import exceptions

# from opsml.pipelines.decorator import create_pipeline_card
from opsml.pipelines.types import RequirementPath, CodeInfo
from opsml.pipelines.spec import SpecDefaults, PipelineBaseSpecs
from opsml.pipelines.writer import PipelineWriter

logger = ArtifactLogger.get_logger(__name__)

REQUIREMENTS_FILE = "requirements.txt"
PYPROJECT_FILE = "pyproject.toml"


class RequirementsCopier:
    def __init__(
        self,
        requirements_file: str,
        spec_filepath: str,
    ):
        self.requirements = requirements_file
        self.spec_filepath = spec_filepath

    def copy_req_to_src(self) -> RequirementPath:
        """
        Finds a given requirements file (requirements.txt or poetry.lock
        and copies it to the dir path. Needed for installing packages when
        running container.


        Args:
            requirements:
                String indicating requirements file. Options are "requirements.txt" and "poetry.lock".

        """
        try:
            req_path = FindPath.find_filepath(self.requirements)
        except IndexError as error:
            raise exceptions.NoRequirements(
                f"""No requirement file found. Please make sure the requirements file is in the
                current working directory, {error}"""
            )
        except ValueError as error:
            raise exceptions.MoreThanOnePath(
                f"""More than one requirements file found.
            Try either renaming the requirements file or removing others from
            your path. {error}
            """
            )

        self._check_requirements(req_path=req_path)
        shutil.copy(req_path, self.spec_filepath)

        if ".txt" in self.requirements:
            moved_req_path = self._rename_requirements_file()

        if "poetry" in self.requirements:
            moved_req_path = self._copy_pyproject_toml(str(req_path))

        return RequirementPath(
            req_path=moved_req_path,
            toml_path=f"{self.spec_filepath}/{PYPROJECT_FILE}",
        )

    def _check_requirements(self, req_path: str):
        with open(req_path, "r", encoding="utf-8") as filepath:
            lines = filepath.readlines()
            for line in lines:
                if line.find("pyshipt") != -1:
                    raise ValueError(
                        """Found pyshipt libraries in requirements file. Internal libraries are not
                        currently supported in Vertex due to networking issues. Docker environments
                        already have latest versions of pyshipt-logging and pyshipt-sql."""
                    )

    def _rename_requirements_file(self) -> str:
        os.rename(
            f"{self.spec_filepath}/{self.requirements}",
            f"{self.spec_filepath}/{REQUIREMENTS_FILE}",
        )
        return f"{self.spec_filepath}/{REQUIREMENTS_FILE}"

    def _copy_pyproject_toml(self, req_path: str) -> str:
        path_split = req_path.split("/")
        req_file = path_split[-1]
        base_path = "/".join(path_split[:-1])
        toml_path = f"{base_path}/{PYPROJECT_FILE}"
        shutil.copy(toml_path, self.spec_filepath)

        return f"{self.spec_filepath}/{req_file}"


class PipelineCompressor:
    @staticmethod
    def tar_compress_code(dir_path: str):
        with tarfile.open(SpecDefaults.COMPRESSED_FILENAME, bufsize=10240, mode="w:gz") as tar:
            tar.add(dir_path, arcname=os.path.basename(dir_path))


class PipelineCodeUploader:
    def __init__(self, specs: PipelineBaseSpecs, spec_dir_name: str):
        """Uploads compressed pipeline code to a given storage location"""

        self.specs = specs
        self.spec_dir_name = spec_dir_name

    def _upload_code_to_server(self):
        # iterate and load file to server
        filename = SpecDefaults.COMPRESSED_FILENAME
        response = settings.request_client.post_request()

        # need to add storage_uri + path
        return response["pipeline_storage_path"]

    # change to storage client
    def _upload_code(self, destination_path: str) -> str:
        # if settings.request_client, upload file to path

        if settings.request_client:
            return self._upload_code_to_server()

        return settings.storage_client.upload(
            local_path=SpecDefaults.COMPRESSED_FILENAME,
            write_path=f"{settings.storage_settings.storage_uri}/{destination_path}",
        )

    def upload_compressed_code(self) -> CodeInfo:
        """
        Compresses code and uploads to cloud storage

        Returns:
            `CodeInfo`

        """
        destination_path = f"{self.specs.pipe_storage_root}/{SpecDefaults.COMPRESSED_FILENAME}"
        code_uri = self._upload_code(destination_path=destination_path)

        return CodeInfo(
            code_uri=code_uri,
            source_dir=self.spec_dir_name,
        )


class PipelinePackager:
    def __init__(
        self,
        specs: Dict[str, Any],
        requirements_file: Optional[str],
        req_path: Optional[RequirementPath] = None,
    ):
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
        self.req_path = req_path

    def package_pipeline(self, spec_writer: YamlWriter, spec_dirpath: str):
        spec_writer.write_file()

        if self.requirements is not None:
            self.req_path = RequirementsCopier(
                requirements_file=self.requirements,
                spec_dirpath=spec_dirpath,
            ).copy_req_to_src()

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
        spec_dir_name: str,
        specs: PipelineBaseSpecs,
    ) -> CodeInfo:
        code_info = PipelineCodeUploader(
            specs=specs,
            spec_dir_name=spec_dir_name,
        ).upload_compressed_code()

        return code_info

    # @create_pipeline_card
    def package_and_upload_pipeline(self, spec_dirpath: str, spec_filename: str) -> CodeInfo:
        writer = YamlWriter(
            dict_=self.specs,
            path=spec_dirpath,
            filename=spec_filename,
        )

        self.package_pipeline(
            spec_writer=writer,
            spec_filepath=spec_dirpath,
        )
        a
        code_info = self.upload_pipeline(spec_dir_name=spec_dir_name, specs=self.specs)

        self.clean_up(writer=writer)

        return code_info

    def package_local(self, writer: PipelineWriter, specs: PipelineBaseSpecs):
        Path(specs.run_id).mkdir(parents=True, exist_ok=True)
        specs.path = writer.write_pipeline(tmp_dir=specs.run_id)

        code_info = CodeInfo(
            code_uri=specs.path,
            source_dir=specs.run_id,
        )

        return code_info
