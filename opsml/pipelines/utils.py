"""Module pipeline utils"""

from time import gmtime, strftime
from typing import Dict, Optional, Union, Any
import glob
import shutil
import os
import click
import re
import yaml
from pathlib import Path

from opsml.helpers.utils import FindPath


env_pattern = re.compile(r".*?\${(.*?)}.*?")
PIPELINE_SPEC_FILENAME = "pipeline-spec.yaml"


def echo(*args, **kwargs):
    """Echo func"""

    click.secho(*args, **kwargs)


def stdout_msg(msg, **kwargs):
    """Prints message to stdout"""

    echo(f"[{get_time()}]", fg="cyan", nl=False)
    echo(f" - {msg}", **kwargs)


def get_time():
    """Gets current time"""

    return strftime("%Y-%m-%d %H:%M:%S", gmtime())


class SpecLoader:
    def __init__(
        self,
        filename: str = PIPELINE_SPEC_FILENAME,
        dir_name: Optional[str] = None,
    ):
        """
        Loads a specification file and all associated environment variables

        Args:
            dir_name:
                Optional name of pipeline top-level-directory
            filename:
                spec filename

        """
        self.filename = filename
        self.dir_name = dir_name

    def _get_spec_path(self):
        if bool(self.dir_name):
            dir_path = FindPath.find_dirpath(
                dir_name=self.dir_name,
                anchor_file=self.filename,
            )
        else:
            dir_path = os.getcwd()

        return FindPath.find_filepath(path=dir_path, name=self.filename)

    def _open_spec(self, spec_path: str):
        """
        Loads a pipeline spec from path

        Args:
            spec_path:
                File path of pipeline spec
        """

        assert os.path.isfile(spec_path)
        with open(spec_path, "r", encoding="utf8") as file_:
            spec = yaml.safe_load(file_)
        return spec

    def _load_env_vars(self, spec: Dict[str, Any]):
        """
        Load environment vars specified in spec.

        Args:
            spec:
                Pipeline spec dictionary

        Returns:
            spec dictionary with environment variables injected
        """
        pipeline = spec.get("pipeline")

        if pipeline is not None:
            env_vars: Dict[str, str] = pipeline.get("env_vars")

            if env_vars is not None:
                for key, val in env_vars.items():
                    if isinstance(val, str) and "$" in val:
                        matches = env_pattern.findall(val)

                        for match in matches:
                            spec["pipeline"]["env_vars"][key] = os.getenv(match)

        return spec

    def load(self) -> Dict[Union[str, int], Any]:
        """
        Loads a specification file and all associated environment variables

        filename:
            spec filename

        Returns:
            spec dictionary

        """
        spec_path = self._get_spec_path()

        spec = self._open_spec(spec_path=spec_path)

        spec = self._load_env_vars(spec=spec)

        return spec


class FileWriter:
    """Abstract writer class"""

    def write_file(self):
        """Writes file"""
        raise NotImplementedError


class TemplateWriter(FileWriter):
    def __init__(
        self,
        template_mapping: Dict[str, str],
        template_path: Union[str, Path],
        file_path: str,
        filename: str,
    ):
        """
        Helper for decorator-based pipeline training that opens and writes to a pipeline task template

        Args:
            template_mapping:
                Dictionary mapping to apply to template
            template_path:
                Path to template file
            file_path:
                Path to file
            filename:
                name of file

        """
        self.template_mapping = template_mapping
        self.template_path = template_path
        self.file_path = file_path
        self.filename = filename

    def write_file(self) -> None:
        template = self.populate_template(template_mapping=self.template_mapping)

        with open(file=f"{self.file_path}/{self.filename}", mode="w", encoding="utf=8") as file_:
            file_.write(template)

    def populate_template(self, template_mapping: Dict[str, str]) -> str:
        with open(file=self.template_path, mode="r", encoding="utf=8") as file_:
            template = file_.read()
            template = template.format_map(template_mapping)

        return template


class YamlWriter(FileWriter):
    """Writer for yaml files"""

    def __init__(
        self,
        dict_: Dict[str, Any],
        path: str = os.getcwd(),
    ):
        """
        Instantiates class used to writing and re-writing
        pipeline configuration files.

        Args:
            dict_:
                Dictionary containing pipeline params/metadata
            path:
                Path to use to find file.
            filename:
                Name of pipeline config file.

        """
        self.filename = PIPELINE_SPEC_FILENAME
        self.path = path
        self.dict_ = dict_
        self.original_config = dict_

    def load_orig_config(self):
        orig_file = f"{self.path}/{self.filename}"
        with open(orig_file, encoding="utf-8") as file_:
            orig_config = yaml.safe_load(file_)

        self.original_config = orig_config

    @staticmethod
    def dict_to_yaml(
        dict_: Dict[Any, Any],
        filename: str,
        path: str = os.getcwd(),
    ):
        """
        Static method for writing a dictionary to yaml.

        Args:
            dict_:
                Dictionary
            filename:
                Name of file to write to
            path:
                Path to write file to
        """

        with open(f"{path}/{filename}", "w", encoding="utf-8") as file_:
            yaml.dump(dict_, file_, sort_keys=False)

    def write_file(self):
        """
        Aggregated function that writes dictionary to
        pipeline config

        """
        self.load_orig_config()
        self.dict_to_yaml(
            dict_=self.dict_,
            path=self.path,
            filename=self.filename,
        )

    def revert_temp_to_orig(self):
        """Reverts temporary config to original config file"""

        self.dict_to_yaml(
            dict_=self.original_config,
            path=self.path,
            filename=self.filename,
        )


class Copier:
    """Helper class to copy files to a specified directory"""

    @staticmethod
    def copy(
        src_dir: str,
        dest_dir: str,
    ):
        """
        Copies provided source directory to specified
        destination.

        Args:
            src_dir:
                Source directory
            dest_dir:
                Destination directory

        """
        # Make dest dir if not exist
        Path(dest_dir).mkdir(exist_ok=True)
        src_files = os.listdir(src_dir)
        for file_name in src_files:
            full_file_name = os.path.join(src_dir, file_name)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dest_dir)

    @staticmethod
    def copy_file_to_dir(
        dir_path: str,
        dir_name: str,
        filename: str,
    ):
        """
        Creates directory to store file in

        Args:
            dir_name:
                Directory name to create
            filename:
                File to copy to new directory
        """

        # create dir
        Path(f"{dir_path}/{dir_name}").mkdir(parents=True, exist_ok=True)

        # get file path
        filepath = glob.glob(pathname=f"{os.getcwd()}/**/{filename}", recursive=True)[0]

        shutil.copy(
            src=filepath,
            dst=f"{dir_path}/{dir_name}/{filename}",
        )

    @staticmethod
    def copy_dir_to_path(dir_name: str, new_path: str):
        dir_path = glob.glob(pathname=f"{os.getcwd()}/**/{dir_name}", recursive=True)[0]
        shutil.copytree(
            src=dir_path,
            dst=f"{new_path}/{dir_name}",
            dirs_exist_ok=True,
        )
