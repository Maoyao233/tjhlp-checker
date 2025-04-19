from clang.cindex import BaseEnumeration, Cursor, c_int
from clang.cindex import functionList, conf  # type: ignore

functionList.append(("clang_getCursorBinaryOperatorKind", [Cursor], c_int))
functionList.append(("clang_getUnaryOperatorKindSpelling", [Cursor], c_int))


class BinaryOperator(BaseEnumeration):
    """
    Describes the BinaryOperator of a declaration
    """

    # The required BaseEnumeration declarations.
    _kinds = []
    _name_map = None

    def __nonzero__(self):
        """Allows checks of the kind ```if cursor.binary_operator:```"""
        return self.value != 0

    @property
    def is_assignment(self):
        return BinaryOperator.Assign.value <= self.value < BinaryOperator.Comma.value

    Invalid: "BinaryOperator"
    PtrMemD: "BinaryOperator"
    PtrMemI: "BinaryOperator"
    Mul: "BinaryOperator"
    Div: "BinaryOperator"
    Rem: "BinaryOperator"
    Add: "BinaryOperator"
    Sub: "BinaryOperator"
    Shl: "BinaryOperator"
    Shr: "BinaryOperator"
    Cmp: "BinaryOperator"
    LT: "BinaryOperator"
    GT: "BinaryOperator"
    LE: "BinaryOperator"
    GE: "BinaryOperator"
    EQ: "BinaryOperator"
    NE: "BinaryOperator"
    And: "BinaryOperator"
    Xor: "BinaryOperator"
    Or: "BinaryOperator"
    LAnd: "BinaryOperator"
    LOr: "BinaryOperator"
    Assign: "BinaryOperator"
    MulAssign: "BinaryOperator"
    DivAssign: "BinaryOperator"
    RemAssign: "BinaryOperator"
    AddAssign: "BinaryOperator"
    SubAssign: "BinaryOperator"
    ShlAssign: "BinaryOperator"
    ShrAssign: "BinaryOperator"
    AndAssign: "BinaryOperator"
    XorAssign: "BinaryOperator"
    OrAssign: "BinaryOperator"
    Comma: "BinaryOperator"


BinaryOperator.Invalid = BinaryOperator(0)
BinaryOperator.PtrMemD = BinaryOperator(1)
BinaryOperator.PtrMemI = BinaryOperator(2)
BinaryOperator.Mul = BinaryOperator(3)
BinaryOperator.Div = BinaryOperator(4)
BinaryOperator.Rem = BinaryOperator(5)
BinaryOperator.Add = BinaryOperator(6)
BinaryOperator.Sub = BinaryOperator(7)
BinaryOperator.Shl = BinaryOperator(8)
BinaryOperator.Shr = BinaryOperator(9)
BinaryOperator.Cmp = BinaryOperator(10)
BinaryOperator.LT = BinaryOperator(11)
BinaryOperator.GT = BinaryOperator(12)
BinaryOperator.LE = BinaryOperator(13)
BinaryOperator.GE = BinaryOperator(14)
BinaryOperator.EQ = BinaryOperator(15)
BinaryOperator.NE = BinaryOperator(16)
BinaryOperator.And = BinaryOperator(17)
BinaryOperator.Xor = BinaryOperator(18)
BinaryOperator.Or = BinaryOperator(19)
BinaryOperator.LAnd = BinaryOperator(20)
BinaryOperator.LOr = BinaryOperator(21)
BinaryOperator.Assign = BinaryOperator(22)
BinaryOperator.MulAssign = BinaryOperator(23)
BinaryOperator.DivAssign = BinaryOperator(24)
BinaryOperator.RemAssign = BinaryOperator(25)
BinaryOperator.AddAssign = BinaryOperator(26)
BinaryOperator.SubAssign = BinaryOperator(27)
BinaryOperator.ShlAssign = BinaryOperator(28)
BinaryOperator.ShrAssign = BinaryOperator(29)
BinaryOperator.AndAssign = BinaryOperator(30)
BinaryOperator.XorAssign = BinaryOperator(31)
BinaryOperator.OrAssign = BinaryOperator(32)
BinaryOperator.Comma = BinaryOperator(33)


@property
def binary_operator(self) -> BinaryOperator:
    """
    Retrieves the opcode if this cursor points to a binary operator
    :return:
    """
    if not hasattr(self, "_binopcode"):
        self._binopcode = conf.lib.clang_getCursorBinaryOperatorKind(self)
    return BinaryOperator.from_id(self._binopcode)


Cursor.binary_operator = binary_operator  # type: ignore


class UnaryOperator(BaseEnumeration):
    """
    Describes the UnaryOperator of a declaration
    """

    # The required BaseEnumeration declarations.
    _kinds = []
    _name_map = None

    def __nonzero__(self):
        """Allows checks of the kind ```if cursor.unary_operator:```"""
        return self.value != 0

    Invalid: "UnaryOperator"
    PostInc: "UnaryOperator"
    PostDec: "UnaryOperator"
    PreInc: "UnaryOperator"
    PreDec: "UnaryOperator"
    AddrOf: "UnaryOperator"
    Deref: "UnaryOperator"
    Plus: "UnaryOperator"
    Minus: "UnaryOperator"
    Not: "UnaryOperator"
    LNot: "UnaryOperator"
    Real: "UnaryOperator"
    Image: "UnaryOperator"
    Extension: "UnaryOperator"
    Coawait: "UnaryOperator"


UnaryOperator.Invalid = UnaryOperator(0)
UnaryOperator.PostInc = UnaryOperator(1)
UnaryOperator.PostDec = UnaryOperator(2)
UnaryOperator.PreInc = UnaryOperator(3)
UnaryOperator.PreDec = UnaryOperator(4)
UnaryOperator.AddrOf = UnaryOperator(5)
UnaryOperator.Deref = UnaryOperator(6)
UnaryOperator.Plus = UnaryOperator(7)
UnaryOperator.Minus = UnaryOperator(8)
UnaryOperator.Not = UnaryOperator(9)
UnaryOperator.LNot = UnaryOperator(10)
UnaryOperator.Real = UnaryOperator(11)
UnaryOperator.Image = UnaryOperator(12)
UnaryOperator.Extension = UnaryOperator(13)
UnaryOperator.Coawait = UnaryOperator(14)


@property
def unary_operator(self) -> UnaryOperator:
    """
    Retrieves the opcode if this cursor points to a unary operator
    :return:
    """
    if not hasattr(self, "_unaryopcode"):
        self._unaryopcode = conf.lib.clang_getCursorUnaryOperatorKind(self)
    return UnaryOperator.from_id(self._unaryopcode)


Cursor.unary_operator = unary_operator  # type: ignore

__all__ = ["BinaryOperator", "UnaryOperator"]
