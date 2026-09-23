#!/usr/bin/env python
"""Django-style management script for blog app."""

import sys

if __name__ == "__main__":
    from fastframe.cli.manage import execute_from_command_line

    execute_from_command_line(sys.argv)
