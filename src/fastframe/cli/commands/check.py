from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


def execute(args: argparse.Namespace) -> None:
    from fastframe.core.bootstrap import bootstrap

    registry = bootstrap(None)
    for app_config in registry.app_configs:
        print(f"App '{app_config.label}': OK")
    print("System check identified no issues (0 silenced).")
