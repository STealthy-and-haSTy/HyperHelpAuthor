from __future__ import annotations

from typing import Optional, Set

import sublime         # noqa: F401
import sublime_plugin  # noqa: F401

from HyperHelp.helpcore.data import HelpData, HelpTocEntry

from ..linter_base import LinterBase


###----------------------------------------------------------------------------


class MissingInTOCLinter(LinterBase):
    """
    Lint in the help index to find all help files that appear in the index but
    which don't appear at least once in the defined table of contents.
    """
    def __init__(self, pkg_info: HelpData) -> None:
        super().__init__(pkg_info)

        help_files = {file for file in pkg_info.help_files}
        toc_files: Set[str] = set()
        for topic in pkg_info.help_toc:
            toc_files = self.gather_files(topic, toc_files)

        for file in help_files - toc_files:
            self.add_index(
                "warning",
                "Help file '%s' is not represented in the table of contents",
                file)

    def gather_files(self, topic: HelpTocEntry,
                     file_set: Optional[Set[str]] = None) -> Set[str]:
        if file_set is None:
            file_set = set()

        file_set.add(topic["file"])
        for child in topic.get("children", []):
            file_set = self.gather_files(child, file_set)

        return file_set



###----------------------------------------------------------------------------
