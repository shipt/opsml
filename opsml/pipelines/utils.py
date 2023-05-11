"""Module pipeline utils"""

from time import gmtime, strftime
from typing import Dict, Optional, Union, Any

import os
import click
import re
import yaml

from opsml.helpers.utils import FindPath


env_pattern = re.compile(r".*?\${(.*?)}.*?")
PIPELINE_CONFIG_FILENAME = "pipeline-config.yaml"


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


class ConfigFileLoader:
    def __init__(
        self,
        filename: str = PIPELINE_CONFIG_FILENAME,
        dir_name: Optional[str] = None,
    ):
        """
        Loads a configuration file and all associatedenvironment variables

        dir_name:
            Optional name of pipeline top-level-directory
        filename:
            Config filename

        """

        self.filename = filename
        self.dir_name = dir_name

    def _get_config_path(self):
        if bool(self.dir_name):
            dir_path = FindPath.find_dirpath(
                dir_name=self.dir_name,
                anchor_file=self.filename,
            )
        else:
            dir_path = os.getcwd()

        return FindPath.find_filepath(path=dir_path, name=self.filename)

    def _open_config(self, config_path: str):
        assert os.path.isfile(config_path)
        with open(config_path, "r", encoding="utf8") as file_:
            config = yaml.safe_load(file_)
        return config

    def _load_env_vars(self, config: Dict[str, Any]):
        for key, val in config.items():
            if isinstance(val, str):
                matches = env_pattern.findall(val)
                for match in matches:
                    config[key] = os.getenv(match)
        return config

    def load(self) -> Dict[Union[str, int], Any]:
        """
        Loads a configuration file and all associated environment variables

        filename:
            Config filename

        Returns:
            config dictionary

        """
        config_path = self._get_config_path()
        config = self._open_config(config_path=config_path)

        config = self._load_env_vars(config=config)

        return config
