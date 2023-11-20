# Copyright (c) Shipt, Inc.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from opsml.helpers.logging import ArtifactLogger
from opsml.projects import MlflowProject, ProjectInfo
from opsml.registry import CardRegistries

logger = ArtifactLogger.get_logger()
registries = CardRegistries()

F = TypeVar("F", bound=Callable[..., Any])

def run(add_tags: Optional[str] = None) -> Callable[[F], F]:
    """
    Convenience method decorator for creating an opsml run
    Prevents re-writing the following for every task:

        project = MlflowProject(info=self.project_info)
        with project.run() as run:

    Parameters:
    - add_tags: str
        Attribute name of additional tags to be logged to run
        Expected format is a dictionary - keys represent tag names and the corresponding values represent tag values
    """
    
    def inner_run(func: F) -> F:
        @wraps(func)
        def wrapped(self, *args, **kwargs) -> Any:
            
            if any(isinstance(vals, ProjectInfo) for var,vals in self.__dict__.items()):
                for var,vals in self.__dict__.items():
                    if isinstance(vals, ProjectInfo):
                        project_info = vals
            else:
                raise ValueError("Project info not found")
            
            if isinstance(add_tags, str):
                
                if not bool(self.__dict__.get(add_tags, {})): 
                    logger.info(f"{add_tags} not defined in class. No additional tags added")
                else:
                    if isinstance(self.__dict__.get(add_tags), dict):
                        run_tag = self.__dict__.get(add_tags)
                    else:
                        raise TypeError(f"Tags must be defined as dictionary, but got {type(add_tags).__name__}")
            else:
                raise TypeError(f"Argument add_tags must be a string, but got {type(add_tags).__name__}")
            
            
            runcard = registries.run.list_cards(
                tags={"name": project_info.name, 
                      "team": project_info.team} | run_tag,
                as_dataframe=False,
            )

            if bool(runcard):
                project_info = ProjectInfo(
                    **{
                        **project_info.model_dump(),
                        **{"run_id": runcard[0].get("uid")},
                    }
                )

            project = MlflowProject(info=project_info)
            with project.run() as _run:
                for tag in run_tag.keys():
                    if tag not in _run.tags:
                        _run.add_tag(f"{tag}", run_tag.get(tag))
                        logger.info(f"Added {tag}: {run_tag.get(tag)}")

                func(self, _run, *args, **kwargs)

        return cast(F, wrapped)

    return inner_run
