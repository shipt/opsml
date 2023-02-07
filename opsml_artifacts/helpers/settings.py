import logging
import os
import sys
from datetime import datetime
from typing import IO, Any

from pythonjsonlogger.jsonlogger import JsonFormatter

APP_ENV = os.getenv("APP_ENV", "development")


class LogFormatter(JsonFormatter):
    """Custom formatter"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        log_record["app_env"] = APP_ENV
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


# credit to pyshipt-logging for implementation logic
class ArtifactLogger:
    @classmethod
    def get_handler(cls, stream: IO = sys.stdout) -> logging.StreamHandler:
        log_handler = logging.StreamHandler(stream)
        formatter = LogFormatter()
        log_handler.setFormatter(formatter)
        return log_handler

    @classmethod
    def get_logger(
        cls,
        name: str,
        stream: IO = sys.stdout,
    ):
        log = logging.getLogger(name)

        # Add a new stream handler if the log is new
        if len(log.handlers) == 0:
            log.addHandler(cls.get_handler(stream=stream))

        log_level: int = logging.getLevelName("INFO")
        log.setLevel(log_level)
        log.propagate = False

        return log


# class MockSettings(BaseSettings):
#    class Config:
#        arbitrary_types_allowed = True
#        extra = "allow"
#
#
# def get_settings():
#    if bool(os.getenv("ARTIFACT_TESTING_MODE")):
#        from opsml_artifacts.helpers.fixtures.mock_vars import mock_vars
#
#        return MockSettings(**mock_vars)


# might be a better way to do this in the future
# def get_settings():
#    if bool(os.getenv("ARTIFACT_TESTING_MODE")):
#        from opsml_artifacts.helpers.fixtures.mock_vars import mock_vars
#        return MockSettings(**mock_vars)
#    else:
#        if os.getenv("OPMSL_ARTIFACT_ENV").lower() == "gcp":
#
#
#    return GlobalSettings()
#
#
# settings = get_settings()
