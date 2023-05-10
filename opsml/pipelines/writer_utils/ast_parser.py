# pylint: disable=invalid-name,useless-parent-delegation
import ast
from typing import Any, List

# not sure if it's possible to refactor this given how NodeVisitor works


class FuncAstParser(ast.NodeVisitor):
    def __init__(self):
        self.var_names = []
        self.var_values = []
        self._return_vars = []
        self._return_lines = []
        self.default_return = None
        self.begin_line = None

    @property
    def assigned_vars(self):
        return dict(zip(self.var_names, self.var_values))

    @property
    def returned_vars(self) -> List[Any]:
        return self._return_vars[-1] if bool(self._return_vars) else []

    @property
    def return_line(self) -> int:
        return max(
            self._return_lines,
            default=self.default_return,
        )

    def get_first_line(self, func_def: ast.FunctionDef):
        func_body = func_def.body[0]
        return getattr(func_body, "lineno")

    def get_default_end_line(self, func_def: ast.FunctionDef):
        func_body = func_def.body[0]
        return getattr(func_body, "end_lineno")

    def visit_FunctionDef(self, node):

        if not bool(self.begin_line):
            self.begin_line = self.get_first_line(func_def=node)
            self.default_return = self.get_default_end_line(func_def=node)
            self.generic_visit(node)

    def visit_ClassDef(self, node):
        pass

    def visit_Subscript(self, node, value):
        var_name = node.value.id
        var_slice = node.slice.value

        # py3.8 issue
        if isinstance(var_slice, ast.Constant):
            var_slice = var_slice.value

        if isinstance(var_slice, str):
            self.var_names.append(f"{var_name}['{var_slice}']")
        else:
            self.var_names.append(f"{var_name}[{var_slice}]")

        if isinstance(value, ast.Constant):
            self.visit_Constant(value)
        elif isinstance(value, ast.Call):
            self.visit_Call(value)
        else:
            self.visit_None()

    def visit_Name(self, node):
        self.var_names.append(node.id)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.var_values.append(node.func.id)
        else:
            self.visit_None()

    def visit_Constant(self, node):
        self.var_values.append(node.value)

    def visit_None(self):
        self.var_values.append("None")

    def visit_Return(self, node):
        """Finds return line number and vars"""

        self._return_lines.append(node.lineno)

        func_return = []
        if isinstance(node.value, ast.Tuple):
            for var_ in node.value.elts:
                if isinstance(var_, ast.Name):
                    func_return.append(var_.id)

        elif isinstance(node.value, ast.Name):
            func_return.append(node.value.id)

        elif isinstance(node.value, ast.Dict):
            raise ValueError(
                """Dictionary returns are not yet supported for decorated functions.
            Either return a single variable or a tuple of variables.

            E.g. return var_1 or return var_1, var_2
            """
            )
        self._return_vars.append(func_return)

    def visit_Tuple(self, node, values):

        for name, value in zip(node.elts, values.elts):
            self.visit_Name(name)

            if isinstance(value, ast.Constant):
                self.visit_Constant(value)

            elif isinstance(value, ast.Call):
                self.visit_Call(value)

            else:
                self.visit_None()

    def visit_Assign(self, node):
        target = node.targets[0]
        value = node.value

        if isinstance(target, ast.Name):
            self.visit_Name(target)

            if isinstance(value, ast.Constant):
                self.visit_Constant(value)

            elif isinstance(value, ast.Call):
                self.visit_Call(value)

            else:
                self.visit_None()

        elif isinstance(target, ast.Tuple):
            self.visit_Tuple(target, value)

        elif isinstance(target, ast.Subscript):
            self.visit_Subscript(target, value)

    def visit_Expr(self, node):
        pass

    def visit_arguments(self, node) -> None:
        pass

    def visit_arg(self, node) -> None:
        pass

    def generic_visit(self, node):
        super().generic_visit(node)
