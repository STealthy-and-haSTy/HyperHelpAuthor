from __future__ import annotations

from typing import List, NamedTuple, Optional

import sublime         # noqa: F401
import sublime_plugin  # noqa: F401

import os

from HyperHelp.helpcore.data import HelpData


###----------------------------------------------------------------------------


# TODO: The code in help_index.py uses posixpath as the path module instead of
# os.path because in packages all files are posix. There is probably going to
# be interplay with that in this code in an unfortunate way since it needs to
# work with local files and match them to resources.


# A representation of what is going to be linted.
class LintTarget(NamedTuple):
    target_type: str
    pkg_info: HelpData
    files: List[str]


# Linters produce an array of these tuples to indicate problems found in files.
# type can be one of "info", "warning" or "error".
class LintResult(NamedTuple):
    type: str
    file: str
    line: int
    column: int
    message: str


###----------------------------------------------------------------------------


class LinterBase():
    """
    The base class for all lint operations in the help linter.
    """
    def __init__(self, pkg_info: HelpData) -> None:
        self.pkg_info = pkg_info
        self.issues: List[LintResult] = list()

        self.index_file = os.path.relpath(
                              pkg_info.index_file,
                              "Packages/%s/" % (self.pkg_info.doc_root))

    def lint(self, view: sublime.View, file_name: str) -> None:
        """
        This is invoked with a view that contains raw help text from the help
        file, which is contained in the help index given in the constructor.

        This will be invoked for each file to be linted.
        """
        pass

    def add(self, view: Optional[sublime.View], m_type: str, file: str,
            point: int, msg: str, *args: object) -> None:
        """
        Add a result to the internal result list. point is the location that is
        the focus of the error. If view is None, the point is ignored and the
        issue is added at line 1, column 1.
        """
        pos = view.rowcol(point) if view is not None else (0, 0)
        msg = msg % args
        self.issues.append(LintResult(m_type, file, pos[0] + 1, pos[1]+1, msg))

    def add_index(self, m_type: str, msg: str, *args: object) -> None:
        """
        Add a result that is focused on the help index. As there is no way to
        know the proper location except by hand parsing the index, no view is
        needed and the position of the issue is always row 1, column 1.
        """
        return self.add(None, m_type, self.index_file, 0, msg, *args)

    def results(self) -> List[LintResult]:
        """
        This is invoked after all calls to the lint() method have finished to
        collect the final results of the lint operation.

        This should return a list of LintResult tuples that indicate the issues
        that have been found or an empty list if there are no issues.

        The default is to return the results instance variable.
        """
        return self.issues


###----------------------------------------------------------------------------
