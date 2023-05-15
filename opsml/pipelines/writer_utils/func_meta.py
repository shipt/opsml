import ast
import inspect
import textwrap
from typing import Any, Callable, List, Mapping, Optional, cast

from opsml.pipelines.writer_utils.ast_parser import FuncAstParser
from opsml.pipelines.writer_utils.types import (
    ARTIFACT_CARD_TYPES,
    FuncMetadata,
    ParserOutput,
    SigTypeHints,
)

AST_ARGS = [ast.ImportFrom, ast.Import, ast.Assign, ast.Pass, ast.AnnAssign]


class Parser:
    def __init__(
        self,
        func_body: str,
        ast_parser: FuncAstParser,
        sig_params: Mapping[str, inspect.Parameter],
        func_lines: List[str],
        func_name: str,
    ):
        self.func_body = func_body
        self.sig_params = sig_params
        self.ast_parser = ast_parser
        self.func_lines = func_lines
        self.func_name = func_name
        self.has_return = False

    def parse(self) -> ParserOutput:
        raise NotImplementedError

    @staticmethod
    def validate(parse_type: str) -> bool:
        raise NotImplementedError


class FuncDefParser(Parser):
    def artifact_type(self, type_name: str):
        return type_name in SigTypeHints.ARTIFACT_CARD

    def parse(self) -> ParserOutput:
        args = []
        if bool(self.sig_params):
            for param, type_ in self.sig_params.items():
                if not self.artifact_type(type_.annotation.__name__):
                    args.append(param)

        return ParserOutput(func_def=f"def {self.func_name}({','.join(args)}):")

    @staticmethod
    def validate(parse_type: str) -> bool:
        return parse_type == "definition"


class FuncBodyParser(Parser):
    def parse(self) -> ParserOutput:
        begin = self.ast_parser.begin_line - 1
        end = self.ast_parser.return_line - 1

        # in case of no return statement
        if begin == end:
            end = len(self.func_lines)

        text = textwrap.dedent("".join(self.func_lines[begin:end]))
        return ParserOutput(func_body=text)

    @staticmethod
    def validate(parse_type: str) -> bool:
        return parse_type == "body"


class FuncCardParser(Parser):
    def artifact_type(self, type_name: str) -> bool:
        return type_name in SigTypeHints.ARTIFACT_CARD

    def get_cards_to_load(self):
        cards_to_load = []
        if bool(self.sig_params):
            for param, type_ in self.sig_params.items():
                if self.artifact_type(type_name=type_.annotation.__name__):
                    cards_to_load.append(param)

        return cards_to_load

    def get_cards_to_save(self) -> List[Optional[str]]:
        """
        Looks through assigned vars for ArtifactCards and
        searches return statement to see if any are returned
        """
        assigned_cards = []
        for var_name, var_value in self.ast_parser.assigned_vars.items():
            card_type = var_value.lower().split("card")[0]

            if self._is_card(card_type=card_type):
                assigned_cards.append(var_name)

            if bool(self.ast_parser.returned_vars):
                self.has_return = True

        if self.has_return:
            return self._compare_assigned_and_returned(
                assigned_cards=assigned_cards,
                return_vars=self.ast_parser.returned_vars,
            )

        return []

    def _compare_assigned_and_returned(
        self,
        assigned_cards: List[str],
        return_vars: List[str],
    ):
        return [var_ for var_ in return_vars if var_ in assigned_cards]

    def _is_card(self, card_type: str):
        return card_type in ARTIFACT_CARD_TYPES

    def parse(self) -> ParserOutput:
        cards_to_save = self.get_cards_to_save()

        return ParserOutput(cards_to_save=cards_to_save)

    @staticmethod
    def validate(parse_type: str) -> bool:
        return parse_type == "card"


class FuncMetaCreator:
    def __init__(
        self,
        function: Callable[..., Any],
        name: str,
    ):
        self.func_name = name
        self.function = function
        self.func_body = textwrap.dedent(inspect.getsource(function))
        self.ast_parser = self._get_ast_parser()
        self.func_lines = inspect.getsourcelines(function)[0]
        self.sig_params = cast(Mapping[str, inspect.Parameter], inspect.signature(self.function).parameters)

    def _get_ast_parser(self):
        parser = FuncAstParser()
        parsed = ast.parse(self.func_body)
        parser.visit(parsed)

        return parser

    def parse(self) -> FuncMetadata:
        definition = self._parse_type(parse_type="definition")
        body = self._parse_type(parse_type="body")
        cards = self._parse_type(parse_type="card")

        return FuncMetadata(
            name=self.func_name,
            assigned_cards=cards.cards_to_save,
            text=body.func_body,
            definition=definition.func_def,
        )

    def _parse_type(self, parse_type: str) -> ParserOutput:
        parser = next(parser for parser in Parser.__subclasses__() if parser.validate(parse_type=parse_type))

        return parser(
            func_name=self.func_name,
            func_body=self.func_body,
            sig_params=self.sig_params,
            ast_parser=self.ast_parser,
            func_lines=self.func_lines,
        ).parse()
