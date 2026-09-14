from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "addrport",
        nargs="?",
        default="127.0.0.1:8000",
        help="Optional ip:port (default 127.0.0.1:8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development)",
    )


def execute(args: argparse.Namespace) -> None:
    import uvicorn

    from fastframe.core.bootstrap import bootstrap
    from fastframe.core.settings import load_settings

    bootstrap(None)
    settings = load_settings(None)
    asgi_path = getattr(settings, "ASGI_APPLICATION", "config.asgi.application")
    module_path, attr = asgi_path.rsplit(".", 1)
    host, port = _split_addrport(args.addrport)
    uvicorn.run(
        f"{module_path}:{attr}",
        host=host,
        port=port,
        reload=args.reload,
    )


def _split_addrport(addrport: str) -> tuple[str, int]:
    if ":" in addrport:
        host, port_str = addrport.rsplit(":", 1)
        return host, int(port_str)
    return addrport, 8000
