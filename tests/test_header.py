import pytest
from tjhlp_checker import find_all_violations, load_config, ViolationKind
from pydantic import ValidationError
from io import BytesIO

HEADER_CONTENT = """\
#ifndef __MY_WONDERFUL_HEADER
#define __MY_WONDERFUL_HEADER
// 在自己的头文件中包含
#include <vector>
#include <string>
#endif
"""

CPP_CONTENT = """\
#include <iostream>
#include <cstdlib>
#include <algorithm>
#include "my_header.h"
#include "queue" // 自定义头文件与系统头文件重名
#include <1ostream> // 不存在的头文件
"""

BLACKLIST_CONFIG_CONTENT = b"""\
[header]
blacklist = ["vector", "algorithm", "queue"]
"""

WHITELIST_CONFIG_CONTENT = b"""\
[header]
whitelist = ["iostream"]
"""

AMBIGUOUS_CONFIG_CONTENT = b"""\
[header]
blacklist = ["vector", "array"]
whitelist = ["iostream"]
"""


def test_ambiguous_config():
    with pytest.raises(ValidationError):
        load_config(BytesIO(AMBIGUOUS_CONFIG_CONTENT))


@pytest.fixture()
def cpp_file(tmp_path):
    (tmp_path / "my_header.h").write_text(HEADER_CONTENT)
    (tmp_path / "queue").write_text(HEADER_CONTENT)

    cpp_file = tmp_path / "test_header.cpp"
    cpp_file.write_text(CPP_CONTENT)

    return cpp_file


def test_blacklist(cpp_file, tmp_path):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                BLACKLIST_CONFIG_CONTENT
                + f'base_path = "{tmp_path.as_posix()}"'.encode()
            )
        ),
    )
    assert len(violations) == 2

    assert all(vio.kind == ViolationKind.HEADER for vio in violations)
    # <algorithm>
    assert violations[0].cursor.location.line == 3
    # my_header.h 中间接包含了禁用的 vector
    assert violations[1].cursor.location.line == 4
    # 尽管 queue 也在禁用之列, 但根据相对位置能发现它是自定义头文件，不计入违规
    # 头文件第二次包含时由于 define guard, 违规不会重复报


def test_whitelist(cpp_file):
    violations = find_all_violations(
        cpp_file, load_config(BytesIO(WHITELIST_CONFIG_CONTENT))
    )
    assert len(violations) == 6
