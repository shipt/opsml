"""Module for PipelinePlanner"""

import ast
import inspect
import textwrap
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
from opsml.helpers.logging import ArtifactLogger
from opsml.pipelines.types import PipelinePlan, MachineType, TaskArgs
from opsml.pipelines.writer_utils.types import SigTypeHints
from opsml.pipelines.types import PipelineParams, Tasks, PipelineSystem

logger = ArtifactLogger.get_logger(__name__)


TaskResourceType = Tuple[List[Callable[..., Any]], Optional[Dict[str, TaskArgs]]]
RelationshipType = Dict[str, Dict[str, List[Optional[str]]]]


class DecoParser:
    @staticmethod
    def parse_decorated_funcs(deco_task_list: List[Callable[..., Any]]):
        """Helper to to parse decorated functions"""
        tasks = []
        task_args = []
        for deco_func in deco_task_list:
            task, func = deco_func()
            tasks.append(func)
            task_args.append(task)
        return tasks, task_args


class TaskFuncParser:
    def __init__(
        self,
        function: Callable,
    ):
        self.vars_: Dict[str, Any] = {}
        self.func_src = textwrap.dedent(inspect.getsource(function))
        self.func_ast = cast(ast.FunctionDef, ast.parse(self.func_src).body[0])
        self.func_sig_params = inspect.signature(function).parameters

    def _parse_var_for_attribute(self, var: Any):
        if isinstance(var, ast.Assign) and hasattr(var.value, "n"):
            var_names = cast(List[ast.Name], var.targets)
            var_name = var_names[0].id
            var_val = var.value.n
            if not bool(var_val):
                self.vars_[var_name] = None

            elif any(substring in var_name for substring in ["count", "number", "retry"]):  # noqa
                self.vars_[var_name] = int(var_val)

            else:
                self.vars_[var_name] = str(var_val)

    def get_vars_from_func(self):
        for var in self.func_ast.body:
            self._parse_var_for_attribute(var=var)
        return self.vars_

    def artifact_type(self, type_name: str):
        return type_name == SigTypeHints.ARTIFACT_CARD

    def get_func_sig_params(self) -> List[Optional[str]]:
        params: List[Optional[str]] = []
        if self.func_sig_params:
            for param, type_ in self.func_sig_params.items():
                if not self.artifact_type(type_name=type_.annotation.__name__):
                    params.append(param)
        return params


class ResourceCreator:
    @staticmethod
    def create_resources_from_task_args(task_args: List[TaskArgs]):
        """Creates pipelines resource from TaskArg list"""
        resources: Dict[str, TaskArgs] = {}
        for task in task_args:
            resources[task.name] = task
        return resources

    @staticmethod
    def parse_task_args(
        task: Callable[..., Any],
    ) -> TaskArgs:
        """
        Parses pipeline task and assigns mandatory kwargs

        Args:
            task:
                Pipeline task
        Returns:
            Dictionary of task resources
        """
        task_name = task.__name__
        resource_dict = TaskFuncParser(function=task).get_vars_from_func()
        resource_dict["name"] = task_name

        resource_dict["machine_type"] = MachineType(**resource_dict)

        # validate tasks
        return TaskArgs(**resource_dict)


class PipelinePlanner:

    """
    Class that constructs a Pipeline plan for training from a
    configuration file.

    Args:
        pipeline_params:
            Pydantic model of pipeline configuration.
    """

    def __init__(
        self,
        params: PipelineParams,
        tasks: Tasks,
    ):
        self.params = params
        self.tasks, self.resources = self._set_pipeline_tasks(tasks=tasks)

        if not self._has_resources:
            self.resources = cast(Dict[str, TaskArgs], self._parse_non_deco_tasks())

        self._validate_compute_resources(pipeline_system=self.params.pipeline_system)
        self._parse_task_dependencies()

    def _validate_vertex(self):
        for name, task_args in self.resources.items():
            if not bool(task_args.machine_type.machine_type):
                raise ValueError(
                    f"""Error on task {name}. Machine type must be specified for Vertex Pipelines""",
                )

    def _validate_kubeflow(self):
        for name, task_args in self.resources.items():
            if not all(bool(arg) for arg in [task_args.machine_type.memory, task_args.machine_type.cpu]):
                logger.info(
                    """Task: %s - Memory and CPU must both be set if running on Kubeflow. Setting defaults""", name
                )
                task_args.machine_type.memory = 16
                task_args.machine_type.cpu = 2

    def _validate_compute_resources(self, pipeline_system: PipelineSystem):
        if pipeline_system == PipelineSystem.VERTEX:
            self._validate_vertex()
        elif pipeline_system != PipelineSystem.KUBEFLOW:
            self._validate_kubeflow()

    def _set_pipeline_tasks(self, tasks: Tasks) -> TaskResourceType:
        if tasks.decorated:
            task_list, task_args = DecoParser.parse_decorated_funcs(deco_task_list=tasks.task_list)
            resources = ResourceCreator.create_resources_from_task_args(task_args=task_args)
            return task_list, resources
        return tasks.task_list, {}

    @property
    def _has_resources(self):
        return bool(self.resources)

    def _parse_non_deco_tasks(self) -> Dict[str, TaskArgs]:
        """Parses list of functions into task argument pydantic model"""
        resources: Dict[str, TaskArgs] = {}
        for task in self.tasks:
            task_args = ResourceCreator.parse_task_args(task=task)
            resources[task_args.name] = task_args
        return resources

    @property
    def pipeline_plan(
        self,
    ) -> PipelinePlan:
        """
        Returns the pipeline plan
        """

        return PipelinePlan(
            tasks=self.tasks,
            resources=self.resources,
        )

    def _get_parent_relationships(self) -> RelationshipType:
        """Parses a task func arg to find upstream (parent dependencies)"""
        tasks: RelationshipType = {}
        for task in self.tasks[::-1]:
            tasks[task.__name__] = {
                "parents": TaskFuncParser(function=task).get_func_sig_params(),
            }

        self._validate_task_names(tasks=tasks)
        return tasks

    def _validate_task_names(self, tasks: RelationshipType) -> None:
        task_names = tasks.keys()

        for _, upstream_tasks in tasks.items():
            if bool(upstream_tasks):
                if not all(upstream_task in task_names for upstream_task in upstream_tasks["parents"]):
                    raise ValueError(
                        f"""Check spelling on task names and task input arguments, {upstream_tasks}, {task_names}"""
                    )

    def _get_child_relationships(self, parents: RelationshipType) -> RelationshipType:
        for parent_name, relationships in parents.items():
            children: List[Optional[str]] = []
            for child_name, child_parents in parents.items():
                if parent_name in cast(List[Optional[str]], child_parents.get("parents")):
                    children.append(child_name)
            relationships["children"] = children
        return parents

    def _get_parent_child_relationships(self):
        parents = self._get_parent_relationships()
        parents = self._get_child_relationships(parents=parents)

        return parents

    def _parse_task_dependencies(self):
        """Parses pipeline steps into resources and and pipeline step
        flow.
        """
        # set upstream dependencies
        task_relationships = self._get_parent_child_relationships()
        for task_name, relationships in task_relationships.items():
            self.resources[task_name].depends_on = relationships["parents"]  # noqa
            self.resources[task_name].destinations = relationships["children"]  # noqa

    def get_visualizer(self):
        """Visualize a pipeline

        Args:
            show_diagram (bool)
        """
        from fn_graph import Composer  # pylint: disable=import-outside-toplevel

        composer = Composer().update(*self.tasks)
        func_names = [func.__name__ for func in self.tasks]

        return composer, func_names
