#!/usr/bin/env python
"""FastFrame management utility."""

import os
import sys


def main() -> None:
    os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")
    from fastframe.cli.manage import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
