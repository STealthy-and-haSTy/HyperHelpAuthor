import sublime
import sublime_plugin

import os
from collections import OrderedDict, namedtuple
import codecs

from hyperhelpcore.common import log, hh_syntax
from hyperhelpcore.core import help_index_list, lookup_help_topic
from hyperhelpcore.core import parse_help_header, parse_anchor_body, parse_link_body
from hyperhelpcore.core import is_topic_file_valid



###----------------------------------------------------------------------------


# TODO: The code in help_index.py uses posixpath as the path module instead of
# os.path because in packages all files are posix. There is probably going to
# be interplay with that in this code in an unfortunate way since it needs to
# work with local files and match them to resources.


# A representation of what is going to be linted.
LintTarget = namedtuple("LintTarget", [
    "target_type", "pkg_info", "files"
])


# Linters produce an array of these tuples to indicate problems found in files.
# type can be one of "info", "warning" or "error".
LintResult = namedtuple("LintResult", [
    "type", "file", "line", "column", "message"
])


###----------------------------------------------------------------------------


class LinterBase():
    """
    The base class for all lint operations in the help linter.
    """
    def __init__(self, pkg_info):
        self.pkg_info = pkg_info
        self.issues = list()

        self.index_file = os.path.relpath(
                              pkg_info.index_file,
                              "Packages/%s/" % (self.pkg_info.doc_root))

    def lint(self, view, file_name):
        """
        This is invoked with a view that contains raw help text from the help
        file, which is contained in the help index given in the constructor.

        This will be invoked for each file to be linted.
        """
        pass

    def add(self, view, m_type, file, point, msg, *args):
        """
        Add a result to the internal result list. point is the location that is
        the focus of the error. If view is None, the point is ignored and the
        issue is added at line 1, column 1.
        """
        pos = view.rowcol(point) if view is not None else (0, 0)
        msg = msg % args
        self.issues.append(LintResult(m_type, file, pos[0] + 1, pos[1]+1, msg))

    def add_index(self, m_type, msg, *args):
        """
        Add a result that is focused on the help index. As there is no way to
        know the proper location except by hand parsing the index, no view is
        needed and the position of the issue is always row 1, column 1.
        """
        return self.add(None, m_type, self.index_file, 0, msg, *args)

    def results(self):
        """
        This is invoked after all calls to the lint() method have finished to
        collect the final results of the lint operation.

        This should return a list of LintResult tuples that indicate the issues
        that have been found or an empty list if there are no issues.

        The default is to return the results instance variable.
        """
        return self.issues


###----------------------------------------------------------------------------
