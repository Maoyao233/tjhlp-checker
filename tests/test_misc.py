from io import BytesIO
import sys
import pytest
import os
from tjhlp_checker import find_all_violations
from tjhlp_checker.config import load_config

CPP_CONTENT = """\
#include <algorithm>
"""


@pytest.fixture()
def cpp_file(tmp_path):
    cpp_file = tmp_path / os.fsdecode("中文.cpp".encode(sys.getfilesystemencoding()))
    cpp_file.write_text(CPP_CONTENT)

    return cpp_file


@pytest.mark.skipif(
    sys.getfilesystemencoding() == "utf-8", reason="The file system encoding is UTF-8"
)
def test_non_unicode_path(cpp_file):
    violations = find_all_violations(
        cpp_file,
        load_config(
            BytesIO(
                b"""\
[header]
whitelist = ["iostream"]
"""
            )
        ),
    )
    assert len(violations) == 1
