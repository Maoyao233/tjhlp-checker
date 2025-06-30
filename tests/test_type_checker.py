from io import BytesIO

import pytest

from tjhlp_checker import ViolationKind, find_all_violations, load_config

CPP_CONTENT = """\
#include <stdint.h>
#include <cstddef>

// 直接使用
long long a;
void* pa;
void* &rpa = pa;
// 系统别名
std::size_t sz;
// C方式自定义类型别名
typedef long long ll;
ll b;
typedef long long* llp;
llp pb;
// C++方式自定义类型别名
using ull = unsigned long long int;
ull c;
using arr_of_intptr = int(*)[10];
arr_of_intptr arr;

// 作为函数参数/返回值, 使用系统提供的类型别名
// 同一个类型中只计第一个发现的违规
uint64_t fun(int64_t* x) {
    // 显式类型转换
    int y = static_cast<uint64_t>(x[0]);
    // 使用字面量
    return y + 42ull;
}

// 复杂类型的组成部分
void (*p[20])(float, uint64_t&, void*, double);

// 类成员中使用
class T {
    const char* const p;
    long long& l;
    void*(&arr)[10];
};
"""


@pytest.fixture()
def cpp_file(tmp_path):
    cpp_file = tmp_path / "test_type_checker.cpp"
    cpp_file.write_text(CPP_CONTENT)

    return cpp_file


@pytest.mark.parametrize("arch", ["x86", "x64"])
def test_int64(cpp_file, arch):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_int64_or_larger = true
"""
                + f"""\
[common]
is_32bit = {"true" if arch == "x86" else "false"}
""".encode()
            )
        ),
    )

    # 32bit 模式下, size_t 是四字节，不违规
    if arch == "x86":
        # a, b, pb, c, fun, static_cast, 42ull, p, T::l
        assert len(violations) == 9
    else:
        assert len(violations) == 10

    assert all(vio.kind == ViolationKind.INT64 for vio in violations)


def test_pointer(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_pointer = true
"""
            )
        ),
    )
    assert len(violations) == 8


def test_reference(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_reference = true
"""
            )
        ),
    )
    assert len(violations) == 4


def test_array(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_array = true
"""
            )
        ),
    )
    assert len(violations) == 4


def test_global(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[grammar]
disable_external_global_var = true
"""
            )
        ),
    )
    assert len(violations) == 9
