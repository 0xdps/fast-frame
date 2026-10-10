"""Interactive REPL selection for ``manage.py shell``.

``SHELL_INTERFACE`` (a setting, default ``"auto"``) controls which REPL
``manage.py shell`` launches once the namespace (models, ``session``,
``SHELL_IMPORTS``, ``shell_startup.py``, app hooks) is built:

* ``"auto"`` — tries ``ptpython``, then ``IPython``, then falls back to the
  standard library REPL (``code.interact``), whichever is importable
  first. ``ptpython`` is tried first because :func:`_run_ptpython` turns on
  its autosuggestion explicitly (off by default upstream) in addition to
  its default syntax highlighting; IPython (8.12+) ships both on by
  default too, with no extra configuration needed here.
* ``"ptpython"`` / ``"ipython"`` / ``"python"`` — force one, raising
  :class:`ShellInterfaceError` if the package isn't installed.

Neither third-party package is a hard dependency of FastFrame — install
one with ``pip install fast-frame[shell]`` (bundles both) or individually
(``pip install ptpython`` / ``pip install ipython``).

Can also be overridden per-invocation with ``manage.py shell -i ipython``
(see ``fastframe.cli.commands.shell``), which takes priority over the
setting.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable
from typing import Any

ShellRunner = Callable[[dict[str, Any], str], None]


class ShellInterfaceError(RuntimeError):
    """Raised when a requested ``SHELL_INTERFACE`` is unknown or unusable."""


def _ptpython_available() -> bool:
    return importlib.util.find_spec("ptpython") is not None


def _ipython_available() -> bool:
    return importlib.util.find_spec("IPython") is not None


def _run_ptpython(namespace: dict[str, Any], banner: str) -> None:
    from ptpython.repl import embed

    def _configure(repl: Any) -> None:
        # Syntax highlighting is already on by default; autosuggestion
        # (fish-style ghost text completed from history) is not — turn it
        # on, since that's the whole reason ptpython is tried first.
        repl.enable_auto_suggest = True

    if banner:
        print(banner)
    embed(globals=namespace, locals=namespace, configure=_configure)


def _run_ipython(namespace: dict[str, Any], banner: str) -> None:
    import IPython

    # header=... prints our own (short) banner; banner1="" suppresses
    # IPython's own multi-line version/help banner so output stays close
    # to the plain-REPL banner shown today. separate_in="" turns off
    # IPython's default blank line before every `In [n]:` prompt (it
    # defaults to "\n") — that spacing doesn't match a normal terminal's
    # REPL density, and nothing else here adds blank lines around output.
    IPython.embed(header=banner, banner1="", user_ns=namespace, separate_in="")


def _run_stdlib(namespace: dict[str, Any], banner: str) -> None:
    import code

    code.interact(banner=banner, local=namespace)


_AVAILABILITY: dict[str, Callable[[], bool]] = {
    "ptpython": _ptpython_available,
    "ipython": _ipython_available,
    "python": lambda: True,
}

_RUNNERS: dict[str, ShellRunner] = {
    "ptpython": _run_ptpython,
    "ipython": _run_ipython,
    "python": _run_stdlib,
}

# Order "auto" tries interfaces in — ptpython first since it's made to give
# autosuggestion out of the box here, not just highlighting.
_AUTO_ORDER = ["ptpython", "ipython", "python"]


def resolve_shell_interface(interface: str) -> str:
    """Resolve ``"auto"`` (or a specific name) to one of ``_RUNNERS``'s keys.

    Args:
        interface: ``"auto"``, or one of ``"ptpython"``, ``"ipython"``,
            ``"python"``.

    Returns:
        A concrete, available interface name — never ``"auto"``.

    Raises:
        ShellInterfaceError: `interface` is an unknown value, or names a
            specific (non-``"auto"``) interface whose package isn't
            installed. ``"auto"`` never raises — it always has ``"python"``
            (the standard library) to fall back to.
    """
    if interface == "auto":
        return next((name for name in _AUTO_ORDER if _AVAILABILITY[name]()), "python")

    if interface not in _RUNNERS:
        choices = ", ".join(repr(name) for name in ["auto", *_RUNNERS])
        raise ShellInterfaceError(f"Unknown SHELL_INTERFACE {interface!r}. Choose one of: {choices}.")

    if not _AVAILABILITY[interface]():
        raise ShellInterfaceError(
            f"SHELL_INTERFACE={interface!r} requires the '{interface}' package, which "
            f"isn't installed. Run `pip install {interface}` (or `pip install fast-frame[shell]`)."
        )
    return interface


def run_shell(interface: str, namespace: dict[str, Any], banner: str) -> None:
    """Launch the REPL for `interface`.

    `interface` must already be resolved (via :func:`resolve_shell_interface`)
    to a concrete name — this does not handle ``"auto"``.
    """
    _RUNNERS[interface](namespace, banner)


__all__ = ["ShellInterfaceError", "resolve_shell_interface", "run_shell"]
