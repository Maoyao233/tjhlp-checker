from pathlib import Path
from typing import Annotated

import typer

from checker import find_all_violations
from config import load_config


def main(
    file: Annotated[Path, typer.Argument(help="The path of input file", exists=True)],
    config_file: Annotated[str, typer.Option(help="The path of config file")],
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


if __name__ == "__main__":
    typer.run(main)
