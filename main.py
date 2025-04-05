"""
同济高程代码合规检查
"""

from typing import Annotated
import clang.cindex as CX
from clang.cindex import CursorKind as CK, BinaryOperator as BO
import typer
import pathlib
from enum import Enum
from config import Config, load_config
# from rich import print

#  工作基准目录，用来判定头文件是否为系统头文件（用户自定义头文件不受blacklist/whitelist限制）
#  TODO: 由用户指定
basePath = pathlib.Path.cwd()


class ViolationKind(Enum):
    HEADER = 0
    INT64 = 1
    POINTER = 2
    REFERENCE = 3
    ARRAY = 4
    STRUCT = 5
    CLASS = 6
    FUNCTION = 7
    AUTO = 8
    BRANCH = 9
    GOTO = 10
    LOOP = 11
    RANGE_BASED_LOOP = 12
    BIT_OPERATION = 13
    SYSTEM_CLASS = 14


class RuleViolation:
    kind: ViolationKind
    cursor: CX.Cursor
    extra_message: str

    def __init__(
        self, kind: ViolationKind, cursor: CX.Cursor, extra_message: str = ""
    ) -> None:
        self.kind = kind
        self.cursor = cursor
        self.extra_message = extra_message

    def __str__(self) -> str:
        location = self.cursor.location
        return f"{str(self.kind).removeprefix('ViolationKind.')} ({location.line}, {location.column})"

    def __repr__(self) -> str:
        return str(self)


def find_all_violations(tu: CX.TranslationUnit, config: Config):
    rule_violations: list[RuleViolation] = []

    def check_inclusion(node: CX.Cursor):
        assert node.kind == CK.INCLUSION_DIRECTIVE
        # print(list(token.spelling for token in node.get_tokens()))
        if (
            path := pathlib.Path(node.get_included_file().name).resolve()
        ).is_relative_to(basePath):
            # 本地头文件，和禁用的头文件重名可以接受
            return

        if (config.header.whitelist and path.name not in config.header.whitelist) or (
            path.name in config.header.blacklist
        ):
            rule_violations.append(
                RuleViolation(
                    ViolationKind.HEADER,
                    node,
                )
            )

    def check_var_type(node_type: CX.Type):
        # 去除类型别名
        canonical_type = node_type.get_canonical()

        match canonical_type.kind:
            case CX.TypeKind.RECORD:
                # 如果不是用户自定义的类, 则检查是否在白名单中
                if (
                    config.grammar.system_class.disable
                    and node_type.get_declaration().location.is_in_system_header
                    and node_type.spelling not in config.grammar.system_class.whitelist
                ):
                    return ViolationKind.SYSTEM_CLASS
            # 检查是否数组
            case CX.TypeKind.CONSTANTARRAY | CX.TypeKind.VARIABLEARRAY:
                if config.grammar.disable_array:
                    return ViolationKind.ARRAY
                # 递归检查数组元素
                return check_var_type(canonical_type.element_type)

            # 检查是否指针
            case CX.TypeKind.POINTER:
                if config.grammar.disable_pointers:
                    return ViolationKind.POINTER
                # 递归检查指向的类型
                check_var_type(canonical_type.get_pointee())
            # 引用
            case CX.TypeKind.LVALUEREFERENCE | CX.TypeKind.RVALUEREFERENCE:
                if config.grammar.disable_reference:
                    return ViolationKind.REFERENCE
                # 递归检查指向的类型
                check_var_type(canonical_type.get_pointee())
            # 64位/128位整数
            case CX.TypeKind.LONGLONG | CX.TypeKind.ULONGLONG | CX.TypeKind.INT128:
                if config.grammar.disable_int64_or_larger:
                    return ViolationKind.INT64

    def check_var_declaration(node: CX.Cursor):
        if type_violation_kind := check_var_type(node.type):
            rule_violations.append(RuleViolation(type_violation_kind, node))

    def check_func_declaration(node: CX.Cursor):
        if config.grammar.disable_function and node.spelling != "main":
            rule_violations.append(RuleViolation(ViolationKind.FUNCTION, node))

        if type_violation_kind := check_var_type(node.result_type):
            rule_violations.append(RuleViolation(type_violation_kind, node))

    def check_binary_operator(node: CX.Cursor):
        match node.binary_operator:
            case (
                BO.Shl
                | BO.ShlAssign
                | BO.Shr
                | BO.ShrAssign
                | BO.And
                | BO.AddAssign
                | BO.Or
                | BO.OrAssign
                | BO.Xor
                | BO.XorAssign
            ):
                if config.grammar.disable_bit_operation:
                    rule_violations.append(
                        RuleViolation(ViolationKind.BIT_OPERATION, node)
                    )
            case BO.LAnd | BO.LE | BO.EQ | BO.NE | BO.LOr | BO.LT | BO.GT | BO.GE:
                if config.grammar.disable_branch:
                    rule_violations.append(RuleViolation(ViolationKind.BRANCH, node))

    def traverse(node: CX.Cursor):
        match node.kind:
            case CK.INCLUSION_DIRECTIVE:
                check_inclusion(node)
            case CK.VAR_DECL | CK.PARM_DECL:
                check_var_declaration(node)
            case CK.FUNCTION_DECL:
                check_func_declaration(node)
            case CK.BINARY_OPERATOR:
                check_binary_operator(node)
            case CK.ARRAY_SUBSCRIPT_EXPR:
                if config.grammar.disable_array:
                    rule_violations.append(RuleViolation(ViolationKind.ARRAY, node))
            case CK.CONDITIONAL_OPERATOR | CK.IF_STMT | CK.SWITCH_STMT:
                if config.grammar.disable_branch:
                    rule_violations.append(RuleViolation(ViolationKind.BRANCH, node))
            case CK.GOTO_STMT:
                if config.grammar.disable_goto:
                    rule_violations.append(RuleViolation(ViolationKind.GOTO, node))
            case CK.WHILE_STMT | CK.FOR_STMT | CK.DO_STMT:
                if config.grammar.disable_loop:
                    rule_violations.append(RuleViolation(ViolationKind.LOOP, node))
            case CK.UNARY_OPERATOR:
                # TODO: 检查单目位运算符/逻辑运算符
                # TODO: 检查形如 *(p+i) 的非法指针使用
                pass
            case CK.CONDITIONAL_OPERATOR:
                if config.grammar.disable_branch:
                    rule_violations.append(RuleViolation(ViolationKind.BRANCH, node))
            case CK.STRUCT_DECL:
                if config.grammar.disable_struct:
                    rule_violations.append(RuleViolation(ViolationKind.STRUCT, node))
            case CK.CLASS_DECL:
                if config.grammar.disable_class:
                    rule_violations.append(RuleViolation(ViolationKind.CLASS, node))

        children = list(
            child
            for child in node.get_children()
            if not child.location.is_in_system_header
        )

        for child in children:
            traverse(child)

    traverse(tu.cursor)

    return rule_violations


def main(
    file: Annotated[str, typer.Argument(help="The path of input file")],
    config_file: Annotated[str, typer.Option(help="The path of config file")],
):
    with open(config_file, "rb") as f:
        config = load_config(f)

    if config.common.libclang_file:
        CX.Config.set_library_file(config.common.libclang_file)

    if config.common.libclang_path:
        CX.Config.set_library_path(config.common.libclang_path)

    parse_options = CX.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    if file.endswith((".h", ".hpp")):
        parse_options |= CX.TranslationUnit.PARSE_INCOMPLETE

    index = CX.Index.create()
    tu = index.parse(
        file, options=parse_options, args=[f"-finput-charset={config.common.encoding}"]
    )

    violations = find_all_violations(tu, config)
    if violations:
        print(f"Found {len(violations)} violations in {file}:")
        with open(file, "rb") as src:
            src_text = src.read()
            for violation in violations:
                source_range = violation.cursor.extent
                print(
                    str(violation),
                    src_text[
                        source_range.start.offset : source_range.end.offset
                    ].decode(config.common.encoding),
                )


if __name__ == "__main__":
    typer.run(main)
