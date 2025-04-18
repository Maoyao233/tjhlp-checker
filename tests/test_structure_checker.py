from io import BytesIO

import pytest

from tjhlp_checker import find_all_violations, load_config, ViolationKind
from tjhlp_checker.config import Config, GrammarConfig

CPP_CONTENT = """\
int x;

static int y;

inline int v;

namespace {
    double z;
}

int branch1() {
    return x > 1 ? x : 1;
}

int branch2(int x) {
    if (x < 0) {
        return -1;
    }
    return x > 0;
}

bool branch3(bool c1, bool c2, bool c3) {
    return (c1 && c2) || c3;
}

bool branch4(int x) {
    return !!x;
}

void swap_int(int& x, int& y) {
    x ^= y ^= x ^= y;
}

int bit_op(int x, int y) {
    int z = x & 1;
    z |= y;
    return (~z);
}

int loop1(double t) {
    static int x = 0;
    while (t > 0) {
        t /= 2;
        x++;
    }
    return x;
}

int loop2(int x) {
    for(;;) {
        if (x % 2 == 0) {
            return x;
        }
        x /= 2;
    }
}

int loop3(int x) {
    int t = 0;
retry:
    x *= 2;
    if (t < 10) {
        goto retry;
    }
}

int loop4(double x) {
    do {
        return x;
    } while(0);
}

int main() {
    return 0;
}
"""


@pytest.fixture()
def cpp_file(tmp_path):
    cpp_file = tmp_path / "test_type_checker.cpp"
    cpp_file.write_text(CPP_CONTENT)

    return cpp_file


def test_branch(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_branch = true
"""
            )
        ),
    )
    assert len(violations) == 14


def test_goto(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_goto = true
"""
            )
        ),
    )
    assert len(violations) == 1


def test_bitop(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_bit_operation = true
"""
            )
        ),
    )
    assert len(violations) == 6


def test_function(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_function = true
"""
            )
        ),
    )
    assert len(violations) == 10


def test_global_and_static_local(cpp_file):
    violations = find_all_violations(
        cpp_file,
        Config(
            grammar=GrammarConfig(
                disable_external_global_var=True,
                disable_internal_global_var=True,
                disable_static_local_var=True,
            )
        ),
    )
    assert len(violations) == 5
    print(violations)
    assert (
        sum(1 for vio in violations if vio.kind == ViolationKind.EXTERNAL_GLOBAL) == 2
    )
    assert (
        sum(1 for vio in violations if vio.kind == ViolationKind.INTERNAL_GLOBAL) == 2
    )
    assert sum(1 for vio in violations if vio.kind == ViolationKind.STATIC_LOCAL) == 1
