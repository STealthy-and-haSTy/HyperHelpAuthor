from __future__ import annotations

from typing import Any, Optional, Sequence

import sublime

import importlib
import sys

import textwrap


###----------------------------------------------------------------------------


def reload(prefix: str, modules: Optional[Sequence[str]] = None) -> None:
    modules = [""] if modules is None else modules
    prefix = "HyperHelpAuthor.%s." % prefix

    for module in modules:
        module = (prefix + module).rstrip(".")
        if module in sys.modules:
            importlib.reload(sys.modules[module])


###----------------------------------------------------------------------------


reload("src")

common: Any = None
CORE_IMPORTED: bool = False

try:
    # Try to import something from HyperHelp first; if this fails, the whole
    # import block is skipped and we know we should not be running anything.
    from HyperHelp.helpcore import __version__ as hyperhelp_version  # noqa: F401

    # Import all of the commands, event listeners and such.
    from .src import *

    from .src import common as common

    # Flag that the core is loaded, so we are good to go.
    CORE_IMPORTED = True
except Exception:
    # For any import error, we don't want the core.
    CORE_IMPORTED = False


###----------------------------------------------------------------------------


def plugin_loaded() -> None:
    if CORE_IMPORTED:
        common.loaded()
    else:
        sublime.message_dialog(textwrap.dedent("""
            HyperHelpAuthor requires the HyperHelp package to be installed in
            order operate.

            Please install HyperHelp from Package Control and restart Sublime
            to enable HyperHelpAuthor commands and functionality.
        """))


def plugin_unloaded() -> None:
    if CORE_IMPORTED:
        common.unloaded()


###----------------------------------------------------------------------------
