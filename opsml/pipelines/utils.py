"""Module pipeline utils"""

from time import gmtime, strftime
from typing import Dict, Optional, Union, Any

import os
import click
import re
import yaml

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
        env_vars: Dict[str, str] = spec.get("env_vars")

        if env_vars is not None:
            for key, val in env_vars.items():
                if isinstance(val, str) and "$" in val:
                    matches = env_pattern.findall(val)

                    for match in matches:
                        spec["env_vars"][key] = os.getenv(match)

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
