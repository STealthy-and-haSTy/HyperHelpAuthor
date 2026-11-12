from __future__ import annotations

from typing import List, Optional, Set

import sublime         # noqa: F401
import sublime_plugin  # noqa: F401

from HyperHelp.helpcore.core import lookup_help_topic, help_index_list
from HyperHelp.helpcore.core import parse_link_body
from HyperHelp.helpcore.data import HelpData

from ..linter_base import LintResult, LinterBase


###----------------------------------------------------------------------------


class UnlinkedHelpFilesLinter(LinterBase):
    """
    Lint in the help index to find all help files that appear in the index but
    which don't appear at least one in the defined table of contents.
    """
    def __init__(self, pkg_info: HelpData) -> None:
        super().__init__(pkg_info)

        self.help_files = {file for file in pkg_info.help_files}
        self.linked_files: Set[str] = {"index.txt"}

    def lint(self, view: sublime.View, file_name: str) -> None:
        for pos in view.find_by_selector("meta.link"):
            link_body = view.substr(pos)
            pkg, topic, text = parse_link_body(link_body)

            file = self.validate(pkg, topic, file_name)
            if file is not None:
                self.linked_files.add(file)

    def validate(self, pkg: Optional[str], topic: Optional[str],
                 file_name: str) -> Optional[str]:
        if topic is None:
            return None

        link_pkg = self.pkg_info if pkg is None else help_index_list().get(pkg)
        if link_pkg is None or link_pkg.package != self.pkg_info.package:
            return None

        index_info = lookup_help_topic(link_pkg, topic)
        if index_info is None:
            return None

        if index_info["file"] == file_name:
            return None

        return index_info["file"]

    def results(self) -> List[LintResult]:
        for file in self.help_files - self.linked_files:
            self.add_index(
                "warning",
                "Help file '%s' is not linked to from any other file in this package",
                file)

        return super().results()


###----------------------------------------------------------------------------
