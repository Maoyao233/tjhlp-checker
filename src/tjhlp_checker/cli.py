from pathlib import Path
from typing import Annotated
import sys

try:
    import typer
except ModuleNotFoundError:
    print(
        'Cannot find dependency "typer". Please install "tjhlp-checker[cli]" for this module.',
        file=sys.stderr,
    )
    sys.exit(1)

from .checker import find_all_violations
from .config import load_config


def cli_main(
    file: Annotated[Path, typer.Argument(help="Path to input file", exists=True)],
    config_file: Annotated[
        Path, typer.Option(help="Path to TOML config file", prompt=True)
    ],
):
    with open(config_file, "rb") as f:
        config = load_config(f)

    violations = find_all_violations(file, config)
    if violations:
        with open(file, "rb") as src:
            src_text = src.read()
            print(f"Found {len(violations)} violations in {file}:")

            for violation in violations:
                source_range = violation.cursor.extent
                try:
                    print(
                        str(violation),
                        src_text[source_range.start.offset : source_range.end.offset]
                        .decode(config.common.encoding)
                        .replace(
                            "\r\n",
                            "\n",
                        ),
                    )
                except UnicodeError:
                    print(str(violation), "<Encoding Error>")


def main():
    typer.run(cli_main)
