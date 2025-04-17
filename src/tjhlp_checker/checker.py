"""
同济高程代码合规检查
"""

import os
from enum import Enum
from pathlib import Path

import clang.cindex as CX
from clang.cindex import BinaryOperator as BO
from clang.cindex import CursorKind as CK

from .config import Config


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
    BIT_OPERATION = 12
    SYSTEM_CLASS = 13
    INTERNAL_GLOBAL = 14
    EXTERNAL_GLOBAL = 15
    STATIC_LOCAL = 16


class RuleViolation:
    kind: ViolationKind
    cursor: CX.Cursor
    context: CX.Cursor
    extra_message: str

    def __init__(
        self,
        kind: ViolationKind,
        cursor: CX.Cursor,
        context: CX.Cursor,
        extra_message: str = "",
    ) -> None:
        self.kind = kind
        self.cursor = cursor
        self.context = context
        self.extra_message = extra_message

    def __str__(self) -> str:
        location = self.cursor.location
        return f"{str(self.kind).removeprefix('ViolationKind.')} ({location.line}, {location.column})"

    def __repr__(self) -> str:
        return str(self)


def find_all_violations(file: Path, config: Config):
    if not CX.Config.loaded:
        libclang_path = os.environ.get("LIBCLANG_PATH")
        if not libclang_path:
            raise RuntimeError(
                "Cannot find libclang installation. Please make sure LLVM is installed and env variable 'LIBCLANG_PATH' is set correctlly."
            )

        CX.Config.set_library_path(libclang_path)

    parse_options = CX.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
    if file.name.endswith((".h", ".hpp")):
        parse_options |= CX.TranslationUnit.PARSE_INCOMPLETE

    index = CX.Index.create()
    tu = index.parse(
        str(file.resolve()),
        options=parse_options,
        args=[f"-finput-charset={config.common.encoding}"] + (["-m32"] if config.common.is_32bit else []),
    )

    rule_violations: list[RuleViolation] = []

    def record_violation(
        kind: ViolationKind,
        node: CX.Cursor,
        context: CX.Cursor,
        extra_message: str = "",
    ):
        rule_violations.append(RuleViolation(kind, node, context, extra_message))

    def check_inclusion(node: CX.Cursor, context: CX.Cursor):
        assert node.kind == CK.INCLUSION_DIRECTIVE

        try:
            filename = node.get_included_file().name
        except AssertionError:
            # 若包含的头文件不存在，则直接忽略
            return

        if (path := Path(filename).resolve()).is_relative_to(
            config.header.base_path
        ):
            # 本地头文件，和禁用的头文件重名可以接受
            return

        if (config.header.whitelist and path.name not in config.header.whitelist) or (
            path.name in config.header.blacklist
        ):
            record_violation(ViolationKind.HEADER, node, context)

    def check_var_type(node_type: CX.Type) -> ViolationKind | None:
        # 去除类型别名
        canonical_type = node_type.get_canonical()

        match canonical_type.kind:
            case CX.TypeKind.RECORD:
                if config.grammar.system_class.disable:
                    # 如果不是用户自定义的类, 则检查是否在白名单中
                    diclaration = node_type.get_declaration()
                    assert diclaration
                    if (
                        diclaration.location.is_in_system_header
                        and node_type.spelling
                        not in config.grammar.system_class.whitelist
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
                if config.grammar.disable_pointer:
                    return ViolationKind.POINTER
                # 递归检查指向的类型
                return check_var_type(canonical_type.get_pointee())
            # 引用
            case CX.TypeKind.LVALUEREFERENCE | CX.TypeKind.RVALUEREFERENCE:
                if config.grammar.disable_reference:
                    return ViolationKind.REFERENCE
                # 递归检查指向的类型
                return check_var_type(canonical_type.get_pointee())
            # 64位/128位整数
            case CX.TypeKind.LONGLONG | CX.TypeKind.ULONGLONG | CX.TypeKind.INT128:
                if config.grammar.disable_int64_or_larger:
                    return ViolationKind.INT64

    def check_var_declaration(node: CX.Cursor, context: CX.Cursor):
        if type_violation_kind := check_var_type(node.type):
            record_violation(type_violation_kind, node, context)
        # 静态全局/在匿名命名空间里的全局（除全局常变量）
        if (
            config.grammar.disable_internal_global_var
            and node.linkage == CX.LinkageKind.INTERNAL
            and not node.type.is_const_qualified()
        ):
            record_violation(ViolationKind.INTERNAL_GLOBAL, node, context)
        if config.grammar.disable_external_global_var and node.linkage in (
            CX.LinkageKind.EXTERNAL,
            CX.LinkageKind.UNIQUE_EXTERNAL,
        ):
            record_violation(ViolationKind.EXTERNAL_GLOBAL, node, context)
        if (
            config.grammar.disable_static_local_var
            and node.storage_class == CX.StorageClass.STATIC
            and node.linkage == CX.LinkageKind.NO_LINKAGE
        ):
            record_violation(ViolationKind.EXTERNAL_GLOBAL, node, context)

    def check_func_declaration(node: CX.Cursor, context: CX.Cursor):
        if config.grammar.disable_function and node.spelling != "main":
            record_violation(ViolationKind.FUNCTION, node, context)

        if type_violation_kind := check_var_type(node.result_type):
            record_violation(type_violation_kind, node, context)

    def check_binary_operator(node: CX.Cursor, context: CX.Cursor):
        match node.binary_operator:
            case (
                BO.Shl
                | BO.ShlAssign
                | BO.Shr
                | BO.ShrAssign
                | BO.And
                | BO.AndAssign
                | BO.Or
                | BO.OrAssign
                | BO.Xor
                | BO.XorAssign
            ):
                if config.grammar.disable_bit_operation:
                    record_violation(ViolationKind.BIT_OPERATION, node, context)
            case BO.LAnd | BO.LE | BO.EQ | BO.NE | BO.LOr | BO.LT | BO.GT | BO.GE:
                if config.grammar.disable_branch:
                    record_violation(ViolationKind.BRANCH, node, context)

    def check_unary_operator(node: CX.Cursor, context: CX.Cursor):
        operator_token = next(node.get_tokens())

        if operator_token.spelling == "!":
            if config.grammar.disable_branch:
                record_violation(ViolationKind.BRANCH, node, context)
        if operator_token.spelling == "~":
            if config.grammar.disable_bit_operation:
                record_violation(ViolationKind.BIT_OPERATION, node, context)

    def traverse(node: CX.Cursor, context: CX.Cursor):
        match node.kind:
            case CK.INCLUSION_DIRECTIVE:
                check_inclusion(node, context)
            case CK.VAR_DECL | CK.PARM_DECL | CK.FIELD_DECL:
                check_var_declaration(node, context)
            case CK.FUNCTION_DECL:
                context = node
                check_func_declaration(node, context)
            case CK.BINARY_OPERATOR:
                check_binary_operator(node, context)
            case CK.ARRAY_SUBSCRIPT_EXPR:
                if config.grammar.disable_array:
                    record_violation(ViolationKind.ARRAY, node, context)
            case CK.CONDITIONAL_OPERATOR | CK.IF_STMT | CK.SWITCH_STMT:
                if config.grammar.disable_branch:
                    record_violation(ViolationKind.BRANCH, node, context)
            case CK.GOTO_STMT:
                if config.grammar.disable_goto:
                    record_violation(ViolationKind.GOTO, node, context)
            case CK.WHILE_STMT | CK.FOR_STMT | CK.DO_STMT:
                if config.grammar.disable_loop:
                    record_violation(ViolationKind.LOOP, node, context)
            case CK.UNARY_OPERATOR:
                # TODO: 检查形如 *(p+i) 的非法指针使用
                check_unary_operator(node, context)
            case CK.CONDITIONAL_OPERATOR:
                if config.grammar.disable_branch:
                    record_violation(ViolationKind.BRANCH, node, context)
            case CK.STRUCT_DECL:
                context = node
                if config.grammar.disable_struct:
                    record_violation(ViolationKind.STRUCT, node, context)
            case CK.CLASS_DECL:
                context = node
                if config.grammar.disable_class:
                    record_violation(ViolationKind.CLASS, node, context)
            case CK.INTEGER_LITERAL:
                if vk := check_var_type(node.type):
                    record_violation(vk, node, context)
            # TODO: 检查显式类型转换中违规使用 int64
            # TODO: 检查违规使用系统函数（）

        children = list(
            child
            for child in node.get_children()
            if not child.location.is_in_system_header
        )

        for child in children:
            traverse(child, context)

    assert tu.cursor
    traverse(tu.cursor, tu.cursor)

    return rule_violations
